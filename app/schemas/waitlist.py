from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import CreatedAtSchema


class WaitlistEntryBase(BaseModel):
    user_id: int
    tour_id: int
    seats_count: int
    status: str = "active"


class WaitlistEntryCreate(WaitlistEntryBase):
    pass


class WaitlistEntryUpdate(BaseModel):
    seats_count: int | None = None
    status: str | None = None


class WaitlistEntryRead(WaitlistEntryBase, CreatedAtSchema):
    id: int
