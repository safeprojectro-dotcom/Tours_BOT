from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, sqlalchemy_enum
from app.models.mixins import TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("seats_count > 0", name="ck_orders_seats_count_positive"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="RESTRICT"), nullable=False, index=True)
    boarding_point_id: Mapped[int] = mapped_column(
        ForeignKey("boarding_points.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seats_count: Mapped[int] = mapped_column(nullable=False)
    booking_status: Mapped[BookingStatus] = mapped_column(
        sqlalchemy_enum(BookingStatus, name="booking_status"),
        nullable=False,
        default=BookingStatus.NEW,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        sqlalchemy_enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.UNPAID,
    )
    cancellation_status: Mapped[CancellationStatus] = mapped_column(
        sqlalchemy_enum(CancellationStatus, name="cancellation_status"),
        nullable=False,
        default=CancellationStatus.ACTIVE,
    )
    reservation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    source_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_operator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user: Mapped["User"] = relationship(back_populates="orders", foreign_keys=[user_id])
    tour: Mapped["Tour"] = relationship(back_populates="orders")
    boarding_point: Mapped["BoardingPoint"] = relationship(back_populates="orders")
    assigned_operator: Mapped["User | None"] = relationship(
        back_populates="assigned_orders",
        foreign_keys=[assigned_operator_id],
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    handoffs: Mapped[list["Handoff"]] = relationship(back_populates="order")
