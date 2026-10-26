import csv
import io
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.models.balance import StockBalance
from backend.app.models.item import Item
from backend.app.models.movement import StockMovement
from backend.app.schemas.movement import MovementType


def sanitize_csv_cell(value: Any) -> str:
    """Mitigates spreadsheet formula injection by escaping trigger characters."""
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{text}"
    return text


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_stock_report(
        self, category: str | None = None, location: str | None = None
    ) -> list[dict[str, Any]]:
        q = (
            self.db.query(Item)
            .join(StockBalance, Item.id == StockBalance.item_id)
            .options(joinedload(Item.balance), joinedload(Item.supplier))
            .filter(Item.is_active.is_(True))
        )
        if category and category != "All":
            q = q.filter(Item.category == category)
        if location:
            q = q.filter(Item.storage_location.ilike(f"%{location}%"))

        items = q.order_by(Item.category.asc(), Item.name.asc()).all()
        rows = []
        for it in items:
            qoh = it.balance.quantity_on_hand if it.balance else 0.0
            min_thresh = it.min_stock_threshold or 0.0
            status_str = (
                "OUT_OF_STOCK" if qoh <= 0 else ("LOW_STOCK" if qoh <= min_thresh else "IN_STOCK")
            )
            rows.append(
                {
                    "SKU": it.sku,
                    "Item Name": it.name,
                    "Category": it.category,
                    "Storage Location": it.storage_location,
                    "Unit": it.unit,
                    "Quantity on Hand": qoh,
                    "Min Threshold": min_thresh,
                    "Stock Status": status_str,
                    "Supplier": it.supplier.name if it.supplier else "N/A",
                }
            )
        return rows

    def get_low_stock_report(self) -> list[dict[str, Any]]:
        q = (
            self.db.query(Item)
            .join(StockBalance, Item.id == StockBalance.item_id)
            .options(joinedload(Item.balance), joinedload(Item.supplier))
            .filter(
                Item.is_active.is_(True),
                StockBalance.quantity_on_hand <= Item.min_stock_threshold,
            )
            .order_by(StockBalance.quantity_on_hand.asc())
            .all()
        )
        rows = []
        for it in q:
            qoh = it.balance.quantity_on_hand if it.balance else 0.0
            rows.append(
                {
                    "SKU": it.sku,
                    "Item Name": it.name,
                    "Category": it.category,
                    "Storage Location": it.storage_location,
                    "Quantity on Hand": qoh,
                    "Min Threshold": it.min_stock_threshold,
                    "Deficit": round(it.min_stock_threshold - qoh, 2),
                    "Supplier": it.supplier.name if it.supplier else "N/A",
                }
            )
        return rows

    def get_out_of_stock_report(self) -> list[dict[str, Any]]:
        q = (
            self.db.query(Item)
            .join(StockBalance, Item.id == StockBalance.item_id)
            .options(joinedload(Item.balance), joinedload(Item.supplier))
            .filter(
                Item.is_active.is_(True),
                StockBalance.quantity_on_hand <= 0,
            )
            .order_by(Item.name.asc())
            .all()
        )
        rows = []
        for it in q:
            rows.append(
                {
                    "SKU": it.sku,
                    "Item Name": it.name,
                    "Category": it.category,
                    "Storage Location": it.storage_location,
                    "Min Threshold": it.min_stock_threshold,
                    "Supplier": it.supplier.name if it.supplier else "N/A",
                }
            )
        return rows

    def get_movements_report(
        self,
        item_id: int | None = None,
        movement_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        q = (
            self.db.query(StockMovement)
            .join(Item, StockMovement.item_id == Item.id)
            .options(joinedload(StockMovement.item), joinedload(StockMovement.actor))
        )
        if item_id:
            q = q.filter(StockMovement.item_id == item_id)
        if movement_type and movement_type != "All":
            q = q.filter(StockMovement.movement_type == movement_type)
        if start_date:
            q = q.filter(StockMovement.timestamp >= start_date)
        if end_date:
            q = q.filter(StockMovement.timestamp <= end_date)

        movements = q.order_by(StockMovement.timestamp.desc()).limit(1000).all()
        rows = []
        for m in movements:
            rows.append(
                {
                    "Movement ID": m.id,
                    "Timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S") if m.timestamp else "",
                    "Item SKU": m.item.sku if m.item else "",
                    "Item Name": m.item.name if m.item else "",
                    "Type": m.movement_type.upper(),
                    "Quantity": m.quantity,
                    "Signed Change": m.signed_quantity,
                    "Balance After": m.balance_after,
                    "Recipient/Project": m.recipient_project or "",
                    "Reason/Reference": m.reason or m.reference_id or "",
                    "Actor": m.actor.full_name if m.actor else "System",
                }
            )
        return rows

    def get_consumption_report(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Calculates consumption by item: gross issues, accepted returns, and true net consumption."""
        items = self.db.query(Item).filter(Item.is_active.is_(True)).order_by(Item.name.asc()).all()

        rows = []
        for it in items:
            q_base = self.db.query(StockMovement).filter(StockMovement.item_id == it.id)
            if start_date:
                q_base = q_base.filter(StockMovement.timestamp >= start_date)
            if end_date:
                q_base = q_base.filter(StockMovement.timestamp <= end_date)

            gross_issues = (
                q_base.filter(StockMovement.movement_type == MovementType.ISSUE.value)
                .with_entities(func.coalesce(func.sum(StockMovement.quantity), 0.0))
                .scalar()
                or 0.0
            )

            returns = (
                q_base.filter(StockMovement.movement_type == MovementType.RETURN.value)
                .with_entities(func.coalesce(func.sum(StockMovement.quantity), 0.0))
                .scalar()
                or 0.0
            )

            net_consumption = max(0.0, round(float(gross_issues) - float(returns), 2))

            if gross_issues > 0 or returns > 0:
                rows.append(
                    {
                        "SKU": it.sku,
                        "Item Name": it.name,
                        "Category": it.category,
                        "Unit": it.unit,
                        "Gross Issued": round(float(gross_issues), 2),
                        "Returned": round(float(returns), 2),
                        "Net Consumption": net_consumption,
                    }
                )
        return rows

    def get_damaged_stock_report(self) -> list[dict[str, Any]]:
        damages = (
            self.db.query(StockMovement)
            .join(Item, StockMovement.item_id == Item.id)
            .options(joinedload(StockMovement.item), joinedload(StockMovement.actor))
            .filter(StockMovement.movement_type == MovementType.DAMAGE.value)
            .order_by(StockMovement.timestamp.desc())
            .all()
        )
        rows = []
        for d in damages:
            rows.append(
                {
                    "Date": d.timestamp.strftime("%Y-%m-%d %H:%M:%S") if d.timestamp else "",
                    "SKU": d.item.sku if d.item else "",
                    "Item Name": d.item.name if d.item else "",
                    "Quantity Written Off": d.quantity,
                    "Unit": d.item.unit if d.item else "pcs",
                    "Damage Reason": d.reason or "No explanation recorded",
                    "Logged By": d.actor.full_name if d.actor else "System",
                }
            )
        return rows

    def generate_csv_stream(self, rows: list[dict[str, Any]]) -> io.StringIO:
        """Serializes dictionary rows into CSV with formula-injection mitigation."""
        output = io.StringIO()
        if not rows:
            output.write("No data records available\n")
            output.seek(0)
            return output

        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for r in rows:
            sanitized = {k: sanitize_csv_cell(v) for k, v in r.items()}
            writer.writerow(sanitized)

        output.seek(0)
        return output
