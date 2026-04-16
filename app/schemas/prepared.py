from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import BookingStatus, PaymentStatus, TourStatus
from app.schemas.order import OrderRead
from app.schemas.payment import PaymentRead
from app.schemas.tour import BoardingPointRead, TourRead
from app.schemas.tour_sales_mode_policy import TourSalesModePolicyRead


class LocalizedTourContentRead(BaseModel):
    requested_language: str | None = None
    resolved_language: str | None = None
    used_fallback: bool = False
    title: str
    short_description: str | None = None
    full_description: str | None = None
    program_text: str | None = None
    included_text: str | None = None
    excluded_text: str | None = None


class CatalogTourCardRead(BaseModel):
    id: int
    code: str
    title: str
    short_description: str | None = None
    departure_datetime: datetime
    return_datetime: datetime
    duration_days: int
    base_price: Decimal
    currency: str
    seats_total: int
    seats_available: int
    status: TourStatus
    guaranteed_flag: bool
    is_available: bool
    localized_content: LocalizedTourContentRead
    sales_mode_policy: TourSalesModePolicyRead


class CatalogBrowseFiltersRead(BaseModel):
    departure_from: datetime | None = None
    departure_to: datetime | None = None
    destination_query: str | None = None
    max_price: Decimal | None = None


class PreparedTourDetailRead(BaseModel):
    tour: TourRead
    localized_content: LocalizedTourContentRead
    boarding_points: list[BoardingPointRead]
    sales_mode_policy: TourSalesModePolicyRead


class ReservationPreparationTourRead(BaseModel):
    id: int
    code: str
    departure_datetime: datetime
    return_datetime: datetime
    base_price: Decimal
    currency: str
    seats_available_snapshot: int
    localized_content: LocalizedTourContentRead


class ReservationPreparationSummaryRead(BaseModel):
    tour: ReservationPreparationTourRead
    seats_count: int
    boarding_point: BoardingPointRead
    estimated_total_amount: Decimal
    preparation_only: bool = True


class OrderTourSummaryRead(BaseModel):
    id: int
    code: str
    departure_datetime: datetime
    return_datetime: datetime
    localized_content: LocalizedTourContentRead


class OrderBoardingPointSummaryRead(BaseModel):
    id: int
    city: str
    address: str
    time: time
    notes: str | None = None


class OrderSummaryRead(BaseModel):
    order: OrderRead
    booking_status: BookingStatus
    payment_status: PaymentStatus
    tour: OrderTourSummaryRead
    boarding_point: OrderBoardingPointSummaryRead | None = None


class PaymentSummaryRead(BaseModel):
    order: OrderRead
    payments: list[PaymentRead]
    latest_payment: PaymentRead | None = None


class PaymentEntryRead(BaseModel):
    order: OrderRead
    payment: PaymentRead
    payment_session_reference: str
    payment_url: str | None = None
    reused_existing_payment: bool = False
