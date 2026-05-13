"""B16: read-only Admin / OPS visibility dashboard response DTOs (no mutations)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SupplierOfferShowcasePublishAttemptStatus, TourStatus
from app.schemas.admin import AdminOrderListItem

AdminOpsAttentionSeverity = Literal["info", "warning", "error"]


class AdminOpsDashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upcoming_tours_count: int = 0
    open_for_sale_tours_count: int = 0
    active_holds_count: int = 0
    pending_payment_orders_count: int = 0
    confirmed_orders_count: int = 0
    expired_or_closed_orders_count: int = 0
    open_handoffs_count: int = 0
    attention_items_count: int = 0


class AdminOpsAttentionItemRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    severity: AdminOpsAttentionSeverity = "info"
    title: str
    summary: str
    admin_path: str
    related_order_id: int | None = None
    related_tour_id: int | None = None
    related_supplier_offer_id: int | None = None


class AdminOpsUpcomingTourRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tour_id: int
    code: str
    title_default: str
    departure_datetime: datetime
    status: TourStatus
    seats_available: int
    seats_total: int


class AdminOpsRecentPublicationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publish_attempt_id: int
    supplier_offer_id: int
    status: SupplierOfferShowcasePublishAttemptStatus
    showcase_message_id: int | None = None
    channel_ref: str | None = None
    created_at: datetime


class AdminOpsConversionLinkRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_link_id: int
    supplier_offer_id: int
    tour_id: int
    tour_code: str
    link_status: str


class AdminOpsDashboardRead(BaseModel):
    """GET /admin/ops-dashboard — read-only operations visibility slice."""

    model_config = ConfigDict(extra="forbid")

    summary: AdminOpsDashboardSummary
    attention_items: list[AdminOpsAttentionItemRead] = Field(default_factory=list)
    recent_orders: list[AdminOrderListItem] = Field(default_factory=list)
    upcoming_tours: list[AdminOpsUpcomingTourRead] = Field(default_factory=list)
    recent_publications: list[AdminOpsRecentPublicationRead] = Field(default_factory=list)
    conversion_links: list[AdminOpsConversionLinkRead] = Field(default_factory=list)
    generated_at: datetime = Field(description="UTC timestamp when the dashboard was built.")
    audit_hint: str = Field(
        default="Read-only OPS dashboard; no mutation or Telegram send is performed from this endpoint.",
    )


# Re-export for tests / OpenAPI clarity
__all__ = [
    "AdminOpsAttentionItemRead",
    "AdminOpsAttentionSeverity",
    "AdminOpsConversionLinkRead",
    "AdminOpsDashboardRead",
    "AdminOpsDashboardSummary",
    "AdminOpsRecentPublicationRead",
    "AdminOpsUpcomingTourRead",
]
