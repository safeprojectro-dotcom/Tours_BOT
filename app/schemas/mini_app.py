from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.enums import TourStatus
from app.schemas.prepared import CatalogTourCardRead, LocalizedTourContentRead, OrderSummaryRead, ReservationPreparationTourRead
from app.schemas.tour import BoardingPointRead, TourRead


class MiniAppBookingFacadeState(StrEnum):
    ACTIVE_TEMPORARY_RESERVATION = "active_temporary_reservation"
    EXPIRED_TEMPORARY_RESERVATION = "expired_temporary_reservation"
    CANCELLED_NO_PAYMENT = "cancelled_no_payment"
    CONFIRMED = "confirmed"
    IN_TRIP_PIPELINE = "in_trip_pipeline"
    OTHER = "other"


class MiniAppBookingPrimaryCta(StrEnum):
    PAY_NOW = "pay_now"
    BROWSE_TOURS = "browse_tours"
    BACK_TO_BOOKINGS = "back_to_bookings"


class MiniAppBookingListItemRead(BaseModel):
    summary: OrderSummaryRead
    user_visible_booking_label: str
    user_visible_payment_label: str
    facade_state: MiniAppBookingFacadeState
    primary_cta: MiniAppBookingPrimaryCta


class MiniAppBookingsListRead(BaseModel):
    items: list[MiniAppBookingListItemRead]


class MiniAppBookingDetailRead(BaseModel):
    summary: OrderSummaryRead
    user_visible_booking_label: str
    user_visible_payment_label: str
    facade_state: MiniAppBookingFacadeState
    primary_cta: MiniAppBookingPrimaryCta
    payment_session_hint: str | None = None


class MiniAppCatalogFiltersRead(BaseModel):
    departure_date_from: date | None = None
    departure_date_to: date | None = None
    destination_query: str | None = None
    max_price: Decimal | None = None


class MiniAppCatalogRead(BaseModel):
    items: list[CatalogTourCardRead]
    applied_filters: MiniAppCatalogFiltersRead
    limit: int
    offset: int
    status_scope: list[TourStatus]


class MiniAppTourDetailRead(BaseModel):
    tour: TourRead
    localized_content: LocalizedTourContentRead
    boarding_points: list[BoardingPointRead]
    is_available: bool


class MiniAppReservationPreparationRead(BaseModel):
    tour: ReservationPreparationTourRead
    boarding_points: list[BoardingPointRead]
    seat_count_options: list[int]
    preparation_only: bool = True


class MiniAppCreateReservationRequest(BaseModel):
    """Body for Mini App temporary reservation until Telegram init-data auth exists."""

    telegram_user_id: int = Field(gt=0)
    seats_count: int = Field(ge=1)
    boarding_point_id: int = Field(ge=1)


class MiniAppPaymentEntryRequest(BaseModel):
    telegram_user_id: int = Field(gt=0)


class MiniAppHelpCategoryRead(BaseModel):
    title: str
    bullets: list[str]


class MiniAppHelpRead(BaseModel):
    """Static, honest help copy for Mini App (no live handoff)."""

    title: str
    intro: str
    categories: list[MiniAppHelpCategoryRead]
    operator_notice: str
    when_to_contact_support: str


class MiniAppSettingsRead(BaseModel):
    supported_languages: list[str]
    mini_app_default_language: str
    active_language: str | None = Field(
        default=None,
        description="User profile language when known and supported; otherwise None.",
    )
    resolved_language: str = Field(
        description="Language the Mini App UI should use (active if set, else default, else first supported).",
    )
    mock_payment_completion_enabled: bool = Field(
        default=False,
        description="When True, Mini App may call mock-payment-complete for mockpay (staging/local).",
    )


class MiniAppLanguagePreferenceRequest(BaseModel):
    telegram_user_id: int = Field(gt=0)
    language_code: str = Field(min_length=2, max_length=16)


class MiniAppLanguagePreferenceResponse(BaseModel):
    language_code: str
