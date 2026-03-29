from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMBaseSchema


class NotificationEventType(StrEnum):
    TEMPORARY_RESERVATION_CREATED = "temporary_reservation_created"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_CONFIRMED = "payment_confirmed"
    RESERVATION_EXPIRED = "reservation_expired"


class NotificationChannel(StrEnum):
    TELEGRAM_PRIVATE = "telegram_private"


class NotificationDispatchStatus(StrEnum):
    PREPARED = "prepared"


class NotificationDeliveryStatus(StrEnum):
    DELIVERED = "delivered"
    FAILED = "failed"


class NotificationOutboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"


class NotificationPayloadRead(BaseModel):
    event_type: NotificationEventType
    order_id: int
    user_id: int
    telegram_user_id: int
    language_code: str
    title: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationDispatchRead(BaseModel):
    dispatch_key: str
    channel: NotificationChannel
    status: NotificationDispatchStatus
    payload: NotificationPayloadRead


class NotificationDeliveryRead(BaseModel):
    dispatch_key: str
    channel: NotificationChannel
    status: NotificationDeliveryStatus
    payload: NotificationPayloadRead
    provider_message_id: str | None = None
    error_message: str | None = None


class NotificationOutboxRead(ORMBaseSchema):
    id: int
    dispatch_key: str
    channel: NotificationChannel
    event_type: NotificationEventType
    order_id: int
    user_id: int
    telegram_user_id: int
    language_code: str
    title: str
    message: str
    payload_metadata: dict[str, Any] = Field(default_factory=dict)
    status: NotificationOutboxStatus
