from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import TourStatus
from app.schemas.prepared import CatalogTourCardRead, LocalizedTourContentRead
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
