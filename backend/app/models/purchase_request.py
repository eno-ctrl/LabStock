from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.item import Item
    from backend.app.models.supplier import Supplier
    from backend.app.models.user import User


class PurchaseRequest(Base, TimestampMixin):
    __tablename__ = "purchase_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    # Lifecycle status: draft -> submitted -> approved -> ordered -> partially_received -> received / cancelled
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True, nullable=False)

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approver_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", lazy="joined")
    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id], lazy="joined")
    approver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approver_id], lazy="joined"
    )
    lines: Mapped[list["PurchaseRequestLine"]] = relationship(
        "PurchaseRequestLine",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<PurchaseRequest {self.request_number} ({self.status})>"


class PurchaseRequestLine(Base):
    __tablename__ = "purchase_request_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    requested_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    ordered_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    received_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="lines")
    item: Mapped["Item"] = relationship("Item", lazy="joined")

    def __repr__(self) -> str:
        return f"<PurchaseRequestLine req={self.request_id} item={self.item_id} req_qty={self.requested_quantity}>"
