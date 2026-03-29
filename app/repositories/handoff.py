from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.handoff import Handoff
from app.repositories.base import SQLAlchemyRepository


class HandoffRepository(SQLAlchemyRepository[Handoff]):
    def __init__(self) -> None:
        super().__init__(Handoff)

    def list_by_user(self, session: Session, *, user_id: int) -> list[Handoff]:
        stmt = (
            select(Handoff)
            .where(Handoff.user_id == user_id)
            .order_by(Handoff.created_at.desc(), Handoff.id.desc())
        )
        return list(session.scalars(stmt).all())

    def list_by_assigned_operator(self, session: Session, *, operator_id: int) -> list[Handoff]:
        stmt = (
            select(Handoff)
            .where(Handoff.assigned_operator_id == operator_id)
            .order_by(Handoff.created_at.desc(), Handoff.id.desc())
        )
        return list(session.scalars(stmt).all())

    def list_by_status(self, session: Session, *, status: str) -> list[Handoff]:
        stmt = (
            select(Handoff)
            .where(Handoff.status == status)
            .order_by(Handoff.created_at.desc(), Handoff.id.desc())
        )
        return list(session.scalars(stmt).all())
