"""Read-only admin API response models."""

from __future__ import annotations

from datetime import datetime, time as time_type
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    BookingStatus,
    CancellationStatus,
    SupplierLegalEntityType,
    PaymentStatus,
    SupplierOnboardingStatus,
    SupplierServiceComposition,
    TourSalesMode,
    TourStatus,
)
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind


class AdminTourListItem(BaseModel):
    id: int
    code: str
    title_default: str
    departure_datetime: datetime
    status: TourStatus
    sales_mode: TourSalesMode
    seats_total: int
    seats_available: int
    currency: str
    base_price: Decimal


class AdminTourListRead(BaseModel):
    items: list[AdminTourListItem]
    total_returned: int


class AdminTourCreate(BaseModel):
    """Admin-only create payload for core `Tour` fields (no translations / boarding in this step)."""

    code: str = Field(min_length=1, max_length=64)
    title_default: str = Field(min_length=1, max_length=255)
    short_description_default: str | None = None
    full_description_default: str | None = None
    duration_days: int = Field(ge=1)
    departure_datetime: datetime
    return_datetime: datetime
    base_price: Decimal = Field(ge=0)
    currency: str = Field(min_length=1, max_length=8)
    seats_total: int = Field(ge=0)
    sales_deadline: datetime | None = None
    sales_mode: TourSalesMode = TourSalesMode.PER_SEAT
    status: TourStatus
    guaranteed_flag: bool = False

    @field_validator("code", "currency")
    @classmethod
    def strip_ws(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s


class AdminTourCoreUpdate(BaseModel):
    """
    Partial update of core `Tour` columns (same family as create). Forbidden: `code`, `cover_media_reference`
    (use `PUT /admin/tours/{tour_id}/cover` for cover).
    """

    model_config = ConfigDict(extra="forbid")

    title_default: str | None = Field(default=None, min_length=1, max_length=255)
    short_description_default: str | None = None
    full_description_default: str | None = None
    duration_days: int | None = Field(default=None, ge=1)
    departure_datetime: datetime | None = None
    return_datetime: datetime | None = None
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=8)
    seats_total: int | None = Field(default=None, ge=0)
    sales_deadline: datetime | None = None
    sales_mode: TourSalesMode | None = None
    status: TourStatus | None = None
    guaranteed_flag: bool | None = None

    @field_validator("currency")
    @classmethod
    def strip_currency(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("currency must not be empty or whitespace-only")
        return s


class AdminBoardingPointCreate(BaseModel):
    """Create one boarding stop for a tour (admin-only)."""

    city: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=255)
    time: time_type
    notes: str | None = None

    @field_validator("city", "address")
    @classmethod
    def strip_required_non_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s

    @field_validator("notes")
    @classmethod
    def empty_notes_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s if s else None


