from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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

    def list_entries_for_user_tour(
        self,
        session: Session,
        *,
        user_id: int,
        tour_id: int,
    ) -> list[WaitlistEntry]:
        """Rows for this user+tour with status in active / in_review / closed (excludes legacy e.g. cancelled)."""
        stmt = (
            select(WaitlistEntry)
            .where(
                WaitlistEntry.user_id == user_id,
                WaitlistEntry.tour_id == tour_id,
                WaitlistEntry.status.in_(("active", "in_review", "closed")),
            )
            .order_by(WaitlistEntry.id.desc())
        )
        return list(session.scalars(stmt).all())

    def get_pending_entry(
        self,
        session: Session,
        *,
        user_id: int,
        tour_id: int,
    ) -> WaitlistEntry | None:
        """Active or in_review row — user should not create a duplicate join while ops is handling."""
        stmt = (
            select(WaitlistEntry)
            .where(
                WaitlistEntry.user_id == user_id,
                WaitlistEntry.tour_id == tour_id,
                WaitlistEntry.status.in_(("active", "in_review")),
            )
            .limit(1)
        )
        return session.scalars(stmt).first()

    def list_active_for_ops_queue(self, session: Session, *, limit: int = 500) -> list[WaitlistEntry]:
        """Active waitlist rows only, oldest first (longest-waiting first). Eager-loads tour for labels."""
        stmt = (
            select(WaitlistEntry)
            .where(WaitlistEntry.status == "active")
            .order_by(WaitlistEntry.created_at.asc(), WaitlistEntry.id.asc())
            .limit(limit)
            .options(selectinload(WaitlistEntry.tour))
        )
        return list(session.scalars(stmt).all())
