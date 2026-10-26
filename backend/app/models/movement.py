from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.item import Item
    from backend.app.models.user import User


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    movement_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    # Movement quantity is the entered scalar (> 0)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    # Net change applied to quantity_on_hand (+ or -)
    signed_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    # Balance on hand immediately after this ledger entry
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)

    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_project: Mapped[str | None] = mapped_column(String(255), nullable=True)

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
        nullable=False,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
    )
    reversal_of_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_movements.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    item: Mapped["Item"] = relationship("Item", back_populates="movements")
    actor: Mapped[Optional["User"]] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return f"<StockMovement id={self.id} item={self.item_id} type={self.movement_type} qty={self.signed_quantity}>"
