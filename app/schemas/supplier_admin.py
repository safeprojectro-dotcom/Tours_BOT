"""Supplier-admin API request/response models (Layer B)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

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
