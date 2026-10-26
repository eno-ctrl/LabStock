from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.item import Item


class StockBalance(Base):
    __tablename__ = "stock_balances"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="chk_positive_qoh"),
        CheckConstraint("reserved_quantity >= 0", name="chk_positive_reserved"),
        CheckConstraint("available_to_issue >= 0", name="chk_positive_available"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    quantity_on_hand: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Available to issue is persisted/calculated to support fast queries and constraints
    available_to_issue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationship
    item: Mapped["Item"] = relationship("Item", back_populates="balance")

    def __repr__(self) -> str:
        return f"<StockBalance item_id={self.item_id} qoh={self.quantity_on_hand} avail={self.available_to_issue}>"
