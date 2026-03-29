from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class HandoffBase(BaseModel):
    user_id: int
    order_id: int | None = None
    reason: str
    priority: str = "normal"
    status: str = "open"
    assigned_operator_id: int | None = None


class HandoffCreate(HandoffBase):
    pass


class HandoffUpdate(BaseModel):
    order_id: int | None = None
    reason: str | None = None
    priority: str | None = None
    status: str | None = None
    assigned_operator_id: int | None = None


class HandoffRead(HandoffBase, TimestampSchema):
    id: int
