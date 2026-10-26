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
    quantity: float = Field(..., gt=0.0, description="Movement quantity must be positive")
    reference_type: str | None = Field(None, max_length=100)
    reference_id: str | None = Field(None, max_length=100)
    reason: str | None = None
    recipient_project: str | None = Field(None, max_length=255)
    idempotency_key: str | None = Field(None, max_length=128)


class ReceiptCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0)
    supplier_id: int | None = None
    reference_type: str | None = "purchase_order"
    reference_id: str | None = None
    reason: str | None = None
    idempotency_key: str | None = None


class IssueCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0)
    recipient_project: str = Field(
        ..., min_length=2, max_length=255, description="Person, student ID, project or lab course"
    )
    reference_type: str | None = "lab_work"
    reference_id: str | None = None
    reason: str | None = None
    idempotency_key: str | None = None


class ReturnCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0)
    recipient_project: str | None = None
    reason: str | None = "Returned unused/working component"
    idempotency_key: str | None = None


class DamageCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0)
    reason: str = Field(..., min_length=3, description="Mandatory failure/damage explanation")
    reference_id: str | None = None
    idempotency_key: str | None = None


class AdjustmentCreate(BaseModel):
    item_id: int
    quantity: float = Field(..., gt=0.0)
    direction: str = Field(..., pattern="^(INCREASE|DECREASE)$")
    reason: str = Field(..., min_length=5, description="Mandatory reason for audit reconciliation")
    idempotency_key: str | None = None


class ReversalCreate(BaseModel):
    reason: str = Field(..., min_length=5, description="Mandatory reason for movement reversal")
    idempotency_key: str | None = None


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
