"""Read models for supplier notification outbox (S1C-1)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

SupplierNotificationEventType = Literal["supplier_offer_published", "supplier_order_created"]

SupplierNotificationDispatchStatus = Literal[
    "pending_dispatch",
    "skipped_no_target",
    "delivery_in_progress",
    "delivered",
    "send_failed",
]

SupplierNotificationDeliveryOutcome = Literal["delivered", "already_delivered", "send_failed"]


class SupplierNotificationOutboxRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    idempotency_key: str
    event_type: str
    channel: str
    supplier_id: int | None = None
    supplier_offer_id: int | None = None
    tour_id: int | None = None
    order_id: int | None = None
    telegram_user_id: int | None = None
    contact_resolution_status: str
    title: str
    message: str
    payload_metadata: dict | None = None
    readiness_warnings: list[str] | None = None
    dispatch_status: str
    telegram_message_id: str | None = None
    last_delivery_error: str | None = None
    delivered_at: datetime | None = None
    actor_surface: str | None = None
    created_at: datetime
    updated_at: datetime


class SupplierNotificationOutboxDeliveryResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: SupplierNotificationDeliveryOutcome
    supplier_notification_outbox: SupplierNotificationOutboxRead
    error_detail: str | None = None
