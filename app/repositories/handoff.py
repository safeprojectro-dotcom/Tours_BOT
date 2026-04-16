from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.handoff import Handoff
from app.models.order import Order
from app.repositories.base import SQLAlchemyRepository

_GROUP_FOLLOWUP_START_REASON = "group_followup_start"


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

    def list_open_for_ops_queue(self, session: Session, *, limit: int = 500) -> list[Handoff]:
        """Open handoffs, oldest first (FIFO-style triage). Eager-loads linked order and tour when present."""
        stmt = (
            select(Handoff)
            .where(Handoff.status == "open")
            .order_by(Handoff.created_at.asc(), Handoff.id.asc())
            .limit(limit)
            .options(selectinload(Handoff.order).selectinload(Order.tour))
        )
        return list(session.scalars(stmt).all())

    def find_open_by_user_reason(self, session: Session, *, user_id: int, reason: str) -> Handoff | None:
        stmt = (
            select(Handoff)
            .where(
                Handoff.user_id == user_id,
                Handoff.reason == reason,
                Handoff.status == "open",
            )
            .order_by(Handoff.created_at.desc(), Handoff.id.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    def find_latest_by_user_reason(self, session: Session, *, user_id: int, reason: str) -> Handoff | None:
        """Most recently updated row for this user+reason (any status)."""
        stmt = (
            select(Handoff)
            .where(Handoff.user_id == user_id, Handoff.reason == reason)
            .order_by(Handoff.updated_at.desc(), Handoff.id.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    def list_for_admin(
        self,
        session: Session,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        group_followup_queue: str | None = None,
    ) -> list[Handoff]:
        """Recent activity first; optional status filter. Loads order+tour for list summaries."""
        stmt = select(Handoff).options(selectinload(Handoff.order).selectinload(Order.tour))
        if status is not None:
            stmt = stmt.where(Handoff.status == status)
        if group_followup_queue is not None:
            stmt = stmt.where(Handoff.reason == _GROUP_FOLLOWUP_START_REASON)
            if group_followup_queue == "resolved":
                stmt = stmt.where(Handoff.status == "closed")
            elif group_followup_queue == "awaiting_assignment":
                stmt = stmt.where(Handoff.status == "open", Handoff.assigned_operator_id.is_(None))
            elif group_followup_queue == "assigned_open":
                stmt = stmt.where(Handoff.status == "open", Handoff.assigned_operator_id.is_not(None))
            elif group_followup_queue == "in_work":
                stmt = stmt.where(Handoff.status == "in_review")
        stmt = stmt.order_by(Handoff.updated_at.desc(), Handoff.id.desc()).offset(offset).limit(limit)
        return list(session.scalars(stmt).all())

    def get_by_id_for_admin_detail(self, session: Session, *, handoff_id: int) -> Handoff | None:
        stmt = (
            select(Handoff)
            .where(Handoff.id == handoff_id)
            .options(selectinload(Handoff.order).selectinload(Order.tour))
        )
        return session.scalars(stmt).first()
