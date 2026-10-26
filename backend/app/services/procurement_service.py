from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ConflictException,
    InvalidMovementException,
    NotFoundException,
    PurchaseRequestStateConflictException,
)
from backend.app.models.purchase_request import PurchaseRequest
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.purchase_request_repo import PurchaseRequestRepository
from backend.app.schemas.movement import ReceiptCreate
from backend.app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestFilter,
    PurchaseRequestStatus,
    ReceivePurchaseRequestPayload,
)
from backend.app.services.stock_engine import StockEngine


class ProcurementService:
    def __init__(self, db: Session):
        self.db = db
        self.pr_repo = PurchaseRequestRepository(db)
        self.audit_repo = AuditRepository(db)
        self.stock_engine = StockEngine(db)

    def get_request(self, request_id: int) -> PurchaseRequest:
        pr = self.pr_repo.get_by_id(request_id)
        if not pr:
            raise NotFoundException("PurchaseRequest", request_id)
        return pr

    def list_requests(self, filters: PurchaseRequestFilter) -> tuple[list[PurchaseRequest], int]:
        return self.pr_repo.list_requests(filters)

    def create_request(self, requester_id: int, pr_in: PurchaseRequestCreate) -> PurchaseRequest:
        pr = self.pr_repo.create(requester_id, pr_in)
        self.audit_repo.log_event(
            action="CREATE_PURCHASE_REQUEST",
            entity_type="purchase_request",
            entity_id=str(pr.id),
            actor_id=requester_id,
            details={"request_number": pr.request_number, "lines_count": len(pr_in.lines)},
        )
        self.db.commit()
        return pr

    def submit_request(self, request_id: int, actor_id: int | None = None) -> PurchaseRequest:
        pr = self.get_request(request_id)
        if pr.status != PurchaseRequestStatus.DRAFT.value:
            raise PurchaseRequestStateConflictException(
                f"Cannot submit request with status '{pr.status}'. Only 'draft' requests can be submitted."
            )
        updated = self.pr_repo.update_status(pr, PurchaseRequestStatus.SUBMITTED)
        self.audit_repo.log_event(
            action="SUBMIT_PURCHASE_REQUEST",
            entity_type="purchase_request",
            entity_id=str(pr.id),
            actor_id=actor_id,
        )
        self.db.commit()
        return updated

    def approve_request(self, request_id: int, approver_id: int) -> PurchaseRequest:
        pr = self.get_request(request_id)
        if pr.status != PurchaseRequestStatus.SUBMITTED.value:
            raise PurchaseRequestStateConflictException(
                f"Cannot approve request with status '{pr.status}'. Only 'submitted' requests can be approved."
            )
        updated = self.pr_repo.update_status(
            pr, PurchaseRequestStatus.APPROVED, approver_id=approver_id
        )
        self.audit_repo.log_event(
            action="APPROVE_PURCHASE_REQUEST",
            entity_type="purchase_request",
            entity_id=str(pr.id),
            actor_id=approver_id,
        )
        self.db.commit()
        return updated

    def order_request(self, request_id: int, actor_id: int | None = None) -> PurchaseRequest:
        pr = self.get_request(request_id)
        if pr.status != PurchaseRequestStatus.APPROVED.value:
            raise PurchaseRequestStateConflictException(
                f"Cannot order request with status '{pr.status}'. Only 'approved' requests can be marked ordered."
            )
        updated = self.pr_repo.update_status(pr, PurchaseRequestStatus.ORDERED)
        self.audit_repo.log_event(
            action="ORDER_PURCHASE_REQUEST",
            entity_type="purchase_request",
            entity_id=str(pr.id),
            actor_id=actor_id,
        )
        self.db.commit()
        return updated

    def cancel_request(
        self, request_id: int, actor_id: int | None = None, reason: str | None = None
    ) -> PurchaseRequest:
        pr = self.get_request(request_id)
        allowed = [
            PurchaseRequestStatus.DRAFT.value,
            PurchaseRequestStatus.SUBMITTED.value,
            PurchaseRequestStatus.APPROVED.value,
        ]
        if pr.status not in allowed:
            raise PurchaseRequestStateConflictException(
                f"Cannot cancel request in status '{pr.status}'."
            )
        updated = self.pr_repo.update_status(pr, PurchaseRequestStatus.CANCELLED)
        self.audit_repo.log_event(
            action="CANCEL_PURCHASE_REQUEST",
            entity_type="purchase_request",
            entity_id=str(pr.id),
            actor_id=actor_id,
            details={"reason": reason},
        )
        self.db.commit()
        return updated

    def receive_stock_for_request(
        self,
        request_id: int,
        payload: ReceivePurchaseRequestPayload,
        actor_id: int | None = None,
    ) -> PurchaseRequest:
        """Atomically receives physical stock for ordered lines, increments inventory balances, and updates PR status."""
        pr = self.get_request(request_id)
        if pr.status not in [
            PurchaseRequestStatus.ORDERED.value,
            PurchaseRequestStatus.PARTIALLY_RECEIVED.value,
        ]:
            raise PurchaseRequestStateConflictException(
                f"Cannot receive stock for purchase request in '{pr.status}' status. "
                f"Must be 'ordered' or 'partially_received'."
            )

        line_map = {line.id: line for line in pr.lines}

        for item_recv in payload.items:
            line = line_map.get(item_recv.line_id)
            if not line:
                raise NotFoundException("PurchaseRequestLine", item_recv.line_id)

            if item_recv.quantity_to_receive <= 0:
                raise InvalidMovementException("Received quantity must be greater than zero")

            # Check over-receipt against ordered quantity
            remaining_expected = max(0.0, line.ordered_quantity - line.received_quantity)
            if item_recv.quantity_to_receive > remaining_expected:
                raise ConflictException(
                    code="OVER_RECEIPT_DISALLOWED",
                    message=(
                        f"Cannot receive {item_recv.quantity_to_receive} units for line #{line.id}. "
                        f"Only {remaining_expected} units remaining on order."
                    ),
                )

            # Atomically receive stock through the stock engine
            self.stock_engine.receive_stock(
                payload=ReceiptCreate(
                    item_id=line.item_id,
                    quantity=item_recv.quantity_to_receive,
                    reference_type="purchase_request",
                    reference_id=pr.request_number,
                    reason=f"Received against {pr.request_number} line #{line.id}",
                    idempotency_key=(
                        f"{payload.idempotency_key}_line_{line.id}"
                        if payload.idempotency_key
                        else None
                    ),
                ),
                actor_id=actor_id,
            )

            # Update line received quantity
            line.received_quantity = round(
                line.received_quantity + item_recv.quantity_to_receive, 4
            )

        # Re-evaluate overall request completion status
        all_fulfilled = all(line.received_quantity >= line.ordered_quantity for line in pr.lines)
        any_received = any(line.received_quantity > 0 for line in pr.lines)

        if all_fulfilled:
            pr.status = PurchaseRequestStatus.RECEIVED.value
        elif any_received:
            pr.status = PurchaseRequestStatus.PARTIALLY_RECEIVED.value

        self.audit_repo.log_event(
            action="RECEIVE_PR_STOCK",
            entity_type="purchase_request",
            entity_id=str(pr.id),
            actor_id=actor_id,
            details={
                "status": pr.status,
                "received_items_count": len(payload.items),
            },
        )

        self.db.commit()
        self.db.refresh(pr)
        return pr
