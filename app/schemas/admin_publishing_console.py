"""B15B/B15D/B15E/B15F/B15K/B15L/B15M/B15P/B17A/B17A1: read-only Admin Publishing Console response DTOs (no publish / schedule / mutations)."""

from __future__ import annotations

from datetime import datetime
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

PublishingConsoleUiCardStatusTone = Literal["neutral", "success", "warning", "danger", "info"]

PublishingConsoleUiPrimaryActionKind = Literal["safe_read", "guarded_post", "future", "none"]


class AdminPublishingConsoleUiCardRead(BaseModel):
    """B15P: compact read-only presentation hints for a publishing-console list row (no execution)."""

    model_config = ConfigDict(extra="forbid")

    card_title: str | None = None
    card_subtitle: str | None = None
    status_badge: str
    status_label: str
    status_tone: PublishingConsoleUiCardStatusTone
    primary_line: str | None = None
    secondary_line: str | None = None
    primary_action_label: str | None = None
    primary_action_code: str | None = None
    primary_action_enabled: bool = False
    primary_action_kind: PublishingConsoleUiPrimaryActionKind = "none"
    primary_action_path: str | None = None
    secondary_action_label: str | None = None
    secondary_action_code: str | None = None
    secondary_action_enabled: bool = False
    warning_line: str | None = None
    blocker_line: str | None = None
    safety_line: str = Field(
        description="Short reminder that this GET is read-only (no publish / Telegram I/O).",
    )


def _placeholder_console_ui_card() -> AdminPublishingConsoleUiCardRead:
    """Satisfies validation until ``_finalize_console_item`` replaces with real B15P hints."""

    return AdminPublishingConsoleUiCardRead(
        status_badge="unknown",
        status_label="",
        status_tone="neutral",
        safety_line="",
    )


class AdminPublishingConsoleUiSectionRead(BaseModel):
    """B15P: suggested grouping for supplier-offer publishing-console detail rendering."""

    model_config = ConfigDict(extra="forbid")

    section_key: str
    title: str
    description: str | None = None
    display_order: int = Field(ge=0)


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


PublishingConsolePreviewPayloadStatus = Literal["available", "placeholder", "blocked", "not_applicable"]

PublishingConsolePreviewPayloadSource = Literal[
    "showcase_preview",
    "packaging_draft",
    "supplier_offer_fields",
    "tour_placeholder",
    "none",
]


