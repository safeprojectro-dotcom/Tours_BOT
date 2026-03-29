from __future__ import annotations

from app.schemas.common import TimestampSchema
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    preferred_language: str | None = None
    home_city: str | None = None
    source_channel: str | None = None


class UserCreate(UserBase):
    telegram_user_id: int


class UserUpdate(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    preferred_language: str | None = None
    home_city: str | None = None
    source_channel: str | None = None


class UserRead(UserBase, TimestampSchema):
    id: int
    telegram_user_id: int
