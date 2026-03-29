from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import BookingStatus, PaymentStatus
from app.schemas.order import OrderRead
from app.schemas.common import TimestampSchema


class PaymentBase(BaseModel):
    order_id: int
    provider: str
    external_payment_id: str | None = None
    amount: Decimal
    currency: str
    status: PaymentStatus = PaymentStatus.UNPAID
    raw_payload: dict | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    provider: str | None = None
    external_payment_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: PaymentStatus | None = None
    raw_payload: dict | None = None


class PaymentRead(PaymentBase, TimestampSchema):
    id: int


class PaymentProviderResult(BaseModel):
    provider: str
    external_payment_id: str
    verified: bool
    provider_status: str
    normalized_status: PaymentStatus
    amount: Decimal | None = None
    currency: str | None = None
    raw_payload: dict | None = None


class PaymentReconciliationRead(BaseModel):
    payment: PaymentRead
    order: OrderRead
    reconciliation_applied: bool
    payment_confirmed: bool


class PaymentWebhookPayload(BaseModel):
    external_payment_id: str
    status: str
    amount: Decimal | None = None
    currency: str | None = None
    payload: dict | None = None


class PaymentWebhookResponse(BaseModel):
    status: str
    payment_id: int
    order_id: int
    payment_status: PaymentStatus
    booking_status: BookingStatus
    payment_confirmed: bool
    reconciliation_applied: bool
