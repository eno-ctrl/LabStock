from pydantic import BaseModel

from backend.app.schemas.movement import MovementOut


class FrequentItem(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    issue_count: int
    total_issued_qty: float


class AttentionItem(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    storage_location: str
    quantity_on_hand: float
    min_stock_threshold: float
    status: str  # LOW_STOCK or OUT_OF_STOCK
    suggested_reorder: float | None = None


class DashboardSummary(BaseModel):
    active_items_count: int
    total_quantity_on_hand: float
    low_stock_count: int
    out_of_stock_count: int
    recent_receipts_count: int
    recent_issues_count: int
    recent_adjustments_count: int
    pending_purchase_requests_count: int
    attention_items: list[AttentionItem] = []
    frequent_items: list[FrequentItem] = []


class DashboardRecentActivity(BaseModel):
    recent_movements: list[MovementOut] = []
