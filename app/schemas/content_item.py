from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import CreatedAtSchema


class ContentItemBase(BaseModel):
    tour_id: int
    channel_type: str
    language_code: str
    content_type: str
    title: str | None = None
    body: str | None = None
    media_path: str | None = None
    status: str = "draft"
    approved_by: int | None = None
    published_at: datetime | None = None


class ContentItemCreate(ContentItemBase):
    pass


class ContentItemUpdate(BaseModel):
    channel_type: str | None = None
    language_code: str | None = None
    content_type: str | None = None
    title: str | None = None
    body: str | None = None
    media_path: str | None = None
    status: str | None = None
    approved_by: int | None = None
    published_at: datetime | None = None


class ContentItemRead(ContentItemBase, CreatedAtSchema):
    id: int
