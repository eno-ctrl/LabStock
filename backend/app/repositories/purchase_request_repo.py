from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from backend.app.models.purchase_request import PurchaseRequest, PurchaseRequestLine
from backend.app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestFilter,
    PurchaseRequestStatus,
)


class PurchaseRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, request_id: int) -> PurchaseRequest | None:
        return (
            self.db.query(PurchaseRequest)
            .options(
                joinedload(PurchaseRequest.supplier),
                joinedload(PurchaseRequest.requester),
                joinedload(PurchaseRequest.approver),
                joinedload(PurchaseRequest.lines).joinedload(PurchaseRequestLine.item),
            )
            .filter(PurchaseRequest.id == request_id)
            .first()
        )

    def generate_request_number(self) -> str:
        current_year = datetime.now().year
        count = (
            self.db.query(func.count(PurchaseRequest.id))
            .filter(PurchaseRequest.request_number.like(f"PR-{current_year}-%"))
            .scalar()
            or 0
        )
        return f"PR-{current_year}-{(count + 1):04d}"

    def list_requests(self, filters: PurchaseRequestFilter) -> tuple[list[PurchaseRequest], int]:
        q = self.db.query(PurchaseRequest)
        if filters.status:
            q = q.filter(PurchaseRequest.status == filters.status.value)
        if filters.supplier_id:
            q = q.filter(PurchaseRequest.supplier_id == filters.supplier_id)

        total = q.count()
        skip = (filters.page - 1) * filters.page_size
        items = (
            q.options(
                joinedload(PurchaseRequest.supplier),
                joinedload(PurchaseRequest.requester),
                joinedload(PurchaseRequest.approver),
                joinedload(PurchaseRequest.lines).joinedload(PurchaseRequestLine.item),
            )
            .order_by(desc(PurchaseRequest.created_at))
            .offset(skip)
            .limit(filters.page_size)
            .all()
        )
        return items, total

    def create(self, requester_id: int, pr_in: PurchaseRequestCreate) -> PurchaseRequest:
        req_number = self.generate_request_number()
        db_pr = PurchaseRequest(
            request_number=req_number,
            status=PurchaseRequestStatus.DRAFT.value,
            supplier_id=pr_in.supplier_id,
            requester_id=requester_id,
            notes=pr_in.notes.strip() if pr_in.notes else None,
        )
        self.db.add(db_pr)
        self.db.flush()

        for line_in in pr_in.lines:
            line = PurchaseRequestLine(
                request_id=db_pr.id,
                item_id=line_in.item_id,
                requested_quantity=round(line_in.requested_quantity, 4),
                ordered_quantity=0.0,
                received_quantity=0.0,
                unit_cost=line_in.unit_cost,
                notes=line_in.notes.strip() if line_in.notes else None,
            )
            self.db.add(line)

        self.db.commit()
        return self.get_by_id(db_pr.id)  # type: ignore

    def update_status(
        self,
        request: PurchaseRequest,
        new_status: PurchaseRequestStatus,
        approver_id: int | None = None,
    ) -> PurchaseRequest:
        request.status = new_status.value
        if approver_id:
            request.approver_id = approver_id
        # When ordered, sync ordered_quantity = requested_quantity for all lines
        if new_status == PurchaseRequestStatus.ORDERED:
            for line in request.lines:
                if line.ordered_quantity == 0.0:
                    line.ordered_quantity = line.requested_quantity

        self.db.commit()
        self.db.refresh(request)
        return request
