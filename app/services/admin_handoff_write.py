"""Narrow admin mutations on handoffs (Phase 6 / Step 19) — no notifications, no order/payment changes."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.handoff import Handoff
from app.repositories.handoff import HandoffRepository
from app.services.handoff_ops_actions import (
    HANDOFF_STATUS_CLOSED,
    HANDOFF_STATUS_IN_REVIEW,
    HANDOFF_STATUS_OPEN,
)


class AdminHandoffNotFoundError(Exception):
    """No handoff row for the given id."""


class AdminHandoffMarkInReviewStateError(Exception):
    """mark-in-review not allowed from current status."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class AdminHandoffWriteService:
    """Minimal status transitions for `/admin/handoffs/*`; does not assign operators."""

    def __init__(self, *, handoff_repository: HandoffRepository | None = None) -> None:
        self._handoffs = handoff_repository or HandoffRepository()

    def mark_in_review(self, session: Session, *, handoff_id: int) -> Handoff:
        """
        open -> in_review; already in_review -> idempotent (no write).
        closed -> error. Other statuses -> error (narrow slice).
        """
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise AdminHandoffNotFoundError
        if row.status == HANDOFF_STATUS_CLOSED:
            raise AdminHandoffMarkInReviewStateError(current_status=row.status)
        if row.status == HANDOFF_STATUS_IN_REVIEW:
            return row
        if row.status == HANDOFF_STATUS_OPEN:
            return self._handoffs.update(session, instance=row, data={"status": HANDOFF_STATUS_IN_REVIEW})
        raise AdminHandoffMarkInReviewStateError(current_status=row.status)
