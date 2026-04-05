"""Read-only admin API response models."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind


class AdminTourListItem(BaseModel):
    id: int
    code: str
    title_default: str
    departure_datetime: datetime
    status: TourStatus
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
    status: TourStatus
    guaranteed_flag: bool = False

    @field_validator("code", "currency")
    @classmethod
    def strip_ws(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s


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


class AdminBoardingPointSummary(BaseModel):
    id: int
    city: str
    address: str
    time: time
    notes: str | None = None


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


class AdminHandoffSummaryItem(BaseModel):
    id: int
    status: str
    reason: str
    priority: str
    created_at: datetime
    updated_at: datetime


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
    payments: list[AdminPaymentSummaryItem] = Field(
        default_factory=list,
        description="Recent payment rows (newest first), capped for read-only visibility.",
    )
    handoffs: list[AdminHandoffSummaryItem] = Field(
        default_factory=list,
        description="Handoff rows linked to this order (newest activity first).",
    )


class AdminOverviewRead(BaseModel):
    app_env: str = Field(description="Configured APP_ENV for orientation (not a secret).")
    tours_total_approx: int
    orders_total_approx: int
    open_handoffs_count: int
    active_waitlist_entries_count: int
