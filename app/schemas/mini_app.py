from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import TourStatus
from app.schemas.prepared import CatalogTourCardRead, LocalizedTourContentRead, ReservationPreparationTourRead
from app.schemas.tour import BoardingPointRead, TourRead


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
