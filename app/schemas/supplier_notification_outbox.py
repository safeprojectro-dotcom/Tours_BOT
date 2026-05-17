"""Read models for supplier notification outbox (S1C-1)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

SupplierNotificationEventType = Literal["supplier_offer_published", "supplier_order_created"]

SupplierNotificationDispatchStatus = Literal["pending_dispatch", "skipped_no_target"]


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
    actor_surface: str | None = None
    created_at: datetime
    updated_at: datetime
