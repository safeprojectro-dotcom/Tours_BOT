from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreatedAtSchema(ORMBaseSchema):
    created_at: datetime


class UpdatedAtSchema(ORMBaseSchema):
    updated_at: datetime


class TimestampSchema(CreatedAtSchema, UpdatedAtSchema):
    pass
