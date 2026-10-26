from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from backend.app.models.item import Item
from backend.app.models.movement import StockMovement
from backend.app.schemas.movement import MovementFilter


class MovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movement_id: int) -> StockMovement | None:
        return (
            self.db.query(StockMovement)
            .options(joinedload(StockMovement.item), joinedload(StockMovement.actor))
            .filter(StockMovement.id == movement_id)
            .first()
        )

    def get_by_idempotency_key(self, key: str) -> StockMovement | None:
        if not key:
            return None
        return (
            self.db.query(StockMovement)
            .options(joinedload(StockMovement.item), joinedload(StockMovement.actor))
            .filter(StockMovement.idempotency_key == key.strip())
            .first()
        )

    def create(
        self,
        item_id: int,
        movement_type: str,
        quantity: float,
        signed_quantity: float,
        balance_after: float,
        reference_type: str | None = None,
        reference_id: str | None = None,
        reason: str | None = None,
        recipient_project: str | None = None,
        actor_id: int | None = None,
        idempotency_key: str | None = None,
        reversal_of_movement_id: int | None = None,
    ) -> StockMovement:
        movement = StockMovement(
            item_id=item_id,
            movement_type=movement_type,
            quantity=round(quantity, 4),
            signed_quantity=round(signed_quantity, 4),
            balance_after=round(balance_after, 4),
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason,
            recipient_project=recipient_project,
            actor_id=actor_id,
            idempotency_key=idempotency_key.strip() if idempotency_key else None,
            reversal_of_movement_id=reversal_of_movement_id,
        )
        self.db.add(movement)
        self.db.flush()
        return movement

    def list_movements(self, filters: MovementFilter) -> tuple[list[StockMovement], int]:
        q = (
            self.db.query(StockMovement)
            .join(Item, StockMovement.item_id == Item.id)
            .options(joinedload(StockMovement.item), joinedload(StockMovement.actor))
        )

        if filters.item_id:
            q = q.filter(StockMovement.item_id == filters.item_id)
        if filters.movement_type:
            q = q.filter(StockMovement.movement_type == filters.movement_type.value)
        if filters.actor_id:
            q = q.filter(StockMovement.actor_id == filters.actor_id)
        if filters.start_date:
            q = q.filter(StockMovement.timestamp >= filters.start_date)
        if filters.end_date:
            q = q.filter(StockMovement.timestamp <= filters.end_date)
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            q = q.filter(
                (Item.sku.ilike(pattern))
                | (Item.name.ilike(pattern))
                | (StockMovement.recipient_project.ilike(pattern))
                | (StockMovement.reason.ilike(pattern))
                | (StockMovement.reference_id.ilike(pattern))
            )

        total = q.count()
        skip = (filters.page - 1) * filters.page_size
        items = (
            q.order_by(desc(StockMovement.timestamp)).offset(skip).limit(filters.page_size).all()
        )
        return items, total
