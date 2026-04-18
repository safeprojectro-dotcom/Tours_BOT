"""W1: prepared customer messaging for Mode 3 custom request lifecycle (not Layer A / not order outbox)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CustomRequestNotificationEventType(StrEnum):
    """Lifecycle points that map to existing request truth — no booking/payment semantics."""

    REQUEST_RECORDED = "custom_request_recorded"
    REQUEST_UNDER_REVIEW = "custom_request_under_review"
    REQUEST_SELECTION_RECORDED = "custom_request_selection_recorded"
    REQUEST_APP_FOLLOWUP_MAY_EXIST = "custom_request_app_followup_may_exist"
    REQUEST_CLOSED = "custom_request_closed"


class MiniAppCustomRequestActivityPreviewRead(BaseModel):
    """W2: customer-visible lifecycle copy derived from W1 templates (in-app only; not delivery proof)."""

    title: str
    message: str
    notification_event: str
    in_app_preview_only: bool = True
    preview_disclaimer: str


class AdminPreparedCustomRequestLifecycleMessageRead(BaseModel):
    """W3: internal/admin inspection of W1-prepared Mode 3 copy — not delivery, not outbox, not receipt proof."""

    model_config = ConfigDict(extra="forbid")

    title: str
    message: str
    notification_event: str
    language_code: str
    preparation_scope: Literal["message_preparation_only"] = "message_preparation_only"
    w1_metadata: dict[str, Any] = Field(default_factory=dict)
    not_sent_to_customer_channels: bool = True
    not_enqueued_to_order_notification_outbox: bool = True
    does_not_prove_customer_read_or_receipt: bool = True
    matches_mini_app_detail_preview_basis: bool = True
    internal_disclaimer: str
    customer_preview_disclaimer: str
    request_status: str
    booking_bridge_status_used_for_resolution: str | None = None


class CustomRequestNotificationPayloadRead(BaseModel):
    """
    Prepared Telegram-friendly (or similar) copy for a single lifecycle touchpoint.

    This payload is not written to ``notification_outbox`` in W1: that table is order-scoped
    (Layer A). Delivery or enqueue, if added later, must use a separate path.
    """

    event_type: CustomRequestNotificationEventType
    request_id: int
    user_id: int
    telegram_user_id: int
    language_code: str
    title: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    preparation_scope: Literal["message_preparation_only"] = "message_preparation_only"
