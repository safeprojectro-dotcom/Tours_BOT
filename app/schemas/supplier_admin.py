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


class SupplierOfferCreate(BaseModel):
    supplier_reference: str | None = Field(default=None, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=0)
    program_text: str | None = None
    departure_datetime: datetime
    return_datetime: datetime
    transport_notes: str | None = None
    vehicle_label: str | None = Field(default=None, max_length=128)
    seats_total: int = Field(default=0, ge=0)
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    service_composition: SupplierServiceComposition = SupplierServiceComposition.TRANSPORT_ONLY
    sales_mode: TourSalesMode = TourSalesMode.PER_SEAT
    payment_mode: SupplierOfferPaymentMode = SupplierOfferPaymentMode.PLATFORM_CHECKOUT

    @field_validator("supplier_reference", "currency", "vehicle_label")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
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
    seats_total: int | None = Field(default=None, ge=0)
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    service_composition: SupplierServiceComposition | None = None
    sales_mode: TourSalesMode | None = None
    payment_mode: SupplierOfferPaymentMode | None = None
    lifecycle_status: SupplierOfferLifecycle | None = None

    @field_validator("supplier_reference", "currency", "vehicle_label")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
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
