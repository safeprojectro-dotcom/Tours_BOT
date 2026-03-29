from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import UpdatedAtSchema


class KnowledgeBaseEntryBase(BaseModel):
    category: str
    language_code: str
    title: str
    content: str
    is_active: bool = True


class KnowledgeBaseEntryCreate(KnowledgeBaseEntryBase):
    pass


class KnowledgeBaseEntryUpdate(BaseModel):
    category: str | None = None
    language_code: str | None = None
    title: str | None = None
    content: str | None = None
    is_active: bool | None = None


class KnowledgeBaseEntryRead(KnowledgeBaseEntryBase, UpdatedAtSchema):
    id: int
