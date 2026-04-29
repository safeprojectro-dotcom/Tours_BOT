"""Supplier-admin API request/response models (Layer B)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    SupplierServiceComposition,
    TourSalesMode,
)


class SupplierOfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    supplier_reference: str | None
    title: str
    description: str
    program_text: str | None
    departure_datetime: datetime
    return_datetime: datetime
    transport_notes: str | None
    vehicle_label: str | None
    showcase_photo_url: str | None = None
    boarding_places_text: str | None = None
    seats_total: int
    base_price: Decimal | None
    currency: str | None
    service_composition: SupplierServiceComposition
    sales_mode: TourSalesMode
    payment_mode: SupplierOfferPaymentMode
    lifecycle_status: SupplierOfferLifecycle
    moderation_rejection_reason: str | None = None
    published_at: datetime | None = None
    showcase_chat_id: str | None = None
    showcase_message_id: int | None = None
    created_at: datetime
    updated_at: datetime
    # B2: supplier-facing intake (no admin-only packaging audit fields on supplier API)
    cover_media_reference: str | None = None
    media_references: list[Any] | dict[str, Any] | None = None
    included_text: str | None = None
    excluded_text: str | None = None
    short_hook: str | None = None
    marketing_summary: str | None = None
    discount_code: str | None = None
    discount_percent: Decimal | None = None
    discount_amount: Decimal | None = None
    discount_valid_until: datetime | None = None
    recurrence_type: str | None = None
    recurrence_rule: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    supplier_admin_notes: str | None = None


class AdminSupplierOfferRead(SupplierOfferRead):
    """Central-admin / moderation read model: includes B2 admin-only and packaging sub-state."""

    model_config = ConfigDict(from_attributes=True)

    admin_internal_notes: str | None = None
    packaging_status: SupplierOfferPackagingStatus
    missing_fields_json: list[Any] | dict[str, Any] | None = None
    quality_warnings_json: list[Any] | dict[str, Any] | None = None
    # B4: extended draft (Telegram post, CTA, Mini App long text, image hints). Not exposed on supplier-admin API.
    packaging_draft_json: list[Any] | dict[str, Any] | None = None
    # B5: last packaging review (orthogonal to offer lifecycle; approve != publish)
    packaging_reviewed_at: datetime | None = None
    packaging_reviewed_by: str | None = None
    packaging_rejection_reason: str | None = None
    clarification_reason: str | None = None


class SupplierOfferListRead(BaseModel):
    items: list[SupplierOfferRead]
    total_returned: int


class AdminSupplierOfferListRead(BaseModel):
    items: list[AdminSupplierOfferRead]
    total_returned: int


class AdminSupplierOfferRejectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=4000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("reason must not be empty")
        return s


class AdminSupplierOfferPublishResult(BaseModel):
    offer: AdminSupplierOfferRead
    telegram_message_id: int | None = None


class SupplierOfferExecutionLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_offer_id: int
    tour_id: int
    link_status: str
    close_reason: str | None = None
    link_note: str | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SupplierOfferExecutionLinkListRead(BaseModel):
    items: list[SupplierOfferExecutionLinkRead]
    total_returned: int


class AdminSupplierOfferShowcasePreviewRead(BaseModel):
    """Read-only: final channel showcase caption as rendered by ``build_showcase_publication`` (B12/B13.4)."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int
    lifecycle_status: str
    caption_html: str
    publication_mode: Literal["text_only", "photo_with_caption"]
    showcase_photo_url: str | None
    disable_web_page_preview: bool
    cta_detalii_href: str | None
    cta_rezerva_href: str | None
    can_publish_now: bool
    warnings: list[str]
    preview_notice: str = Field(
        default=(
            "Local preview only — nothing was sent to Telegram. "
            "Previzualizare locală — nu a fost trimis nimic pe Telegram."
        ),
    )


