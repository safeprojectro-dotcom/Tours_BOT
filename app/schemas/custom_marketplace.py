"""API schemas for Track 4 custom marketplace (RFQ)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
    SupplierCustomRequestResponseKind,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.schemas.effective_commercial_execution_policy import EffectiveCommercialExecutionPolicyRead
from app.services.effective_commercial_execution_policy import validate_supplier_declared_rfq_commercial_pair


class MiniAppCustomRequestCreate(BaseModel):
    """Mini App intake: same structured fields as bot path."""

    telegram_user_id: int = Field(gt=0)
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None = None
    route_notes: str = Field(min_length=3, max_length=8000)
    group_size: int | None = Field(default=None, ge=1, le=999)
    special_conditions: str | None = Field(default=None, max_length=8000)

    @field_validator("route_notes", "special_conditions")
    @classmethod
    def strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def date_range_ok(self) -> MiniAppCustomRequestCreate:
        end = self.travel_date_end or self.travel_date_start
        if end < self.travel_date_start:
            raise ValueError("travel_date_end must not be before travel_date_start.")
        return self


class BotCustomRequestCreate(BaseModel):
    """Internal: bot FSM hands off to service with resolved user_id."""

    user_id: int = Field(gt=0)
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None = None
    route_notes: str = Field(min_length=3, max_length=8000)
    group_size: int | None = Field(default=None, ge=1, le=999)
    special_conditions: str | None = Field(default=None, max_length=8000)
    source_channel: CustomMarketplaceRequestSource = CustomMarketplaceRequestSource.PRIVATE_BOT

    @field_validator("route_notes", "special_conditions")
    @classmethod
    def strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def date_range_ok(self) -> BotCustomRequestCreate:
        end = self.travel_date_end or self.travel_date_start
        if end < self.travel_date_start:
            raise ValueError("travel_date_end must not be before travel_date_start.")
        return self


class CustomMarketplaceRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None
    route_notes: str
    group_size: int | None
    special_conditions: str | None
    source_channel: CustomMarketplaceRequestSource
    status: CustomMarketplaceRequestStatus
    admin_intervention_note: str | None
    selected_supplier_response_id: int | None = None
    commercial_resolution_kind: CommercialResolutionKind | None = None
    created_at: datetime
    updated_at: datetime


class CustomMarketplaceRequestListRead(BaseModel):
    items: list[CustomMarketplaceRequestRead]
    total_returned: int


class SupplierCustomRequestResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    supplier_id: int
    supplier_code: str | None = None
    supplier_display_name: str | None = None
    response_kind: SupplierCustomRequestResponseKind
    supplier_message: str | None
    quoted_price: Decimal | None
    quoted_currency: str | None
    supplier_declared_sales_mode: TourSalesMode | None = None
    supplier_declared_payment_mode: SupplierOfferPaymentMode | None = None
    is_selected: bool = False
    created_at: datetime
    updated_at: datetime


class CustomRequestBookingBridgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    selected_supplier_response_id: int
    user_id: int
    tour_id: int | None
    bridge_status: CustomRequestBookingBridgeStatus
    admin_note: str | None
    created_at: datetime
    updated_at: datetime


class CustomMarketplaceRequestDetailRead(BaseModel):
    request: CustomMarketplaceRequestRead
    responses: list[SupplierCustomRequestResponseRead]
    customer_telegram_user_id: int | None = None
    booking_bridge: CustomRequestBookingBridgeRead | None = None
    effective_execution_policy: EffectiveCommercialExecutionPolicyRead | None = None


class AdminCustomRequestBookingBridgeCreate(BaseModel):
    """Track 5b.1: admin explicitly creates execution intent — no Layer A side effects."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int | None = Field(default=None, gt=0)
    admin_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminCustomRequestBookingBridgePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tour_id: int | None = Field(default=None, gt=0)
    admin_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def at_least_one(self) -> AdminCustomRequestBookingBridgePatch:
        if self.tour_id is None and self.admin_note is None:
            raise ValueError("Provide tour_id and/or admin_note.")
        return self


