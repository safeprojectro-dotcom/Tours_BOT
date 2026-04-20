"""Supplier-admin API request/response models (Layer B)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    SupplierOfferLifecycle,
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


class SupplierOfferListRead(BaseModel):
    items: list[SupplierOfferRead]
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
    offer: SupplierOfferRead
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

    @field_validator("supplier_reference", "currency", "vehicle_label", "showcase_photo_url")
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

    @field_validator("supplier_reference", "currency", "vehicle_label", "showcase_photo_url")
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
