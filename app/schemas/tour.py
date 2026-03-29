from __future__ import annotations

from datetime import datetime, time as time_value
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import TourStatus
from app.schemas.common import ORMBaseSchema, TimestampSchema


class TourTranslationBase(BaseModel):
    language_code: str
    title: str
    short_description: str | None = None
    full_description: str | None = None
    program_text: str | None = None
    included_text: str | None = None
    excluded_text: str | None = None


class TourTranslationCreate(TourTranslationBase):
    tour_id: int


class TourTranslationUpdate(BaseModel):
    language_code: str | None = None
    title: str | None = None
    short_description: str | None = None
    full_description: str | None = None
    program_text: str | None = None
    included_text: str | None = None
    excluded_text: str | None = None


class TourTranslationRead(TourTranslationBase, ORMBaseSchema):
    id: int
    tour_id: int


class BoardingPointBase(BaseModel):
    city: str
    address: str
    time: time_value
    notes: str | None = None


class BoardingPointCreate(BoardingPointBase):
    tour_id: int


class BoardingPointUpdate(BaseModel):
    city: str | None = None
    address: str | None = None
    time: time_value | None = None
    notes: str | None = None


class BoardingPointRead(BoardingPointBase, ORMBaseSchema):
    id: int
    tour_id: int


class TourBase(BaseModel):
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
    sales_deadline: datetime | None = None
    status: TourStatus = TourStatus.DRAFT
    guaranteed_flag: bool = False


class TourCreate(TourBase):
    pass


class TourUpdate(BaseModel):
    code: str | None = None
    title_default: str | None = None
    short_description_default: str | None = None
    full_description_default: str | None = None
    duration_days: int | None = None
    departure_datetime: datetime | None = None
    return_datetime: datetime | None = None
    base_price: Decimal | None = None
    currency: str | None = None
    seats_total: int | None = None
    seats_available: int | None = None
    sales_deadline: datetime | None = None
    status: TourStatus | None = None
    guaranteed_flag: bool | None = None


class TourRead(TourBase, TimestampSchema):
    id: int


class TourDetailRead(BaseModel):
    tour: TourRead
    translations: list[TourTranslationRead]
    boarding_points: list[BoardingPointRead]
