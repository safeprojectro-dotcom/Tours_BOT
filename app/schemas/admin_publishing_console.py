"""B15B: read-only Admin Publishing Console response DTOs (no publish / schedule / mutations)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PublishingConsoleCandidateKind = Literal["supplier_offer_initial", "tour_promotion"]
PublishingConsoleItemStatus = Literal["ready", "blocked", "needs_attention"]

PublishingConsoleReadinessLevel = Literal["ready", "needs_action", "blocked", "published", "unknown"]
PublishingConsoleConversionTargetKind = Literal["exact_tour", "supplier_offer_landing", "none"]
PublishingConsoleCtaSafetyStatusLiteral = Literal[
    "exact_tour_ready",
    "missing_execution_link",
    "tour_not_listed",
    "media_blocked",
    "already_published",
    "not_applicable",
]

PublishingConsoleActionDangerLevel = Literal[
    "safe_read",
    "safe_mutation",
    "conversion_enabling",
    "public_dangerous",
]
PublishingConsoleActionSource = Literal["operator_workflow", "console_read_only", "future"]


class AdminPublishingConsoleActionAffordanceRead(BaseModel):
    """B15E: read-only action hints for a console row (no execution from this endpoint)."""

    model_config = ConfigDict(extra="forbid")

    code: str
    label: str
    kind: PublishingConsoleActionDangerLevel
    enabled: bool
    requires_confirmation: bool
    danger_level: PublishingConsoleActionDangerLevel
    admin_path: str
    method: Literal["GET", "POST", "PATCH"]
    implemented: bool
    disabled_reason: str | None = None
    source: PublishingConsoleActionSource


class AdminPublishingConsoleOfferDebugRead(BaseModel):
    """Technical fields for diagnostics (B15A advanced mode parity)."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int
    lifecycle_status: str
    packaging_status: str
    can_publish_now: bool
    next_missing_step: str | None = None
    effective_showcase_template_id: str | None = None
    primary_operator_action: str | None = None


class AdminPublishingConsoleTourDebugRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tour_id: int
    tour_code: str
    tour_status: str
    sales_mode: str
    seats_available: int
    seats_total: int
    catalog_customer_visible: bool


class AdminPublishingConsoleItemRead(BaseModel):
    """Single publishing candidate card."""

    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    kind: PublishingConsoleCandidateKind
    console_status: PublishingConsoleItemStatus
    title: str
    subtitle: str | None = None
    target_summary: str
    next_best_action: str | None = None
    blocked_reasons: list[str] = Field(default_factory=list)
    human_summary: str
    review_package_path: str | None = None
    admin_tour_path: str | None = None
    offer_debug: AdminPublishingConsoleOfferDebugRead | None = None
    tour_debug: AdminPublishingConsoleTourDebugRead | None = None
    # B15D — richer read-model (additive; still read-only console).
    readiness_summary: str = ""
    readiness_level: PublishingConsoleReadinessLevel = "unknown"
    conversion_target_kind: PublishingConsoleConversionTargetKind = "none"
    conversion_target_url: str | None = None
    cta_safety_status: PublishingConsoleCtaSafetyStatusLiteral = "not_applicable"
    primary_blocker: str | None = None
    blocker_codes: list[str] = Field(default_factory=list)
    next_action_code: str | None = None
    next_action_label: str | None = None
    admin_action_path: str | None = None
    preview_path: str | None = None
    source_status_summary: str | None = None
    audit_hint: str | None = None
    # B15E — action affordance metadata (read-only; mirrors operator_workflow / console hints).
    actions: list[AdminPublishingConsoleActionAffordanceRead] = Field(default_factory=list)


class AdminPublishingConsoleRead(BaseModel):
    """GET /admin/publishing-console — read-only queue projection."""

    model_config = ConfigDict(extra="forbid")

    items: list[AdminPublishingConsoleItemRead]
    total_returned: int
    console_notice: str = Field(
        default=(
            "Read-only publishing console preview. No publish, schedule, skip, retry, or send "
            "is executed from this view."
        ),
    )
    debug_notice: str = Field(
        default=("Technical fields are included under each item's offer_debug / tour_debug for diagnostics only."),
    )
    query_debug: dict[str, Any] | None = Field(
        default=None,
        description="Echo of normalized filters for support.",
    )
