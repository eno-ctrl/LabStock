from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.models.balance import StockBalance
from backend.app.models.item import Item
from backend.app.models.movement import StockMovement
from backend.app.models.purchase_request import PurchaseRequest
from backend.app.schemas.dashboard import AttentionItem, DashboardSummary, FrequentItem
from backend.app.schemas.movement import MovementOut, MovementType
from backend.app.schemas.purchase_request import PurchaseRequestStatus


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> DashboardSummary:
        # Active items count
        active_items_count = (
            self.db.query(func.count(Item.id)).filter(Item.is_active.is_(True)).scalar() or 0
        )

        # Total quantity on hand
        total_qoh = (
            self.db.query(func.coalesce(func.sum(StockBalance.quantity_on_hand), 0.0))
            .join(Item, StockBalance.item_id == Item.id)
            .filter(Item.is_active.is_(True))
            .scalar()
            or 0.0
        )

        # Low stock count: qoh > 0 and qoh <= min_stock_threshold
        low_stock_count = (
            self.db.query(func.count(Item.id))
            .join(StockBalance, Item.id == StockBalance.item_id)
            .filter(
                Item.is_active.is_(True),
                StockBalance.quantity_on_hand > 0,
                StockBalance.quantity_on_hand <= Item.min_stock_threshold,
            )
            .scalar()
            or 0
        )

        # Out of stock count: qoh <= 0
        out_of_stock_count = (
            self.db.query(func.count(Item.id))
            .join(StockBalance, Item.id == StockBalance.item_id)
            .filter(
                Item.is_active.is_(True),
                StockBalance.quantity_on_hand <= 0,
            )
            .scalar()
            or 0
        )

        # Recent 30 days time threshold
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        recent_receipts = (
            self.db.query(func.count(StockMovement.id))
            .filter(
                StockMovement.movement_type == MovementType.RECEIPT.value,
                StockMovement.timestamp >= thirty_days_ago,
            )
            .scalar()
            or 0
        )

        recent_issues = (
            self.db.query(func.count(StockMovement.id))
            .filter(
                StockMovement.movement_type == MovementType.ISSUE.value,
                StockMovement.timestamp >= thirty_days_ago,
            )
            .scalar()
            or 0
        )

        recent_adjustments = (
            self.db.query(func.count(StockMovement.id))
            .filter(
                StockMovement.movement_type == MovementType.ADJUSTMENT.value,
                StockMovement.timestamp >= thirty_days_ago,
            )
            .scalar()
            or 0
        )

        pending_prs = (
            self.db.query(func.count(PurchaseRequest.id))
            .filter(
                PurchaseRequest.status.in_(
                    [
                        PurchaseRequestStatus.SUBMITTED.value,
                        PurchaseRequestStatus.APPROVED.value,
                        PurchaseRequestStatus.ORDERED.value,
                    ]
                )
            )
            .scalar()
            or 0
        )

        # Items requiring attention (low or out of stock)
        attention_query = (
            self.db.query(Item)
            .join(StockBalance, Item.id == StockBalance.item_id)
            .options(joinedload(Item.balance))
            .filter(
                Item.is_active.is_(True),
                StockBalance.quantity_on_hand <= Item.min_stock_threshold,
            )
            .limit(10)
            .all()
        )

        attention_items: list[AttentionItem] = []
        for it in attention_query:
            qoh = it.balance.quantity_on_hand if it.balance else 0.0
            status_str = "OUT_OF_STOCK" if qoh <= 0 else "LOW_STOCK"
            suggested = None
            if it.target_stock and it.target_stock > qoh:
                suggested = round(it.target_stock - qoh, 2)
            elif it.min_stock_threshold > qoh:
                suggested = round((it.min_stock_threshold * 2) - qoh, 2)

            attention_items.append(
                AttentionItem(
                    item_id=it.id,
                    sku=it.sku,
                    name=it.name,
                    category=it.category,
                    storage_location=it.storage_location,
                    quantity_on_hand=qoh,
                    min_stock_threshold=it.min_stock_threshold,
                    status=status_str,
                    suggested_reorder=suggested,
                )
            )

        # Frequent items issued in the last 30 days
        frequent_rows = (
            self.db.query(
                Item.id,
                Item.sku,
                Item.name,
                Item.category,
                func.count(StockMovement.id).label("issue_count"),
                func.sum(StockMovement.quantity).label("total_issued"),
            )
            .join(StockMovement, Item.id == StockMovement.item_id)
            .filter(
                StockMovement.movement_type == MovementType.ISSUE.value,
                StockMovement.timestamp >= thirty_days_ago,
            )
            .group_by(Item.id, Item.sku, Item.name, Item.category)
            .order_by(func.count(StockMovement.id).desc())
            .limit(5)
            .all()
        )

        frequent_items = [
            FrequentItem(
                item_id=r[0],
                sku=r[1],
                name=r[2],
                category=r[3],
                issue_count=r[4],
                total_issued_qty=float(r[5] or 0.0),
            )
            for r in frequent_rows
        ]

        return DashboardSummary(
            active_items_count=active_items_count,
            total_quantity_on_hand=round(float(total_qoh), 2),
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
            recent_receipts_count=recent_receipts,
            recent_issues_count=recent_issues,
            recent_adjustments_count=recent_adjustments,
            pending_purchase_requests_count=pending_prs,
            attention_items=attention_items,
            frequent_items=frequent_items,
        )

    def get_recent_movements(self, limit: int = 15) -> list[MovementOut]:
        movements = (
            self.db.query(StockMovement)
            .join(Item, StockMovement.item_id == Item.id)
            .options(joinedload(StockMovement.item), joinedload(StockMovement.actor))
            .order_by(StockMovement.timestamp.desc())
            .limit(limit)
            .all()
        )
        result = []
        for m in movements:
            result.append(
                MovementOut(
                    id=m.id,
                    item_id=m.item_id,
                    item_sku=m.item.sku if m.item else "UNKNOWN",
                    item_name=m.item.name if m.item else "Unknown Item",
                    movement_type=MovementType(m.movement_type),
                    quantity=m.quantity,
                    signed_quantity=m.signed_quantity,
                    balance_after=m.balance_after,
                    reference_type=m.reference_type,
                    reference_id=m.reference_id,
                    reason=m.reason,
                    recipient_project=m.recipient_project,
                    actor_id=m.actor_id,
                    actor_name=m.actor.full_name if m.actor else None,
                    timestamp=m.timestamp,
                    idempotency_key=m.idempotency_key,
                    reversal_of_movement_id=m.reversal_of_movement_id,
                )
            )
        return result
