from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class SQLAlchemyRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def get(self, session: Session, obj_id: Any) -> ModelT | None:
        return session.get(self.model, obj_id)

    def list(self, session: Session, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = self._base_select().offset(offset).limit(limit)
        return list(session.scalars(stmt).all())

    def create(self, session: Session, *, data: Mapping[str, Any]) -> ModelT:
        instance = self.model(**dict(data))
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance

    def update(self, session: Session, *, instance: ModelT, data: Mapping[str, Any]) -> ModelT:
        for field, value in data.items():
            setattr(instance, field, value)
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance

    def delete(self, session: Session, *, instance: ModelT) -> None:
        session.delete(instance)
        session.flush()

    def _base_select(self) -> Select[tuple[ModelT]]:
        return select(self.model).order_by(self.model.id)
