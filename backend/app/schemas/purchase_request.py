from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.supplier import SupplierOut
from backend.app.schemas.user import UserOut


class PurchaseRequestStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseRequestLineCreate(BaseModel):
    item_id: int
    requested_quantity: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)
    unit_cost: float | None = Field(None, ge=0.0, le=1_000_000_000.0, allow_inf_nan=False)
    notes: str | None = Field(None, max_length=2000)


class PurchaseRequestLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    item_id: int
    item_sku: str | None = None
    item_name: str | None = None
    requested_quantity: float
    ordered_quantity: float
    received_quantity: float
    unit_cost: float | None = None
    notes: str | None = None


class PurchaseRequestCreate(BaseModel):
    supplier_id: int | None = None
    notes: str | None = Field(None, max_length=2000)
    lines: list[PurchaseRequestLineCreate] = Field(..., min_length=1)


class PurchaseRequestUpdate(BaseModel):
    supplier_id: int | None = None
    notes: str | None = Field(None, max_length=2000)
    lines: list[PurchaseRequestLineCreate] | None = None


class ReceiveLineItem(BaseModel):
    line_id: int
    quantity_to_receive: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)


class ReceivePurchaseRequestPayload(BaseModel):
    items: list[ReceiveLineItem] = Field(..., min_length=1)
    reference: str | None = Field(None, max_length=100)
    idempotency_key: str | None = Field(None, max_length=128)


class PurchaseRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_number: str
    status: PurchaseRequestStatus
    supplier_id: int | None = None
    supplier: SupplierOut | None = None
    requester_id: int
    requester: UserOut | None = None
    approver_id: int | None = None
    approver: UserOut | None = None
    notes: str | None = None
    lines: list[PurchaseRequestLineOut] = []
    created_at: datetime
    updated_at: datetime


class PurchaseRequestFilter(BaseModel):
    status: PurchaseRequestStatus | None = None
    supplier_id: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
