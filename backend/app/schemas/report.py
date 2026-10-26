from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ReportType(StrEnum):
    CURRENT_STOCK = "current_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    MOVEMENTS = "movements"
    CONSUMPTION = "consumption"
    DAMAGED_STOCK = "damaged_stock"
    ADJUSTMENTS = "adjustments"
    PURCHASE_REQUESTS = "purchase_requests"


class CurrentStockRow(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    unit: str
    storage_location: str
    quantity_on_hand: float
    min_stock_threshold: float
    stock_status: str
    supplier_name: str | None = None


class ConsumptionRow(BaseModel):
    item_id: int
    sku: str
    name: str
    category: str
    unit: str
    total_issued: float
    total_returned: float
    net_consumption: float
    issue_transactions: int


class DamagedStockRow(BaseModel):
    movement_id: int
    item_sku: str
    item_name: str
    quantity: float
    unit: str
    reason: str
    actor_name: str | None = None
    timestamp: datetime


class ReportResponse(BaseModel):
    report_type: ReportType
    generated_at: datetime
    total_records: int
    data: list[dict]
