"""Narrow admin mutations on handoffs (Phase 6 / Steps 19–22) — no notifications, no order/payment changes."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.handoff import Handoff
from app.models.user import User
from app.repositories.handoff import HandoffRepository
from app.services.handoff_entry import HandoffEntryService
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


class AdminHandoffCloseStateError(Exception):
    """close not allowed from current status (narrow Step 20: only from in_review)."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class AdminHandoffAssignStateError(Exception):
    """assign not allowed from current status (narrow Step 21: non-closed only)."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class AdminHandoffInvalidOperatorError(Exception):
    """assigned_operator_id does not reference an existing user."""


class AdminHandoffReassignNotAllowedError(Exception):
    """Narrow rule: cannot change operator once assigned; idempotent only for same id."""

    def __init__(self, *, current_assigned_operator_id: int, requested_operator_id: int) -> None:
        self.current_assigned_operator_id = current_assigned_operator_id
        self.requested_operator_id = requested_operator_id


class AdminHandoffAssignGroupFollowupReasonOnlyError(Exception):
    """Phase 7 / Step 10 — assign-operator path accepts ``group_followup_start`` only."""

    def __init__(self, *, current_reason: str) -> None:
        self.current_reason = current_reason


class AdminHandoffReopenStateError(Exception):
    """reopen not allowed from current status (narrow Step 22: not from in_review)."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class AdminHandoffWriteService:
    """Minimal status transitions + narrow assignment + reopen for `/admin/handoffs/*`."""

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

    def close_handoff(self, session: Session, *, handoff_id: int) -> Handoff:
        """
        Step 20 narrow rule: in_review -> closed; already closed -> idempotent (no write).
        open -> error (use mark-in-review first). Complements Step 19 without a broad state machine.
        """
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise AdminHandoffNotFoundError
        if row.status == HANDOFF_STATUS_CLOSED:
            return row
        if row.status == HANDOFF_STATUS_IN_REVIEW:
            return self._handoffs.update(session, instance=row, data={"status": HANDOFF_STATUS_CLOSED})
        if row.status == HANDOFF_STATUS_OPEN:
            raise AdminHandoffCloseStateError(current_status=row.status)
        raise AdminHandoffCloseStateError(current_status=row.status)

    def _apply_operator_assignment(
        self,
        session: Session,
        *,
        row: Handoff,
        assigned_operator_id: int,
    ) -> Handoff:
        """Shared Step 21 rules: open/in_review, operator exists, no reassign to different id."""
        if row.status == HANDOFF_STATUS_CLOSED:
            raise AdminHandoffAssignStateError(current_status=row.status)
        if row.status not in (HANDOFF_STATUS_OPEN, HANDOFF_STATUS_IN_REVIEW):
            raise AdminHandoffAssignStateError(current_status=row.status)
        if session.get(User, assigned_operator_id) is None:
            raise AdminHandoffInvalidOperatorError
        current = row.assigned_operator_id
        if current is not None and current != assigned_operator_id:
            raise AdminHandoffReassignNotAllowedError(
                current_assigned_operator_id=current,
                requested_operator_id=assigned_operator_id,
            )
        if current == assigned_operator_id:
            return row
        return self._handoffs.update(
            session,
            instance=row,
            data={"assigned_operator_id": assigned_operator_id},
        )

    def assign_handoff(
        self,
        session: Session,
        *,
        handoff_id: int,
        assigned_operator_id: int,
    ) -> Handoff:
        """
        Step 21: set assigned_operator_id on non-closed handoffs only.
        open / in_review only; closed -> error.
        Operator user must exist. First assignment (None -> id) or idempotent same id OK.
        If already assigned to a different operator -> error (no broad reassign / unassign in this slice).
        """
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise AdminHandoffNotFoundError
        return self._apply_operator_assignment(
            session,
            row=row,
            assigned_operator_id=assigned_operator_id,
        )

    def assign_group_followup_operator(
        self,
        session: Session,
        *,
        handoff_id: int,
        assigned_operator_id: int,
    ) -> Handoff:
        """
        Phase 7 / Step 10 — same assignment rules as ``assign_handoff``, but only when
        ``reason == group_followup_start`` (narrow path; no notifications / workflow).
        """
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise AdminHandoffNotFoundError
        if row.reason != HandoffEntryService.REASON_GROUP_FOLLOWUP_START:
            raise AdminHandoffAssignGroupFollowupReasonOnlyError(current_reason=row.reason)
        return self._apply_operator_assignment(
            session,
            row=row,
            assigned_operator_id=assigned_operator_id,
        )

    def reopen_handoff(self, session: Session, *, handoff_id: int) -> Handoff:
        """
        Step 22 narrow rule: closed -> open. Already open -> idempotent (no write).
        in_review -> error (close first or use other flows; no broad workflow here).
        Only ``status`` is updated; ``assigned_operator_id`` is left unchanged (preserved).
        """
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise AdminHandoffNotFoundError
        if row.status == HANDOFF_STATUS_OPEN:
            return row
        if row.status == HANDOFF_STATUS_CLOSED:
            return self._handoffs.update(session, instance=row, data={"status": HANDOFF_STATUS_OPEN})
        if row.status == HANDOFF_STATUS_IN_REVIEW:
            raise AdminHandoffReopenStateError(current_status=row.status)
        raise AdminHandoffReopenStateError(current_status=row.status)
