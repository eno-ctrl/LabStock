from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ConflictException,
    InsufficientStockException,
    InvalidMovementException,
    NotFoundException,
)
from backend.app.core.logging import logger
from backend.app.models.item import Item
from backend.app.models.movement import StockMovement
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.balance_repo import BalanceRepository
from backend.app.repositories.movement_repo import MovementRepository
from backend.app.schemas.movement import (
    AdjustmentCreate,
    DamageCreate,
    IssueCreate,
    MovementType,
    ReceiptCreate,
    ReturnCreate,
    ReversalCreate,
)


class StockEngine:
    """Core transactional inventory movement engine enforcing atomic balance integrity."""

    def __init__(self, db: Session):
        self.db = db
        self.balance_repo = BalanceRepository(db)
        self.movement_repo = MovementRepository(db)
        self.audit_repo = AuditRepository(db)

    def _check_idempotency(
        self,
        key: str | None,
        item_id: int,
        expected_type: str,
        expected_qty: float,
    ) -> StockMovement | None:
        if not key:
            return None
        existing = self.movement_repo.get_by_idempotency_key(key)
        if existing:
            if (
                existing.item_id == item_id
                and existing.movement_type == expected_type
                and round(existing.quantity, 4) == round(expected_qty, 4)
            ):
                logger.info(f"Idempotent replay for key {key}, movement id {existing.id}")
                return existing
            raise ConflictException(
                code="IDEMPOTENCY_KEY_CONFLICT",
                message=f"Idempotency key '{key}' was previously used with a different movement payload.",
            )
        return None

    def receive_stock(
        self,
        payload: ReceiptCreate,
        actor_id: int | None = None,
        request_id: str | None = None,
    ) -> StockMovement:
        """Atomic stock receipt (increases quantity on hand)."""
        if payload.quantity <= 0:
            raise InvalidMovementException("Receipt quantity must be greater than zero")

        # Idempotency check
        existing = self._check_idempotency(
            payload.idempotency_key, payload.item_id, MovementType.RECEIPT.value, payload.quantity
        )
        if existing:
            return existing

        item = self.db.query(Item).filter(Item.id == payload.item_id).first()
        if not item:
            raise NotFoundException("Item", payload.item_id)
        if not item.is_active:
            raise InvalidMovementException(
                f"Cannot receive stock for deactivated item '{item.sku}'"
            )

        balance = self.balance_repo.get_for_update(payload.item_id)
        if not balance:
            raise NotFoundException("StockBalance", payload.item_id)

        new_qoh = balance.quantity_on_hand + payload.quantity
        balance = self.balance_repo.update_balance(balance, new_qoh)

        movement = self.movement_repo.create(
            item_id=payload.item_id,
            movement_type=MovementType.RECEIPT.value,
            quantity=payload.quantity,
            signed_quantity=payload.quantity,
            balance_after=balance.quantity_on_hand,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            reason=payload.reason,
            actor_id=actor_id,
            idempotency_key=payload.idempotency_key,
        )

        self.audit_repo.log_event(
            action="RECEIVE_STOCK",
            entity_type="movement",
            entity_id=str(movement.id),
            actor_id=actor_id,
            request_id=request_id,
            details={
                "item_id": payload.item_id,
                "sku": item.sku,
                "quantity": payload.quantity,
                "balance_after": balance.quantity_on_hand,
            },
        )

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def issue_stock(
        self,
        payload: IssueCreate,
        actor_id: int | None = None,
        request_id: str | None = None,
    ) -> StockMovement:
        """Atomic stock issue (decreases quantity on hand; checks available stock)."""
        if payload.quantity <= 0:
            raise InvalidMovementException("Issue quantity must be greater than zero")

        existing = self._check_idempotency(
            payload.idempotency_key, payload.item_id, MovementType.ISSUE.value, payload.quantity
        )
        if existing:
            return existing

        item = self.db.query(Item).filter(Item.id == payload.item_id).first()
        if not item:
            raise NotFoundException("Item", payload.item_id)
        if not item.is_active:
            raise InvalidMovementException(f"Cannot issue stock from deactivated item '{item.sku}'")

        balance = self.balance_repo.get_for_update(payload.item_id)
        if not balance:
            raise NotFoundException("StockBalance", payload.item_id)

        if payload.quantity > balance.available_to_issue:
            raise InsufficientStockException(
                item_name=item.name,
                available=balance.available_to_issue,
                requested=payload.quantity,
            )

        new_qoh = balance.quantity_on_hand - payload.quantity
        balance = self.balance_repo.update_balance(balance, new_qoh)

        movement = self.movement_repo.create(
            item_id=payload.item_id,
            movement_type=MovementType.ISSUE.value,
            quantity=payload.quantity,
            signed_quantity=-payload.quantity,
            balance_after=balance.quantity_on_hand,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            reason=payload.reason,
            recipient_project=payload.recipient_project,
            actor_id=actor_id,
            idempotency_key=payload.idempotency_key,
        )

        self.audit_repo.log_event(
            action="ISSUE_STOCK",
            entity_type="movement",
            entity_id=str(movement.id),
            actor_id=actor_id,
            request_id=request_id,
            details={
                "item_id": payload.item_id,
                "sku": item.sku,
                "quantity": payload.quantity,
                "recipient_project": payload.recipient_project,
                "balance_after": balance.quantity_on_hand,
            },
        )

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def return_stock(
        self,
        payload: ReturnCreate,
        actor_id: int | None = None,
        request_id: str | None = None,
    ) -> StockMovement:
        """Atomic return of working items back into active stock."""
        if payload.quantity <= 0:
            raise InvalidMovementException("Return quantity must be greater than zero")

        existing = self._check_idempotency(
            payload.idempotency_key, payload.item_id, MovementType.RETURN.value, payload.quantity
        )
        if existing:
            return existing

        item = self.db.query(Item).filter(Item.id == payload.item_id).first()
        if not item:
            raise NotFoundException("Item", payload.item_id)

        balance = self.balance_repo.get_for_update(payload.item_id)
        if not balance:
            raise NotFoundException("StockBalance", payload.item_id)

        new_qoh = balance.quantity_on_hand + payload.quantity
        balance = self.balance_repo.update_balance(balance, new_qoh)

        movement = self.movement_repo.create(
            item_id=payload.item_id,
            movement_type=MovementType.RETURN.value,
            quantity=payload.quantity,
            signed_quantity=payload.quantity,
            balance_after=balance.quantity_on_hand,
            reference_type="return",
            reason=payload.reason,
            recipient_project=payload.recipient_project,
            actor_id=actor_id,
            idempotency_key=payload.idempotency_key,
        )

        self.audit_repo.log_event(
            action="RETURN_STOCK",
            entity_type="movement",
            entity_id=str(movement.id),
            actor_id=actor_id,
            request_id=request_id,
            details={
                "item_id": payload.item_id,
                "sku": item.sku,
                "quantity": payload.quantity,
                "balance_after": balance.quantity_on_hand,
            },
        )

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def record_damage(
        self,
        payload: DamageCreate,
        actor_id: int | None = None,
        request_id: str | None = None,
    ) -> StockMovement:
        """Atomic damage write-off (reduces quantity on hand with mandatory reason)."""
        if payload.quantity <= 0:
            raise InvalidMovementException("Damage quantity must be greater than zero")
        if not payload.reason or len(payload.reason.strip()) < 3:
            raise InvalidMovementException("Mandatory damage reason is required for write-off")

        existing = self._check_idempotency(
            payload.idempotency_key, payload.item_id, MovementType.DAMAGE.value, payload.quantity
        )
        if existing:
            return existing

        item = self.db.query(Item).filter(Item.id == payload.item_id).first()
        if not item:
            raise NotFoundException("Item", payload.item_id)

        balance = self.balance_repo.get_for_update(payload.item_id)
        if not balance:
            raise NotFoundException("StockBalance", payload.item_id)

        if payload.quantity > balance.available_to_issue:
            raise InsufficientStockException(
                item_name=item.name,
                available=balance.available_to_issue,
                requested=payload.quantity,
            )

        new_qoh = balance.quantity_on_hand - payload.quantity
        balance = self.balance_repo.update_balance(balance, new_qoh)

        movement = self.movement_repo.create(
            item_id=payload.item_id,
            movement_type=MovementType.DAMAGE.value,
            quantity=payload.quantity,
            signed_quantity=-payload.quantity,
            balance_after=balance.quantity_on_hand,
            reference_type="damage_writeoff",
            reference_id=payload.reference_id,
            reason=payload.reason.strip(),
            actor_id=actor_id,
            idempotency_key=payload.idempotency_key,
        )

        self.audit_repo.log_event(
            action="DAMAGE_WRITEOFF",
            entity_type="movement",
            entity_id=str(movement.id),
            actor_id=actor_id,
            request_id=request_id,
            details={
                "item_id": payload.item_id,
                "sku": item.sku,
                "quantity": payload.quantity,
                "reason": payload.reason,
                "balance_after": balance.quantity_on_hand,
            },
        )

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def adjust_stock(
        self,
        payload: AdjustmentCreate,
        actor_id: int | None = None,
        request_id: str | None = None,
    ) -> StockMovement:
        """Authorized stock adjustment with mandatory reconciliation reason."""
        if payload.quantity <= 0:
            raise InvalidMovementException("Adjustment quantity must be greater than zero")
        if not payload.reason or len(payload.reason.strip()) < 5:
            raise InvalidMovementException("Mandatory justification required for stock adjustment")

        existing = self._check_idempotency(
            payload.idempotency_key,
            payload.item_id,
            MovementType.ADJUSTMENT.value,
            payload.quantity,
        )
        if existing:
            return existing

        item = self.db.query(Item).filter(Item.id == payload.item_id).first()
        if not item:
            raise NotFoundException("Item", payload.item_id)

        balance = self.balance_repo.get_for_update(payload.item_id)
        if not balance:
            raise NotFoundException("StockBalance", payload.item_id)

        if payload.direction == "INCREASE":
            signed_qty = payload.quantity
            new_qoh = balance.quantity_on_hand + payload.quantity
        elif payload.direction == "DECREASE":
            if payload.quantity > balance.available_to_issue:
                raise InsufficientStockException(
                    item_name=item.name,
                    available=balance.available_to_issue,
                    requested=payload.quantity,
                )
            signed_qty = -payload.quantity
            new_qoh = balance.quantity_on_hand - payload.quantity
        else:
            raise InvalidMovementException(f"Invalid adjustment direction '{payload.direction}'")

        balance = self.balance_repo.update_balance(balance, new_qoh)

        movement = self.movement_repo.create(
            item_id=payload.item_id,
            movement_type=MovementType.ADJUSTMENT.value,
            quantity=payload.quantity,
            signed_quantity=signed_qty,
            balance_after=balance.quantity_on_hand,
            reference_type="audit_correction",
            reason=f"[{payload.direction}] {payload.reason.strip()}",
            actor_id=actor_id,
            idempotency_key=payload.idempotency_key,
        )

        self.audit_repo.log_event(
            action="ADJUST_STOCK",
            entity_type="movement",
            entity_id=str(movement.id),
            actor_id=actor_id,
            request_id=request_id,
            details={
                "item_id": payload.item_id,
                "sku": item.sku,
                "direction": payload.direction,
                "quantity": payload.quantity,
                "reason": payload.reason,
                "balance_after": balance.quantity_on_hand,
            },
        )

        self.db.commit()
        self.db.refresh(movement)
        return movement

    def reverse_movement(
        self,
        movement_id: int,
        payload: ReversalCreate,
        actor_id: int | None = None,
        request_id: str | None = None,
    ) -> StockMovement:
        """Traceable reversal of an eligible previous stock movement."""
        # Idempotency check before state evaluation
        if payload.idempotency_key:
            existing = self.movement_repo.get_by_idempotency_key(payload.idempotency_key)
            if existing:
                if (
                    existing.movement_type == MovementType.REVERSAL.value
                    and existing.reversal_of_movement_id == movement_id
                ):
                    logger.info(
                        f"Idempotent reversal replay for key {payload.idempotency_key}, movement id {existing.id}"
                    )
                    return existing
                raise ConflictException(
                    code="IDEMPOTENCY_KEY_CONFLICT",
                    message=f"Idempotency key '{payload.idempotency_key}' was previously used with a different movement payload.",
                )

        original = self.movement_repo.get_by_id(movement_id)
        if not original:
            raise NotFoundException("StockMovement", movement_id)

        if original.movement_type == MovementType.REVERSAL.value:
            raise InvalidMovementException("Cannot reverse a reversal entry")

        # Check if already reversed
        already_reversed = (
            self.db.query(StockMovement)
            .filter(StockMovement.reversal_of_movement_id == movement_id)
            .first()
        )
        if already_reversed:
            raise ConflictException(
                code="MOVEMENT_ALREADY_REVERSED",
                message=f"Movement #{movement_id} has already been reversed by movement #{already_reversed.id}",
            )

        balance = self.balance_repo.get_for_update(original.item_id)
        if not balance:
            raise NotFoundException("StockBalance", original.item_id)

        # Opposite signed effect
        reverse_signed_qty = -original.signed_quantity
        new_qoh = balance.quantity_on_hand + reverse_signed_qty
        if new_qoh < 0:
            raise InsufficientStockException(
                item_name=original.item.name,
                available=balance.quantity_on_hand,
                requested=abs(reverse_signed_qty),
            )

        balance = self.balance_repo.update_balance(balance, new_qoh)

        reversal_movement = self.movement_repo.create(
            item_id=original.item_id,
            movement_type=MovementType.REVERSAL.value,
            quantity=original.quantity,
            signed_quantity=reverse_signed_qty,
            balance_after=balance.quantity_on_hand,
            reference_type="movement_reversal",
            reference_id=str(original.id),
            reason=payload.reason.strip(),
            actor_id=actor_id,
            idempotency_key=payload.idempotency_key,
            reversal_of_movement_id=original.id,
        )

        self.audit_repo.log_event(
            action="REVERSE_MOVEMENT",
            entity_type="movement",
            entity_id=str(reversal_movement.id),
            actor_id=actor_id,
            request_id=request_id,
            details={
                "original_movement_id": original.id,
                "reversal_movement_id": reversal_movement.id,
                "reason": payload.reason,
                "balance_after": balance.quantity_on_hand,
            },
        )

        self.db.commit()
        self.db.refresh(reversal_movement)
        return reversal_movement
