from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.schemas.common import TimestampSchema


class OrderBase(BaseModel):
    user_id: int
    tour_id: int
    boarding_point_id: int
    seats_count: int
    booking_status: BookingStatus = BookingStatus.NEW
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    cancellation_status: CancellationStatus = CancellationStatus.ACTIVE
    reservation_expires_at: datetime | None = None
    total_amount: Decimal
    currency: str
    source_channel: str | None = None
    assigned_operator_id: int | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    user_id: int | None = None
    tour_id: int | None = None
    boarding_point_id: int | None = None
    seats_count: int | None = None
    booking_status: BookingStatus | None = None
    payment_status: PaymentStatus | None = None
    cancellation_status: CancellationStatus | None = None
    reservation_expires_at: datetime | None = None
    total_amount: Decimal | None = None
    currency: str | None = None
    source_channel: str | None = None
    assigned_operator_id: int | None = None


class OrderRead(OrderBase, TimestampSchema):
    id: int
