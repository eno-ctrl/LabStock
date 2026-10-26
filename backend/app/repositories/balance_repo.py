from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import ConflictException
from backend.app.models.balance import StockBalance
from backend.app.models.movement import StockMovement


class BalanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_item_id(self, item_id: int) -> StockBalance | None:
        return self.db.query(StockBalance).filter(StockBalance.item_id == item_id).first()

    def get_for_update(self, item_id: int) -> StockBalance | None:
        """Locks row for update in Postgres, or queries within transaction in SQLite."""
        query = self.db.query(StockBalance).filter(StockBalance.item_id == item_id)
        if not settings.DATABASE_URL.startswith("sqlite"):
            query = query.with_for_update()
        return query.first()

    def update_balance(
        self,
        balance: StockBalance,
        new_qoh: float,
        new_reserved: float | None = None,
    ) -> StockBalance:
        """Atomically updates quantity on hand, recalculating available_to_issue and bumping version."""
        if new_qoh < 0:
            raise ConflictException(
                code="NEGATIVE_STOCK_FORBIDDEN",
                message=f"Cannot update stock to negative balance: {new_qoh}",
            )
        balance.quantity_on_hand = round(new_qoh, 4)
        if new_reserved is not None:
            if new_reserved < 0:
                raise ConflictException(
                    code="NEGATIVE_RESERVED_FORBIDDEN",
                    message="Reserved quantity cannot be negative",
                )
            balance.reserved_quantity = round(new_reserved, 4)

        balance.available_to_issue = round(
            max(0.0, balance.quantity_on_hand - balance.reserved_quantity), 4
        )
        balance.version += 1
        self.db.flush()
        return balance

    def reconcile_with_ledger(self, item_id: int) -> dict:
        """Reconciles physical StockBalance with immutable StockMovement ledger summation."""
        balance = self.get_by_item_id(item_id)
        if not balance:
            return {"reconciled": False, "error": "Item balance not found"}

        ledger_sum = (
            self.db.query(func.coalesce(func.sum(StockMovement.signed_quantity), 0.0))
            .filter(StockMovement.item_id == item_id)
            .scalar()
        )
        difference = round(balance.quantity_on_hand - float(ledger_sum), 4)
        return {
            "item_id": item_id,
            "balance_qoh": balance.quantity_on_hand,
            "ledger_sum": float(ledger_sum),
            "difference": difference,
            "is_reconciled": (difference == 0.0),
        }
