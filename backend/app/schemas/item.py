from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.schemas.balance import StockBalanceOut
from backend.app.schemas.supplier import SupplierOut


class ItemBase(BaseModel):
    sku: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(None, max_length=5000)
    category: str = Field(..., min_length=2, max_length=100)
    unit: str = Field(default="pcs", min_length=1, max_length=50)
    storage_location: str = Field(..., min_length=2, max_length=100)
    min_stock_threshold: float = Field(default=0.0, ge=0.0, le=10_000_000.0, allow_inf_nan=False)
    target_stock: float | None = Field(None, ge=0.0, le=10_000_000.0, allow_inf_nan=False)
    preferred_supplier_id: int | None = None
    manufacturer_model: str | None = Field(None, max_length=255)
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def clean_sku(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("SKU cannot be empty or only whitespace")
        return cleaned


class ItemCreate(ItemBase):
    initial_stock: float = Field(
        default=0.0, ge=0.0, le=10_000_000.0, allow_inf_nan=False
    )  # If provided on initial creation, records an opening receipt


class ItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, max_length=5000)
    category: str | None = Field(None, min_length=2, max_length=100)
    unit: str | None = Field(None, min_length=1, max_length=50)
    storage_location: str | None = Field(None, min_length=2, max_length=100)
    min_stock_threshold: float | None = Field(None, ge=0.0, le=10_000_000.0, allow_inf_nan=False)
    target_stock: float | None = Field(None, ge=0.0, le=10_000_000.0, allow_inf_nan=False)
    preferred_supplier_id: int | None = None
    manufacturer_model: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    balance: StockBalanceOut | None = None
    supplier: SupplierOut | None = None
    stock_status: str = "IN_STOCK"  # Computed: "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"
    created_at: datetime
    updated_at: datetime


class ItemFilter(BaseModel):
    query: str | None = None
    category: str | None = None
    storage_location: str | None = None
    status: str | None = None  # all, in_stock, low_stock, out_of_stock
    is_active: bool | None = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "name"
    sort_desc: bool = False