class AdminPublishingConsolePreviewPayloadRead(BaseModel):
    """B15L: structured supplier-offer showcase preview payload for admin console (read-only; no send)."""

    model_config = ConfigDict(extra="forbid")

    payload_status: PublishingConsolePreviewPayloadStatus
    source: PublishingConsolePreviewPayloadSource
    title: str | None = None
    subtitle: str | None = None
    body_text: str | None = None
    caption_html: str | None = None
    primary_cta_label: str | None = None
    primary_cta_url: str | None = None
    secondary_cta_label: str | None = None
    secondary_cta_url: str | None = None
    media_reference: str | None = None
    media_status: str | None = None
    channel_kind: str | None = None
    channel_status: str | None = None
    channel_ref: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    safety_note: str = Field(
        description="Confirms this GET does not publish, schedule, or send Telegram traffic.",
    )
    generated_at: datetime | None = None
    publish_readiness_note: str | None = Field(
        default=None,
        description="How this payload relates to the same row's publish_readiness (read-only hint).",
    )
    template_library_note: str | None = Field(
        default=None,
        description="How this payload relates to the same row's template_library (read-only hint).",
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
    preview_payload: AdminPublishingConsolePreviewPayloadRead = Field(
        description="B15L: showcase-oriented preview fields for admin UI (read-only; supplier rows primary).",
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
    ui_card: AdminPublishingConsoleUiCardRead = Field(
        default_factory=_placeholder_console_ui_card,
        description="B15P: read-only UI alignment hints for list cards (replaced when building responses).",
    )


class AdminPublishingConsoleSupplierOfferConversionSummaryRead(BaseModel):
    """B15M: compact conversion closure projection for publishing-console detail."""

    model_config = ConfigDict(extra="forbid")

    has_tour_bridge: bool | None = None
    has_catalog_visible_tour: bool | None = None
    has_active_execution_link: bool | None = None
    next_missing_step: str | None = None


class AdminPublishingConsoleSupplierOfferLinkedTourSummaryRead(BaseModel):
    """B15M: linked bridged tour snapshot for publishing-console detail."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int | None = None
    tour_code: str | None = None
    tour_status: str | None = None
    catalog_listed_for_mini_app: bool | None = None


class AdminPublishingConsoleSupplierOfferPublicationSummaryRead(BaseModel):
    """B15M: publication / lifecycle snapshot from supplier offer (read-only)."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_status: str | None = None
    published_at: datetime | None = None
    showcase_chat_id: str | None = None
    showcase_message_id: int | None = None
    already_published: bool


class AdminPublishingConsoleSupplierOfferSafetySummaryRead(BaseModel):
    """B15M: explicit guard-rail flags for admin/OPS (documentation; all true for this GET)."""

    model_config = ConfigDict(extra="forbid")

    read_only: Literal[True] = True
    no_telegram_io: Literal[True] = True
    no_publish_attempt: Literal[True] = True
    no_prepare_chain_execution: Literal[True] = True
    no_layer_a_mutation: Literal[True] = True
    note: str


class AdminPublishingConsoleSupplierOfferDetailRead(BaseModel):
    """B15M/B15P: GET /admin/publishing-console/supplier-offers/{offer_id} — single-offer publishing console read view."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int
    candidate_key: str
    kind: Literal["supplier_offer_initial"] = "supplier_offer_initial"
    title: str | None = None
    subtitle: str | None = None
    console_status: PublishingConsoleItemStatus
    human_summary: str | None = None
    operator_summary: str | None = None
    review_package_path: str
    prepare_conversion_chain_plan_path: str | None = None
    publish_action_path: str | None = None
    publish_readiness: AdminPublishReadinessRead
    console_preview: AdminPublishingConsolePreviewRead
    template_library: AdminPublishingConsoleTemplateLibraryRead
    preview_payload: AdminPublishingConsolePreviewPayloadRead
    actions: list[AdminPublishingConsoleActionAffordanceRead] = Field(default_factory=list)
    prepare_conversion_chain_action: PrepareConversionChainActionAffordanceRead | None = None
    conversion_summary: AdminPublishingConsoleSupplierOfferConversionSummaryRead
    linked_tour_summary: AdminPublishingConsoleSupplierOfferLinkedTourSummaryRead
    publication_summary: AdminPublishingConsoleSupplierOfferPublicationSummaryRead
    safety_summary: AdminPublishingConsoleSupplierOfferSafetySummaryRead
    generated_at: datetime
    detail_notice: str = Field(
        default=(
            "Read-only publishing console detail. No publish, schedule, Telegram send, prepare_conversion_chain "
            "execution, or data mutation occurs from this endpoint."
        ),
    )
    ui_sections: list[AdminPublishingConsoleUiSectionRead] = Field(
        default_factory=list,
        description="B15P: suggested section order/labels for admin detail layouts (read-only hints).",
    )


class AdminPublishingConsoleEditorChannelSectionRead(BaseModel):
    """B17A/B17A1: editor-oriented channel slice (read-only; no persisted selection)."""

    model_config = ConfigDict(extra="forbid")

    channel_kind: PublishingConsoleChannelKind
    channel_status: PublishingConsoleChannelStatus
    channel_ref: str | None = None
    channel_summary: str = ""
    can_select_channel: bool = Field(default=False, description="B17A1: channel picker not available on this GET.")
    can_publish_to_channel: bool = Field(
        default=False,
        description="B17A1: no Telegram publish from this read-only editor endpoint.",
    )
    future_capability_hints: list[AdminPublishingConsoleFutureCapabilityHintRead] = Field(default_factory=list)
    payload_channel_kind: str | None = None
    payload_channel_status: str | None = None
    payload_channel_ref: str | None = None
    console_preview_channel_status: str | None = None
    editor_note: str = Field(
        default="Channel targets are read-only projections; this GET does not persist a channel choice.",
    )


class AdminPublishingConsoleEditorTemplateSectionRead(BaseModel):
    """B17A/B17A1: editor-oriented template slice (read-only)."""

    model_config = ConfigDict(extra="forbid")

    template_kind: PublishingConsoleTemplateKind
    template_family: PublishingConsoleTemplateFamily
    template_version: str = ""
    template_source_status: PublishingConsoleTemplateSourceStatus = "not_applicable"
    template_source_summary: str = ""
    library_family: PublishingConsoleTemplateLibraryFamily
    selected_template_id: str | None = None
    recommended_template_id: str | None = None
    library_template_version: str | None = None
    selection_reason: str | None = None
    available_template_count: int = Field(ge=0, default=0)
    console_preview_template_id: str | None = None
    can_select_template: bool = Field(default=False, description="B17A1: template selection API not on this GET.")
    can_edit_template: bool = Field(default=False, description="B17A1: template editor not on this GET.")
    future_capability_hints: list[AdminPublishingConsoleFutureCapabilityHintRead] = Field(default_factory=list)
    editor_note: str = Field(
        default="Template variants are hints from the read model; this GET does not persist template selection.",
    )


class AdminPublishingConsoleEditorPreviewSectionRead(BaseModel):
    """B17A/B17A1: editor-oriented preview slice (read-only)."""

    model_config = ConfigDict(extra="forbid")

    console_preview_status: PublishingConsolePreviewStatus
    payload_status: PublishingConsolePreviewPayloadStatus
    payload_source: PublishingConsolePreviewPayloadSource
    preview_available: bool = Field(
        description="True when console or payload preview is in available state (machine-readable).",
    )
    template_preview_path: str | None = None
    console_preview_path: str | None = None
    title: str | None = None
    subtitle: str | None = None
    body_text_excerpt: str | None = Field(
        default=None,
        description="Truncated body_text for card layout; full text remains in source_snapshot.preview_payload.",
    )
    has_caption_html: bool = False
    can_edit_copy: bool = Field(default=False, description="B17A1: draft copy edit not on this GET.")
    can_refresh_preview: bool = Field(
        default=False,
        description="B17A1: explicit refresh action not exposed from this GET-only editor.",
    )


class AdminPublishingConsoleEditorCtaSectionRead(BaseModel):
    """B17A: conversion / CTA slice for editor layout (read-only)."""

    model_config = ConfigDict(extra="forbid")

    conversion_target_kind: PublishingConsoleConversionTargetKind
    conversion_target_url: str | None = None
    cta_safety_status: PublishingConsoleCtaSafetyStatusLiteral
    primary_cta_label: str | None = None
    primary_cta_url: str | None = None
    secondary_cta_label: str | None = None
    secondary_cta_url: str | None = None
    console_primary_cta_label: str | None = None
    console_target_url: str | None = None


class AdminPublishingConsoleEditorMediaSectionRead(BaseModel):
    """B17A/B17A1: media policy slice (read-only)."""

    model_config = ConfigDict(extra="forbid")

    media_policy_status: PublishingConsoleMediaPolicyStatus
    media_summary: str = ""
    payload_media_reference: str | None = None
    payload_media_status: str | None = None
    console_media_status: str | None = None
    can_upload_media: bool = Field(default=False, description="B17A1: media upload not on this GET.")
    can_generate_card: bool = Field(default=False, description="B17A1: card generation not on this GET.")


class AdminPublishingConsoleEditorReadinessSectionRead(BaseModel):
    """B17A: readiness / gates slice (read-only)."""

    model_config = ConfigDict(extra="forbid")

    readiness_summary: str = ""
    readiness_level: PublishingConsoleReadinessLevel = "unknown"
    console_status: PublishingConsoleItemStatus
    item_primary_blocker: str | None = None
    gate_summary: str = ""
    publish_readiness_summary: str = ""
    next_action_code: str | None = None
    next_action_label: str | None = None


class AdminPublishingConsoleEditorSafetySectionRead(BaseModel):
    """B17A/B17A1: safety / boundary copy for editor chrome (read-only)."""

    model_config = ConfigDict(extra="forbid")

    detail_notice: str
    ui_card_safety_line: str
    editor_boundary_note: str = Field(
        default=(
            "B17A editor view is read-only: no draft edits, channel/template persistence, "
            "prepare_conversion_chain execution, or Telegram publish from this GET."
        ),
    )
    read_only: Literal[True] = True
    no_telegram_io: Literal[True] = True
    no_publish_attempt: Literal[True] = True
    no_scheduler: Literal[True] = True
    no_auto_publish: Literal[True] = True
    no_prepare_chain_execution: Literal[True] = True
    no_layer_a_mutation: Literal[True] = True
    no_mini_app_b11_change: Literal[True] = True


class AdminPublishingConsoleEditorSourceSnapshotRead(BaseModel):
    """B17A: same B15 nested objects as publishing-console detail, for a stable client contract."""

    model_config = ConfigDict(extra="forbid")

    publish_readiness: AdminPublishReadinessRead
    console_preview: AdminPublishingConsolePreviewRead
    template_library: AdminPublishingConsoleTemplateLibraryRead
    preview_payload: AdminPublishingConsolePreviewPayloadRead
    ui_card: AdminPublishingConsoleUiCardRead
    safety_summary: AdminPublishingConsoleSupplierOfferSafetySummaryRead


class AdminPublishingConsoleEditorDetailRead(BaseModel):
    """B17A: GET …/editor — read-only editor-oriented projection (no mutation / no publish)."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int
    candidate_key: str
    kind: Literal["supplier_offer_initial"] = "supplier_offer_initial"
    title: str | None = None
    editor_status: str = Field(description="Mirrors console row status (ready | blocked | needs_attention).")
    editor_status_label: str
    editor_status_tone: PublishingConsoleUiCardStatusTone
    source_detail_path: str
    review_package_path: str
    publishing_console_detail_path: str
    prepare_conversion_chain_plan_path: str | None = None
    channel_section: AdminPublishingConsoleEditorChannelSectionRead
    template_section: AdminPublishingConsoleEditorTemplateSectionRead
    preview_section: AdminPublishingConsoleEditorPreviewSectionRead
    cta_section: AdminPublishingConsoleEditorCtaSectionRead
    media_section: AdminPublishingConsoleEditorMediaSectionRead
    readiness_section: AdminPublishingConsoleEditorReadinessSectionRead
    safety_section: AdminPublishingConsoleEditorSafetySectionRead
    future_actions: list[AdminPublishingConsoleFutureCapabilityHintRead] = Field(
        default_factory=list,
        description="B17A/B17A1: merged template + channel hints plus optional publish placeholders (read-only).",
    )
    source_snapshot: AdminPublishingConsoleEditorSourceSnapshotRead
    generated_at: datetime
    editor_notice: str = Field(
        default=(
            "B17A read-only channel/template editor layout. No selection, draft edits, or publish is performed "
            "from this endpoint."
        ),
    )


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