class AdminCustomRequestBookingBridgeClose(BaseModel):
    """Track 5e: close the active bridge only — no Layer A side effects."""

    model_config = ConfigDict(extra="forbid")

    terminal_status: Literal["superseded", "cancelled"]
    admin_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminCustomRequestBookingBridgeReplace(AdminCustomRequestBookingBridgeCreate):
    """Track 5e: supersede active bridge (if any) and create a new bridge row in one transaction."""

    supersede_note: str | None = Field(default=None, max_length=8000)

    @field_validator("supersede_note")
    @classmethod
    def strip_supersede_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class SupplierCustomRequestResponseUpsert(BaseModel):
    response_kind: SupplierCustomRequestResponseKind
    supplier_message: str | None = Field(default=None, max_length=8000)
    quoted_price: Decimal | None = Field(default=None, ge=0)
    quoted_currency: str | None = Field(default=None, max_length=8)
    supplier_declared_sales_mode: TourSalesMode | None = None
    supplier_declared_payment_mode: SupplierOfferPaymentMode | None = None

    @field_validator("supplier_message", "quoted_currency")
    @classmethod
    def strip_fields(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def proposed_rules(self) -> SupplierCustomRequestResponseUpsert:
        if self.response_kind == SupplierCustomRequestResponseKind.DECLINED:
            if self.supplier_declared_sales_mode is not None or self.supplier_declared_payment_mode is not None:
                raise ValueError("Declined responses must not set supplier_declared sales/payment fields.")
            return self
        if self.response_kind == SupplierCustomRequestResponseKind.PROPOSED:
            if not (self.supplier_message or "").strip():
                raise ValueError("supplier_message is required when response_kind is proposed.")
            if self.quoted_price is not None and not (self.quoted_currency or "").strip():
                raise ValueError("quoted_currency is required when quoted_price is set.")
            if self.supplier_declared_sales_mode is None or self.supplier_declared_payment_mode is None:
                raise ValueError(
                    "supplier_declared_sales_mode and supplier_declared_payment_mode are required when proposed.",
                )
            validate_supplier_declared_rfq_commercial_pair(
                sales_mode=self.supplier_declared_sales_mode,
                payment_mode=self.supplier_declared_payment_mode,
            )
        return self


class AdminCustomRequestPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    admin_intervention_note: str | None = Field(default=None, max_length=8000)
    status: CustomMarketplaceRequestStatus | None = None

    @field_validator("admin_intervention_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def at_least_one(self) -> AdminCustomRequestPatch:
        if self.admin_intervention_note is None and self.status is None:
            raise ValueError("Provide admin_intervention_note and/or status.")
        return self

    @model_validator(mode="after")
    def block_commercial_resolution_via_patch(self) -> AdminCustomRequestPatch:
        blocked = {
            CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
            CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
            CustomMarketplaceRequestStatus.FULFILLED,
        }
        if self.status is not None and self.status in blocked:
            raise ValueError("Use POST /admin/custom-requests/{id}/resolution for commercial resolution statuses.")
        return self


class AdminCustomRequestResolutionApply(BaseModel):
    """Track 5a: record commercial resolution without creating orders or payments."""

    model_config = ConfigDict(extra="forbid")

    status: CustomMarketplaceRequestStatus
    commercial_resolution_kind: CommercialResolutionKind | None = None
    selected_supplier_response_id: int | None = None
    admin_intervention_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_intervention_note")
    @classmethod
    def strip_resolution_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class MiniAppCustomRequestCustomerSummaryRead(BaseModel):
    id: int
    status: CustomMarketplaceRequestStatus
    customer_visible_summary: str


class MiniAppCustomRequestCustomerListRead(BaseModel):
    items: list[MiniAppCustomRequestCustomerSummaryRead]
    total_returned: int


class MiniAppCustomRequestCustomerDetailRead(BaseModel):
    id: int
    status: CustomMarketplaceRequestStatus
    customer_visible_summary: str
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None
    latest_booking_bridge_status: CustomRequestBookingBridgeStatus | None = None
    latest_booking_bridge_tour_code: str | None = None


class MiniAppCustomRequestCreatedRead(BaseModel):
    id: int
    status: CustomMarketplaceRequestStatus
