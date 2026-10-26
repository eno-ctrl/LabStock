from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MovementType(StrEnum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    RETURN = "return"
    DAMAGE = "damage"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"


class MovementBase(BaseModel):
    item_id: int
    quantity: float = Field(
        ...,
        gt=0.0,
        le=10_000_000.0,
        allow_inf_nan=False,
        description="Movement quantity must be positive and bounded",
    )
    reference_type: str | None = Field(None, max_length=100)
    reference_id: str | None = Field(None, max_length=100)
    reason: str | None = Field(None, max_length=1000)
    recipient_project: str | None = Field(None, max_length=255)
    idempotency_key: str | None = Field(None, max_length=128)


class ReceiptCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)
    supplier_id: int | None = None
    reference_type: str | None = Field("purchase_order", max_length=100)
    reference_id: str | None = Field(None, max_length=100)
    reason: str | None = Field(None, max_length=1000)
    idempotency_key: str | None = Field(None, max_length=128)


class IssueCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)
    recipient_project: str = Field(
        ..., min_length=2, max_length=255, description="Person, student ID, project or lab course"
    )
    reference_type: str | None = Field("lab_work", max_length=100)
    reference_id: str | None = Field(None, max_length=100)
    reason: str | None = Field(None, max_length=1000)
    idempotency_key: str | None = Field(None, max_length=128)


class ReturnCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)
    recipient_project: str | None = Field(None, max_length=255)
    reason: str | None = Field("Returned unused/working component", max_length=1000)
    idempotency_key: str | None = Field(None, max_length=128)


class DamageCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)
    reason: str = Field(
        ..., min_length=3, max_length=1000, description="Mandatory failure/damage explanation"
    )
    reference_id: str | None = Field(None, max_length=100)
    idempotency_key: str | None = Field(None, max_length=128)


class AdjustmentCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0, le=10_000_000.0, allow_inf_nan=False)
    direction: str = Field(..., pattern="^(INCREASE|DECREASE)$")
    reason: str = Field(
        ..., min_length=5, max_length=1000, description="Mandatory reason for audit reconciliation"
    )
    idempotency_key: str | None = Field(None, max_length=128)


class ReversalCreate(BaseModel):
    reason: str = Field(
        ..., min_length=5, max_length=1000, description="Mandatory reason for movement reversal"
    )
    idempotency_key: str | None = Field(None, max_length=128)


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    item_sku: str | None = None
    item_name: str | None = None
    movement_type: MovementType
    quantity: float
    signed_quantity: float
    balance_after: float
    reference_type: str | None = None
    reference_id: str | None = None
    reason: str | None = None
    recipient_project: str | None = None
    actor_id: int | None = None
    actor_name: str | None = None
    timestamp: datetime
    idempotency_key: str | None = None
    reversal_of_movement_id: int | None = None


class MovementFilter(BaseModel):
    item_id: int | None = None
    movement_type: MovementType | None = None
    actor_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    query: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