class AdminBoardingPointUpdate(BaseModel):
    """Partial update of core `BoardingPoint` columns only; no `tour_id` (no reassignment in this slice)."""

    model_config = ConfigDict(extra="forbid")

    city: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    time: time_type | None = None
    notes: str | None = None

    @field_validator("city", "address")
    @classmethod
    def strip_required_when_set(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s

    @field_validator("notes")
    @classmethod
    def empty_notes_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s if s else None


class AdminTourTranslationUpsert(BaseModel):
    """
    Create or merge-update one `TourTranslation` row for `language_code` in the path.
    On **create**, `title` must be included in the JSON body. On **update**, send only fields to change.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=255)
    short_description: str | None = None
    full_description: str | None = None
    program_text: str | None = None
    included_text: str | None = None
    excluded_text: str | None = None

    @field_validator("title")
    @classmethod
    def title_non_blank_if_present(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("title must not be empty or whitespace-only when provided")
        return s

    @field_validator(
        "short_description",
        "full_description",
        "program_text",
        "included_text",
        "excluded_text",
    )
    @classmethod
    def optional_long_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s if s else None


class AdminBoardingPointTranslationUpsert(BaseModel):
    """
    Create or merge-update one `BoardingPointTranslation` row for `language_code` in the path.
    On **create**, `city` and `address` must be in the JSON body. Core boarding `time` is not mutable here.
    """

    model_config = ConfigDict(extra="forbid")

    city: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator("city", "address")
    @classmethod
    def strip_required_when_set(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only when provided")
        return s

    @field_validator("notes")
    @classmethod
    def optional_notes(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s if s else None


class AdminTourCoverSet(BaseModel):
    """Set a single cover/media reference (URL or storage key) — no upload in this slice."""

    cover_media_reference: str = Field(min_length=1, max_length=1024)

    @field_validator("cover_media_reference")
    @classmethod
    def strip_non_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("cover_media_reference must not be empty or whitespace-only")
        return s


class AdminTranslationSummaryItem(BaseModel):
    """Read-only snippet per language (no full long-form content in admin detail MVP)."""

    language_code: str
    title: str


class AdminOrderListItem(BaseModel):
    id: int
    user_id: int
    tour_id: int
    tour_code: str
    seats_count: int
    total_amount: Decimal
    currency: str
    created_at: datetime
    lifecycle_kind: AdminOrderLifecycleKind
    lifecycle_summary: str


class AdminOrderListRead(BaseModel):
    items: list[AdminOrderListItem]
    total_returned: int


class AdminOrderPersistenceSnapshot(BaseModel):
    """Persisted enum fields for audit. Prefer `lifecycle_kind` / `lifecycle_summary` for operational meaning."""

    booking_status: BookingStatus
    payment_status: PaymentStatus
    cancellation_status: CancellationStatus


class AdminTourSummary(BaseModel):
    id: int
    code: str
    title_default: str
    departure_datetime: datetime
    status: TourStatus


class AdminBoardingPointTranslationItem(BaseModel):
    """Per-language text overrides for a boarding stop (city/address/notes only)."""

    language_code: str
    city: str
    address: str
    notes: str | None = None


class AdminBoardingPointSummary(BaseModel):
    id: int
    city: str
    address: str
    time: time_type
    notes: str | None = None
    translations: list[AdminBoardingPointTranslationItem] = Field(
        default_factory=list,
        description="Optional per-language overrides; core `time` stays on the boarding point row.",
    )


class AdminTourDetailRead(BaseModel):
    """Read-only operational view of a tour; not an edit form."""

    id: int
    code: str
    title_default: str
    short_description_default: str | None = None
    full_description_default: str | None = None
    duration_days: int
    departure_datetime: datetime
    return_datetime: datetime
    base_price: Decimal
    currency: str
    seats_total: int
    seats_available: int
    sales_deadline: datetime | None
    sales_mode: TourSalesMode
    status: TourStatus
    guaranteed_flag: bool
    cover_media_reference: str | None = Field(
        default=None,
        description="Single cover image/media reference (URL or storage key); not an upload endpoint.",
    )
    created_at: datetime
    updated_at: datetime
    translations: list[AdminTranslationSummaryItem] = Field(
        default_factory=list,
        description="Per-language titles (read-only summary).",
    )
    boarding_points: list[AdminBoardingPointSummary] = Field(
        default_factory=list,
        description="Boarding stops for this tour (read-only).",
    )
    orders_count: int = Field(
        description="Total order rows linked to this tour (visibility metric, not business interpretation).",
    )


class AdminPaymentSummaryItem(BaseModel):
    id: int
    provider: str
    external_payment_id: str | None
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime


class AdminHandoffGroupFollowupQueueFilter(str, Enum):
    """Phase 7 / Step 15 — narrow list filter for ``group_followup_start`` queue buckets only."""

    awaiting_assignment = "awaiting_assignment"
    assigned_open = "assigned_open"
    in_work = "in_work"
    resolved = "resolved"


GroupFollowupQueueState = Literal["awaiting_assignment", "assigned_open", "in_work", "resolved"]


class AdminHandoffSummaryItem(BaseModel):
    id: int
    status: str
    reason: str
    priority: str
    created_at: datetime
    updated_at: datetime
    is_group_followup: bool = Field(
        default=False,
        description="True when reason is group_followup_start (narrow Phase 7 group→private follow-up chain).",
    )
    source_label: str | None = Field(
        default=None,
        description="Human-readable origin label when is_group_followup; read-only.",
    )
    is_assigned_group_followup: bool = Field(
        default=False,
        description="True only for group_followup_start with assigned_operator_id set; read-only.",
    )
    group_followup_work_label: str | None = Field(
        default=None,
        description="Triage copy for group_followup_start only (assigned vs awaiting); None for other reasons.",
    )
    group_followup_resolution_label: str | None = Field(
        default=None,
        description="Read-only: set when group_followup_start is closed (resolved); None otherwise.",
    )
    group_followup_queue_state: GroupFollowupQueueState | None = Field(
        default=None,
        description="Phase 7 / Step 15: single queue bucket for group_followup_start only; None for other reasons.",
    )
    is_full_bus_sales_assistance: bool = Field(
        default=False,
        description="True when reason is structured full_bus_sales_assistance (Phase 7.1 / Step 5).",
    )
    full_bus_sales_assistance_label: str | None = Field(
        default=None,
        description="Operator-facing label for full-bus commercial assistance; None when not applicable.",
    )
    assistance_context_tour_code: str | None = Field(
        default=None,
        description="Tour code from full_bus_sales_assistance reason payload when present.",
    )


class AdminHandoffAssignBody(BaseModel):
    """Phase 6 / Step 21 — assign handoff to one operator user id (narrow)."""

    assigned_operator_id: int = Field(..., description="Existing users.id for the operator/admin actor.")


class AdminHandoffRead(BaseModel):
    """Admin queue visibility for one handoff row (read-only; Phase 6 / Step 18)."""

    id: int
    status: str
    reason: str
    priority: str
    created_at: datetime
    updated_at: datetime
    user_id: int
    order_id: int | None = None
    assigned_operator_id: int | None = None
    tour_id: int | None = Field(default=None, description="From linked order.tour when order exists.")
    tour_code: str | None = None
    tour_title_default: str | None = None
    is_open: bool = Field(description="True when status is open.")
    needs_attention: bool = Field(
        description="True when status is open or in_review (may need operator follow-up).",
    )
    age_bucket: str = Field(
        description="within_1h | within_24h | older — coarse age from created_at (server clock).",
    )
    is_group_followup: bool = Field(
        default=False,
        description="True when reason is group_followup_start (narrow Phase 7 group→private follow-up chain).",
    )
    source_label: str | None = Field(
        default=None,
        description="Human-readable origin label when is_group_followup; read-only.",
    )
    is_assigned_group_followup: bool = Field(
        default=False,
        description="True only for group_followup_start with assigned_operator_id set; read-only.",
    )
    group_followup_work_label: str | None = Field(
        default=None,
        description="Triage copy for group_followup_start only (assigned vs awaiting); None for other reasons.",
    )
    group_followup_resolution_label: str | None = Field(
        default=None,
        description="Read-only: set when group_followup_start is closed (resolved); None otherwise.",
    )
    group_followup_queue_state: GroupFollowupQueueState | None = Field(
        default=None,
        description="Phase 7 / Step 15: single queue bucket for group_followup_start only; None for other reasons.",
    )
    is_full_bus_sales_assistance: bool = Field(
        default=False,
        description="True when reason is structured full_bus_sales_assistance (Phase 7.1 / Step 5).",
    )
    full_bus_sales_assistance_label: str | None = Field(
        default=None,
        description="Operator-facing label for full-bus commercial assistance; None when not applicable.",
    )
    assistance_context_tour_code: str | None = Field(
        default=None,
        description="Tour code from full_bus_sales_assistance reason payload when present.",
    )


class AdminHandoffListRead(BaseModel):
    items: list[AdminHandoffRead]
    total_returned: int


class AdminOrderMovePlacementSnapshot(BaseModel):
    """Read-only: **current** persisted tour/boarding placement; no move-audit timeline (Phase 6 / Step 30)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["current_placement_only"] = Field(
        default="current_placement_only",
        description="Only safe mode without persisted prior placement rows.",
    )
    timeline_available: bool = Field(
        default=False,
        description="False until optional future audit slice stores move history.",
    )
    tour_id: int
    boarding_point_id: int
    tour_code: str
    tour_departure_datetime: datetime
    boarding_city: str
    order_updated_at: datetime
    note: str


class AdminOrderDetailRead(BaseModel):
    id: int
    user_id: int
    lifecycle_kind: AdminOrderLifecycleKind
    lifecycle_summary: str = Field(
        description="Primary admin-facing interpretation of order state (see OPEN_QUESTIONS_AND_TECH_DEBT).",
    )
    persistence_snapshot: AdminOrderPersistenceSnapshot
    tour: AdminTourSummary
    boarding_point: AdminBoardingPointSummary
    seats_count: int
    total_amount: Decimal
    currency: str
    source_channel: str | None
    assigned_operator_id: int | None
    reservation_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    payment_correction_hint: str | None = Field(
        default=None,
        description="Secondary, conservative hint when payment rows vs order.payment_status look inconsistent.",
    )
    needs_manual_review: bool = Field(
        default=False,
        description="True when heuristics suggest operator review (multiple entries or status mismatch).",
    )
    payment_records_count: int = Field(
        default=0,
        description="Total payment rows for this order (not capped by list preview).",
    )
    latest_payment_status: PaymentStatus | None = Field(
        default=None,
        description="Status on the newest payment row by created_at (if any).",
    )
    latest_payment_provider: str | None = Field(
        default=None,
        description="Provider on the newest payment row (if any).",
    )
    latest_payment_created_at: datetime | None = Field(
        default=None,
        description="created_at on the newest payment row (if any).",
    )
    has_multiple_payment_entries: bool = Field(
        default=False,
        description="True if more than one payment row exists.",
    )
    has_paid_entry: bool = Field(
        default=False,
        description="True if any payment row has status paid.",
    )
    has_awaiting_payment_entry: bool = Field(
        default=False,
        description="True if any payment row has status awaiting_payment.",
    )
    suggested_admin_action: str = Field(
        description=(
            "Secondary preview only: none | manual_review | handoff_follow_up | "
            "await_customer_payment. Not a permission or executed action."
        ),
    )
    allowed_admin_actions: list[str] = Field(
        default_factory=list,
        description="Read-only labels for conceivable follow-ups; not enforced capabilities.",
    )
    payment_action_preview: str | None = Field(
        default=None,
        description="One-line orientation for payment/order follow-up; does not perform work.",
    )
    payments: list[AdminPaymentSummaryItem] = Field(
        default_factory=list,
        description="Recent payment rows (newest first), capped for read-only visibility.",
    )
    handoffs: list[AdminHandoffSummaryItem] = Field(
        default_factory=list,
        description="Handoff rows linked to this order (newest activity first).",
    )
    can_consider_move: bool = Field(
        default=False,
        description=(
            "Read-only: conservative signal whether persisted state might suit a future "
            "move-to-tour/date feature; does not authorize or perform a move (Phase 6 / Step 28)."
        ),
    )
    move_blockers: list[str] = Field(
        default_factory=list,
        description="Stable machine-oriented blocker codes when can_consider_move is false.",
    )
    move_readiness_hint: str = Field(
        description="One-line human orientation for move readiness; not a capability or workflow.",
    )
    move_placement_snapshot: AdminOrderMovePlacementSnapshot = Field(
        description=(
            "Read-only current tour/boarding placement for post-move inspection; "
            "not a history timeline (Phase 6 / Step 30)."
        ),
    )


class AdminOrderMoveBody(BaseModel):
    """Body for `POST /admin/orders/{order_id}/move` — target tour plus boarding point on that tour."""

    model_config = ConfigDict(extra="forbid")

    target_tour_id: int = Field(ge=1, description="Tour row to move the order onto.")
    target_boarding_point_id: int = Field(ge=1, description="Boarding point belonging to `target_tour_id`.")


class AdminOverviewRead(BaseModel):
    app_env: str = Field(description="Configured APP_ENV for orientation (not a secret).")
    tours_total_approx: int
    orders_total_approx: int
    open_handoffs_count: int
    active_waitlist_entries_count: int


class AdminSupplierRead(BaseModel):
    """Central-admin visibility for Layer B suppliers (Track 2)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    display_name: str
    is_active: bool
    primary_telegram_user_id: int | None = None
    onboarding_status: SupplierOnboardingStatus
    onboarding_contact_info: str | None = None
    onboarding_region: str | None = None
    legal_entity_type: SupplierLegalEntityType | None = None
    legal_registered_name: str | None = None
    legal_registration_code: str | None = None
    permit_license_type: str | None = None
    permit_license_number: str | None = None
    onboarding_service_composition: SupplierServiceComposition | None = None
    onboarding_fleet_summary: str | None = None
    onboarding_rejection_reason: str | None = None
    onboarding_submitted_at: datetime | None = None
    onboarding_reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AdminSupplierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=255)
    credential_label: str | None = Field(default=None, max_length=128)

    @field_validator("code", "display_name", "credential_label")
    @classmethod
    def strip_ws(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s


class AdminSupplierCreatedRead(BaseModel):
    supplier: AdminSupplierRead
    api_token: str = Field(description="Returned once; store securely (hashed at rest in DB).")


class AdminSupplierListRead(BaseModel):
    items: list[AdminSupplierRead]
    total_returned: int


class AdminSupplierOnboardingReject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=4000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s
