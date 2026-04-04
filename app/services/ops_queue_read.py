"""Thin read layer for ops: open handoffs and active waitlist (no mutations)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.handoff import Handoff
from app.models.waitlist import WaitlistEntry
from app.repositories.handoff import HandoffRepository
from app.repositories.waitlist import WaitlistRepository
from app.schemas.ops_queue import (
    OpsHandoffQueueItem,
    OpsHandoffQueueRead,
    OpsWaitlistQueueItem,
    OpsWaitlistQueueRead,
)


class OpsQueueReadService:
    """Read-only queues for internal tooling; does not change booking or waitlist rules."""

    def __init__(
        self,
        *,
        handoff_repository: HandoffRepository | None = None,
        waitlist_repository: WaitlistRepository | None = None,
    ) -> None:
        self._handoffs = handoff_repository or HandoffRepository()
        self._waitlist = waitlist_repository or WaitlistRepository()

    def open_handoffs(self, session: Session, *, limit: int = 500) -> OpsHandoffQueueRead:
        rows = self._handoffs.list_open_for_ops_queue(session, limit=limit)
        items = [_handoff_row_to_item(h) for h in rows]
        return OpsHandoffQueueRead(items=items)

    def active_waitlist(self, session: Session, *, limit: int = 500) -> OpsWaitlistQueueRead:
        rows = self._waitlist.list_active_for_ops_queue(session, limit=limit)
        items = [_waitlist_row_to_item(w) for w in rows]
        return OpsWaitlistQueueRead(items=items)


def _handoff_row_to_item(h: Handoff) -> OpsHandoffQueueItem:
    tour_id = tour_code = title = None
    if h.order_id is not None and h.order is not None and h.order.tour is not None:
        t = h.order.tour
        tour_id = t.id
        tour_code = t.code
        title = t.title_default
    return OpsHandoffQueueItem(
        id=h.id,
        created_at=h.created_at,
        updated_at=h.updated_at,
        status=h.status,
        priority=h.priority,
        reason=h.reason,
        user_id=h.user_id,
        order_id=h.order_id,
        assigned_operator_id=h.assigned_operator_id,
        order_tour_id=tour_id,
        order_tour_code=tour_code,
        order_tour_title_default=title,
    )


def _waitlist_row_to_item(w: WaitlistEntry) -> OpsWaitlistQueueItem:
    code = title = None
    if w.tour is not None:
        code = w.tour.code
        title = w.tour.title_default
    return OpsWaitlistQueueItem(
        id=w.id,
        created_at=w.created_at,
        status=w.status,
        user_id=w.user_id,
        tour_id=w.tour_id,
        seats_count=w.seats_count,
        tour_code=code,
        tour_title_default=title,
    )
