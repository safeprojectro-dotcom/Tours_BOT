"""B16: read-only Admin / OPS visibility dashboard response DTOs (no mutations)."""

from __future__ import annotations

from datetime import datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SupplierOfferShowcasePublishAttemptStatus, TourStatus
from app.schemas.admin import AdminOrderListItem
from app.schemas.admin_prepare_conversion_chain_plan import PrepareConversionChainPlanSummaryStatus

AdminOpsAttentionSeverity = Literal["info", "warning", "error"]

OPS_DASHBOARD_SECTION_KEYS: Final[tuple[str, ...]] = (
    "summary",
    "attention_items",
    "recent_orders",
    "upcoming_tours",
    "recent_publications",
    "conversion_links",
)
OPS_DASHBOARD_SECTION_KEYS_SET: Final[frozenset[str]] = frozenset(OPS_DASHBOARD_SECTION_KEYS)


def parse_include_sections_query(raw: str | None) -> frozenset[str] | None:
    """Parse comma-separated include_sections; None/empty => all sections. Raises ValueError on unknown tokens."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return None
    invalid = sorted({p for p in parts if p not in OPS_DASHBOARD_SECTION_KEYS_SET})
    if invalid:
        raise ValueError(
            f"Unknown include_sections {invalid!r}; "
            f"allowed: {list(OPS_DASHBOARD_SECTION_KEYS)}",
        )
    return frozenset(parts)


class AdminOpsDashboardFiltersRead(BaseModel):
    """Echo of query parameters applied to build this dashboard response (B16B)."""

    model_config = ConfigDict(extra="forbid")

    days_ahead: int
    recent_days: int
    orders_limit: int
    tours_limit: int
    publications_limit: int
    conversion_links_limit: int
    attention_limit: int
    include_sections: list[str] = Field(
        description="Sections with data populated in this response; canonical order when all included.",
    )


class AdminOpsOrderListItem(AdminOrderListItem):
    """`recent_orders` row for OPS dashboard — adds `admin_path` (B16C); all other fields match `AdminOrderListItem`."""

    admin_path: str = Field(description="Admin HTTP path to order detail.")


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
    prepare_conversion_chain_plan_path: str | None = Field(
        default=None,
        description="When related supplier offer is known: GET plan preview path (B16D1).",
    )
    prepare_conversion_chain_plan_status: PrepareConversionChainPlanSummaryStatus | None = Field(
        default=None,
        description="When related supplier offer is known: chain readiness summary (B16D1.2).",
    )
    prepare_conversion_chain_recommended_action: str | None = Field(
        default=None,
        description="When related supplier offer is known: recommended next action (B16D1.2).",
    )
    prepare_conversion_chain_blockers_count: int | None = Field(
        default=None,
        description="When related supplier offer is known: distinct blocker count (B16D1.2).",
    )


class AdminOpsUpcomingTourRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tour_id: int
    code: str
    title_default: str
    departure_datetime: datetime
    status: TourStatus
    seats_available: int
    seats_total: int
    admin_path: str = Field(description="Admin HTTP path to tour detail.")


class AdminOpsRecentPublicationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publish_attempt_id: int
    supplier_offer_id: int
    status: SupplierOfferShowcasePublishAttemptStatus
    showcase_message_id: int | None = None
    channel_ref: str | None = None
    created_at: datetime
    admin_path: str = Field(
        description="Admin HTTP path to supplier offer review package when supplier_offer_id is set.",
    )
    prepare_conversion_chain_plan_path: str = Field(
        description="Admin HTTP path: read-only prepare_conversion_chain plan for this offer (B16D1).",
    )
    prepare_conversion_chain_plan_status: PrepareConversionChainPlanSummaryStatus = Field(
        description="Lightweight chain readiness for this offer (B16D1.2).",
    )
    prepare_conversion_chain_recommended_action: str | None = Field(
        default=None,
        description="Recommended next action for prepare chain / funnel (B16D1.2).",
    )
    prepare_conversion_chain_blockers_count: int = Field(
        ge=0,
        description="Distinct eligibility + plan blocker count (B16D1.2).",
    )


class AdminOpsConversionLinkRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_link_id: int
    supplier_offer_id: int
    tour_id: int
    tour_code: str
    link_status: str
    supplier_offer_admin_path: str = Field(description="Admin path: supplier offer review package.")
    tour_admin_path: str = Field(description="Admin path: tour detail.")
    admin_path: str = Field(
        description="Primary admin navigation path (supplier offer review package for this link).",
    )
    prepare_conversion_chain_plan_path: str = Field(
        description="Admin HTTP path: read-only prepare_conversion_chain plan for this offer (B16D1).",
    )
    prepare_conversion_chain_plan_status: PrepareConversionChainPlanSummaryStatus = Field(
        description="Lightweight chain readiness for this offer (B16D1.2).",
    )
    prepare_conversion_chain_recommended_action: str | None = Field(
        default=None,
        description="Recommended next action for prepare chain / funnel (B16D1.2).",
    )
    prepare_conversion_chain_blockers_count: int = Field(
        ge=0,
        description="Distinct eligibility + plan blocker count (B16D1.2).",
    )


class AdminOpsDashboardRead(BaseModel):
    """GET /admin/ops-dashboard — read-only operations visibility slice."""

    model_config = ConfigDict(extra="forbid")

    summary: AdminOpsDashboardSummary
    attention_items: list[AdminOpsAttentionItemRead] = Field(default_factory=list)
    recent_orders: list[AdminOpsOrderListItem] = Field(default_factory=list)
    upcoming_tours: list[AdminOpsUpcomingTourRead] = Field(default_factory=list)
    recent_publications: list[AdminOpsRecentPublicationRead] = Field(default_factory=list)
    conversion_links: list[AdminOpsConversionLinkRead] = Field(default_factory=list)
    filters: AdminOpsDashboardFiltersRead
    generated_at: datetime = Field(description="UTC timestamp when the dashboard was built.")
    audit_hint: str = Field(
        default="Read-only OPS dashboard; no mutation or Telegram send is performed from this endpoint.",
    )


# Re-export for tests / OpenAPI clarity
__all__ = [
    "AdminOpsAttentionItemRead",
    "AdminOpsAttentionSeverity",
    "AdminOpsConversionLinkRead",
    "AdminOpsDashboardFiltersRead",
    "AdminOpsDashboardRead",
    "AdminOpsDashboardSummary",
    "AdminOpsOrderListItem",
    "AdminOpsRecentPublicationRead",
    "AdminOpsUpcomingTourRead",
    "OPS_DASHBOARD_SECTION_KEYS",
    "OPS_DASHBOARD_SECTION_KEYS_SET",
    "parse_include_sections_query",
]
