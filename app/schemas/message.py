from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import CreatedAtSchema


class MessageBase(BaseModel):
    user_id: int
    chat_type: str
    telegram_chat_id: int
    direction: str
    language_code: str | None = None
    intent: str | None = None
    text: str
    metadata_json: dict | None = None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    chat_type: str | None = None
    direction: str | None = None
    language_code: str | None = None
    intent: str | None = None
    text: str | None = None
    metadata_json: dict | None = None


class MessageRead(MessageBase, CreatedAtSchema):
    id: int