class AdminSupplierOfferBridgeReadinessRead(BaseModel):
    """Read-only: ``POST .../tour-bridge`` precursor checks (packaging + required fields)."""

    model_config = ConfigDict(extra="forbid")

    can_attempt_bridge: bool
    missing_fields: list[str]
    blocking_codes: list[str]


class AdminSupplierOfferLinkedTourCatalogRead(BaseModel):
    """Linked bridged Tour: Mini App catalog activation readiness (orthogonal to showcase lifecycle)."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int
    tour_code: str
    tour_status: str
    sales_mode: TourSalesMode
    seats_available: int
    catalog_activation_missing_fields: list[str]
    catalog_listed_for_mini_app: bool
    can_activate_for_catalog: bool
    b8_same_offer_date_conflict: bool


class AdminSupplierOfferExecutionLinksReviewRead(BaseModel):
    """Execution-link slice for conversion path (requires lifecycle ``published`` to create)."""

    model_config = ConfigDict(extra="forbid")

    total_links_returned: int
    active_link: SupplierOfferExecutionLinkRead | None
    can_create_execution_link: bool
    execution_link_precheck_note: str | None = None


class AdminSupplierOfferMiniAppConversionPreviewRead(BaseModel):
    """Mirror of landing actionability when offer lifecycle is ``published`` (else not applicable)."""

    model_config = ConfigDict(extra="forbid")

    applicable: bool
    actionability_state: str | None = None
    has_execution_link: bool | None = None
    linked_tour_id: int | None = None
    linked_tour_code: str | None = None


class AdminSupplierOfferConversionClosureRead(BaseModel):
    """Read-only closure checklist for supplier-offer → central Mini App catalog (aggregates existing gates)."""

    model_config = ConfigDict(extra="forbid")

    has_tour_bridge: bool
    has_catalog_visible_tour: bool
    has_active_execution_link: bool
    supplier_offer_landing_routes_to_tour: bool
    bot_deeplink_routes_to_tour: bool
    central_catalog_contains_tour: bool
    next_missing_step: str | None = None


class AdminSupplierOfferAiPublicCopyReviewRead(BaseModel):
    """AI public copy fact-lock slice (read-only). Compares optional ``packaging_draft_json.ai_public_copy_v1`` to live facts."""

    model_config = ConfigDict(extra="forbid")

    source_facts_version: str
    snapshot_content_hash: str
    ai_block_present: bool
    packaged_snapshot_ref: str | None = None
    snapshot_stale: bool = False
    fact_claims_present: bool = False
    fact_lock_passed: bool = True
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AdminSupplierOfferReviewPackageRead(BaseModel):
    """Read-only aggregated admin review surface (no mutations)."""

    model_config = ConfigDict(extra="forbid")

    offer: AdminSupplierOfferRead
    showcase_preview: AdminSupplierOfferShowcasePreviewRead
    bridge_readiness: AdminSupplierOfferBridgeReadinessRead
    active_tour_bridge: AdminSupplierOfferTourBridgeRead | None
    linked_tour_catalog: AdminSupplierOfferLinkedTourCatalogRead | None
    execution_links_review: AdminSupplierOfferExecutionLinksReviewRead
    mini_app_conversion_preview: AdminSupplierOfferMiniAppConversionPreviewRead
    conversion_closure: AdminSupplierOfferConversionClosureRead
    ai_public_copy_review: AdminSupplierOfferAiPublicCopyReviewRead
    warnings: list[str]
    recommended_next_actions: list[str]


class AdminSupplierOfferExecutionLinkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tour_id: int = Field(gt=0)
    link_note: str | None = Field(default=None, max_length=4000)

    @field_validator("link_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminSupplierOfferExecutionLinkCloseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="unlinked", max_length=32)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"unlinked", "retracted", "invalidated"}:
            raise ValueError("reason must be one of: unlinked, retracted, invalidated")
        return s


class SupplierOfferCreate(BaseModel):
    supplier_reference: str | None = Field(default=None, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=0)
    program_text: str | None = None
    departure_datetime: datetime
    return_datetime: datetime
    transport_notes: str | None = None
    vehicle_label: str | None = Field(default=None, max_length=128)
    showcase_photo_url: str | None = Field(default=None, max_length=1024)
    boarding_places_text: str | None = Field(default=None, max_length=4000)
    seats_total: int = Field(default=0, ge=0)
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    service_composition: SupplierServiceComposition = SupplierServiceComposition.TRANSPORT_ONLY
    sales_mode: TourSalesMode = TourSalesMode.PER_SEAT
    payment_mode: SupplierOfferPaymentMode = SupplierOfferPaymentMode.PLATFORM_CHECKOUT
    cover_media_reference: str | None = Field(default=None, max_length=1024)
    media_references: list[Any] | dict[str, Any] | None = None
    included_text: str | None = None
    excluded_text: str | None = None
    short_hook: str | None = Field(default=None, max_length=512)
    marketing_summary: str | None = None
    discount_code: str | None = Field(default=None, max_length=64)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    discount_amount: Decimal | None = Field(default=None, ge=0)
    discount_valid_until: datetime | None = None
    recurrence_type: str | None = Field(default=None, max_length=64)
    recurrence_rule: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    supplier_admin_notes: str | None = None

    @field_validator("supplier_reference", "currency", "vehicle_label", "showcase_photo_url", "cover_media_reference")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("boarding_places_text")
    @classmethod
    def strip_boarding(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("title", "description")
    @classmethod
    def strip_required(cls, v: str) -> str:
        return v.strip()

    @field_validator("discount_code", "recurrence_type")
    @classmethod
    def strip_discount_recurrence(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("included_text", "excluded_text", "marketing_summary", "recurrence_rule", "supplier_admin_notes")
    @classmethod
    def strip_long_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip()

    @field_validator("short_hook")
    @classmethod
    def strip_short_hook(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def validate_valid_window(self) -> SupplierOfferCreate:
        if self.valid_from is not None and self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until must not be before valid_from")
        return self


class SupplierOfferUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_reference: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    program_text: str | None = None
    departure_datetime: datetime | None = None
    return_datetime: datetime | None = None
    transport_notes: str | None = None
    vehicle_label: str | None = Field(default=None, max_length=128)
    showcase_photo_url: str | None = Field(default=None, max_length=1024)
    boarding_places_text: str | None = Field(default=None, max_length=4000)
    seats_total: int | None = Field(default=None, ge=0)
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    service_composition: SupplierServiceComposition | None = None
    sales_mode: TourSalesMode | None = None
    payment_mode: SupplierOfferPaymentMode | None = None
    lifecycle_status: SupplierOfferLifecycle | None = None
    cover_media_reference: str | None = Field(default=None, max_length=1024)
    media_references: list[Any] | dict[str, Any] | None = None
    included_text: str | None = None
    excluded_text: str | None = None
    short_hook: str | None = Field(default=None, max_length=512)
    marketing_summary: str | None = None
    discount_code: str | None = Field(default=None, max_length=64)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    discount_amount: Decimal | None = Field(default=None, ge=0)
    discount_valid_until: datetime | None = None
    recurrence_type: str | None = Field(default=None, max_length=64)
    recurrence_rule: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    supplier_admin_notes: str | None = None

    @field_validator("supplier_reference", "currency", "vehicle_label", "showcase_photo_url", "cover_media_reference")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("boarding_places_text")
    @classmethod
    def strip_boarding(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("title", "description", "program_text", "transport_notes")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip()

    @field_validator("discount_code", "recurrence_type")
    @classmethod
    def strip_discount_recurrence_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("included_text", "excluded_text", "marketing_summary", "recurrence_rule", "supplier_admin_notes")
    @classmethod
    def strip_long_text_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip()

    @field_validator("short_hook")
    @classmethod
    def strip_short_hook_u(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def validate_valid_window(self) -> SupplierOfferUpdate:
        vf, vu = self.valid_from, self.valid_until
        if vf is not None and vu is not None and vu < vf:
            raise ValueError("valid_until must not be before valid_from")
        return self


class AdminPackagingApproveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accept_warnings: bool = False
    reviewed_by: str | None = Field(default=None, max_length=256)

    @field_validator("reviewed_by")
    @classmethod
    def strip_reviewer(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminPackagingReasonBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=4000)
    reviewed_by: str | None = Field(default=None, max_length=256)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("reason must not be empty")
        return s

    @field_validator("reviewed_by")
    @classmethod
    def strip_reviewer2(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminPackagingTelegramDraftPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telegram_post_draft: str = Field(min_length=1, max_length=20000)

    @field_validator("telegram_post_draft")
    @classmethod
    def strip_tg(cls, v: str) -> str:
        return v.rstrip() if v else v


class AdminMediaReviewApproveBody(BaseModel):
    """B7.1: optional reviewer label for cover approve."""

    model_config = ConfigDict(extra="forbid")

    reviewed_by: str | None = Field(default=None, max_length=256)

    @field_validator("reviewed_by")
    @classmethod
    def strip_reviewer_mra(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminMediaReviewRejectBody(BaseModel):
    """B7.1: reject with kind → rejected_bad_quality | rejected_irrelevant."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=1, max_length=4000)
    reviewed_by: str | None = Field(default=None, max_length=256)

    @field_validator("kind")
    @classmethod
    def kind_ok(cls, v: str) -> str:
        s = (v or "").strip().lower()
        if s not in ("bad_quality", "irrelevant"):
            raise ValueError("kind must be 'bad_quality' or 'irrelevant'")
        return s

    @field_validator("reason")
    @classmethod
    def strip_reason_mrr(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("reason must not be empty")
        return s

    @field_validator("reviewed_by")
    @classmethod
    def strip_reviewer_mrr(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminMediaReviewFallbackBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=4000)
    reviewed_by: str | None = Field(default=None, max_length=256)

    @field_validator("reason")
    @classmethod
    def strip_reason_mrf(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("reviewed_by")
    @classmethod
    def strip_reviewer_mrf(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminSupplierOfferTourBridgeCreateBody(BaseModel):
    """B10: optional body for `POST /admin/supplier-offers/{id}/tour-bridge` (empty object allowed)."""

    model_config = ConfigDict(extra="forbid")

    created_by: str | None = None
    notes: str | None = None
    existing_tour_id: int | None = None


class AdminSupplierOfferTourBridgeRead(BaseModel):
    """B10: response for tour bridge create/get."""

    id: int
    supplier_offer_id: int
    tour_id: int
    bridge_status: str
    bridge_kind: str
    tour_status: str
    created_at: datetime
    idempotent_replay: bool
    warnings: list[str]
    notes: str | None
    source_packaging_status: str
    source_lifecycle_status: str


class AdminSupplierOfferRecurrenceDraftToursBody(BaseModel):
    """B8: generate additional draft catalog tours from an approved offer template (explicit admin; no auto-activate)."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=1, le=24, description="Number of tour instances to create.")
    interval_days: int = Field(ge=1, le=366, description="Calendar days between consecutive departures.")
    start_offset_days: int = Field(
        default=0,
        ge=0,
        le=730,
        description="Additional calendar days before the first instance (from template departure).",
    )


class AdminSupplierOfferRecurrenceDraftTourItemRead(BaseModel):
    tour_id: int
    sequence_index: int
    departure_datetime: datetime
    return_datetime: datetime


class AdminSupplierOfferRecurrenceDraftToursRead(BaseModel):
    source_supplier_offer_id: int
    items: list[AdminSupplierOfferRecurrenceDraftTourItemRead]
