from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.waitlist import WaitlistEntry
from app.repositories.base import SQLAlchemyRepository


class WaitlistRepository(SQLAlchemyRepository[WaitlistEntry]):
    def __init__(self) -> None:
        super().__init__(WaitlistEntry)

    def list_by_user(self, session: Session, *, user_id: int) -> list[WaitlistEntry]:
        stmt = (
            select(WaitlistEntry)
            .where(WaitlistEntry.user_id == user_id)
            .order_by(WaitlistEntry.created_at.desc(), WaitlistEntry.id.desc())
        )
        return list(session.scalars(stmt).all())

    def list_by_tour(self, session: Session, *, tour_id: int) -> list[WaitlistEntry]:
        stmt = (
            select(WaitlistEntry)
            .where(WaitlistEntry.tour_id == tour_id)
            .order_by(WaitlistEntry.created_at, WaitlistEntry.id)
        )
        return list(session.scalars(stmt).all())

    def get_active_entry(
        self,
        session: Session,
        *,
        user_id: int,
        tour_id: int,
    ) -> WaitlistEntry | None:
        stmt = (
            select(WaitlistEntry)
            .where(
                WaitlistEntry.user_id == user_id,
                WaitlistEntry.tour_id == tour_id,
                WaitlistEntry.status == "active",
            )
            .limit(1)
        )
        return session.scalars(stmt).first()
