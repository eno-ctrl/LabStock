from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.balance import StockBalance
    from backend.app.models.movement import StockMovement
    from backend.app.models.supplier import Supplier


class Item(Base, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="pcs", nullable=False)
    storage_location: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    min_stock_threshold: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_stock: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    manufacturer_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    balance: Mapped["StockBalance"] = relationship(
        "StockBalance",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
    )
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", lazy="joined")
    movements: Mapped[list["StockMovement"]] = relationship("StockMovement", back_populates="item")

    def __repr__(self) -> str:
        return f"<Item {self.sku}: {self.name}>"
