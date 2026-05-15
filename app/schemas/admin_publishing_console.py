"""B15B/B15D/B15E/B15F/B15K: read-only Admin Publishing Console response DTOs (no publish / schedule / mutations)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.admin_publish_readiness import AdminPublishReadinessRead
from app.schemas.admin_prepare_conversion_chain_plan import (
    PrepareConversionChainActionAffordanceRead,
    PrepareConversionChainPlanSummaryStatus,
)

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

PublishingConsoleSourceKind = Literal["supplier_offer", "tour"]
PublishingConsoleTemplateKind = Literal["supplier_offer_showcase", "tour_promotion_placeholder", "none"]
PublishingConsoleTemplateSourceStatus = Literal["available", "partial", "unavailable", "not_applicable"]
PublishingConsoleChannelKind = Literal["telegram_showcase_channel", "none"]
PublishingConsoleChannelStatus = Literal["configured", "not_configured", "not_applicable"]
PublishingConsoleMediaPolicyStatus = Literal[
    "publish_safe_metadata_only",
    "media_review_pending",
    "media_blocked",
    "text_only_channel_ok",
    "not_applicable",
]

PublishingConsolePreviewStatus = Literal["available", "placeholder", "blocked", "not_applicable"]

PublishingConsoleTemplateFamily = Literal[
    "supplier_offer_showcase",
    "tour_promotion",
    "custom_request_cta",
    "unknown",
]

PublishingConsoleTemplateLibraryFamily = Literal[
    "supplier_offer_showcase",
    "tour_promotion",
    "unknown",
]

PublishingConsoleTemplateLibraryEntryStatus = Literal[
    "available",
    "future",
    "not_applicable",
    "blocked",
]


class AdminPublishingConsoleFutureCapabilityHintRead(BaseModel):
    """B15F: placeholder rows for template/channel UX not built yet (read-only)."""

    model_config = ConfigDict(extra="forbid")

    code: str
    label: str
    implemented: bool
    enabled: bool
    disabled_reason: str | None = None


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


class AdminPublishingConsolePreviewRead(BaseModel):
    """B15F2/B15F3: compact template/preview UX layer for console rows (read-only; no publish)."""

    model_config = ConfigDict(extra="forbid")

    preview_status: PublishingConsolePreviewStatus
    template_family: PublishingConsoleTemplateFamily
    template_id: str | None = None
    template_version: str | None = None
    title: str | None = None
    summary: str | None = None
    primary_cta_label: str | None = None
    target_kind: str | None = None
    target_url: str | None = None
    media_status: str | None = None
    channel_status: str | None = None
    preview_path: str | None = None
    safety_note: str = Field(
        description="Why no public side effect occurs from this read-only console endpoint.",
    )
    next_action_code: str | None = None
    next_action_label: str | None = None


class AdminPublishingConsoleTemplateLibraryEntryRead(BaseModel):
    """B15K: one possible template variant for a console row (read-only metadata)."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    label: str
    description: str
    status: PublishingConsoleTemplateLibraryEntryStatus
    disabled_reason: str | None = None


class AdminPublishingConsoleTemplateLibraryRead(BaseModel):
    """B15K: compact template library / variant projection (read-only; no selection API)."""

    model_config = ConfigDict(extra="forbid")

    family: PublishingConsoleTemplateLibraryFamily
    selected_template_id: str | None = None
    recommended_template_id: str | None = None
    template_version: str | None = None
    available_templates: list[AdminPublishingConsoleTemplateLibraryEntryRead] = Field(default_factory=list)
    selection_reason: str | None = None
    safety_note: str = Field(
        description="Why no public publish/send is executed from this read-only console projection.",
    )


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
    prepare_conversion_chain_plan_path: str | None = Field(
        default=None,
        description="When row is supplier-offer scoped: GET prepare_conversion_chain plan preview (B16D1).",
    )
    prepare_conversion_chain_plan_status: PrepareConversionChainPlanSummaryStatus | None = Field(
        default=None,
        description="When row is supplier-offer scoped: chain readiness summary (B16D1.2).",
    )
    prepare_conversion_chain_recommended_action: str | None = Field(
        default=None,
        description="When row is supplier-offer scoped: recommended next action (B16D1.2).",
    )
    prepare_conversion_chain_blockers_count: int | None = Field(
        default=None,
        description="When row is supplier-offer scoped: distinct blocker count (B16D1.2).",
    )
    prepare_conversion_chain_action: PrepareConversionChainActionAffordanceRead | None = Field(
        default=None,
        description="When supplier-offer scoped: B16D2D POST affordance metadata (read-only).",
    )
    publish_readiness: AdminPublishReadinessRead = Field(
        description="B15H: suggest-only publish readiness for this row (read-only).",
    )
    console_preview: AdminPublishingConsolePreviewRead = Field(
        description="B15F2/B15F3: template/preview clarity for admin UX (read-only).",
    )
    template_library: AdminPublishingConsoleTemplateLibraryRead = Field(
        description="B15K: possible template variants and selection hints (read-only).",
    )
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
    # B15F — template/source/channel visibility (read-only; no editor or selector).
    source_kind: PublishingConsoleSourceKind = "supplier_offer"
    source_id: int = 0
    source_title: str = ""
    template_kind: PublishingConsoleTemplateKind = "none"
    template_version: str = ""
    template_source_status: PublishingConsoleTemplateSourceStatus = "not_applicable"
    template_source_summary: str = ""
    template_preview_available: bool = False
    template_preview_path: str | None = None
    channel_kind: PublishingConsoleChannelKind = "none"
    channel_status: PublishingConsoleChannelStatus = "not_applicable"
    channel_ref: str | None = None
    channel_summary: str = ""
    media_policy_status: PublishingConsoleMediaPolicyStatus = "not_applicable"
    media_summary: str = ""
    template_actions: list[AdminPublishingConsoleFutureCapabilityHintRead] = Field(default_factory=list)
    channel_actions: list[AdminPublishingConsoleFutureCapabilityHintRead] = Field(default_factory=list)


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
