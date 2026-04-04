"""Internal ops actions on handoffs (claim / close) — no booking or notification side effects."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.handoff import Handoff
from app.models.user import User
from app.repositories.handoff import HandoffRepository

# String statuses (column has no DB enum; values are project conventions).
HANDOFF_STATUS_OPEN = "open"
HANDOFF_STATUS_IN_REVIEW = "in_review"
HANDOFF_STATUS_CLOSED = "closed"


class HandoffNotFoundError(Exception):
    """No handoff row for the given id."""


class HandoffInvalidOperatorError(Exception):
    """operator_id does not reference an existing user."""


class HandoffClaimStateError(Exception):
    """Claim allowed only when status is open."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class HandoffCloseStateError(Exception):
    """Close not allowed (e.g. already closed)."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class HandoffOpsActionService:
    """Minimal claim/close loop for internal tooling."""

    def __init__(self, *, handoff_repository: HandoffRepository | None = None) -> None:
        self._handoffs = handoff_repository or HandoffRepository()

    def _ensure_operator(self, session: Session, operator_id: int | None) -> None:
        if operator_id is None:
            return
        if session.get(User, operator_id) is None:
            raise HandoffInvalidOperatorError

    def claim(
        self,
        session: Session,
        *,
        handoff_id: int,
        operator_id: int | None = None,
    ) -> Handoff:
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise HandoffNotFoundError
        if row.status != HANDOFF_STATUS_OPEN:
            raise HandoffClaimStateError(current_status=row.status)
        self._ensure_operator(session, operator_id)
        data: dict[str, object] = {"status": HANDOFF_STATUS_IN_REVIEW}
        if operator_id is not None:
            data["assigned_operator_id"] = operator_id
        return self._handoffs.update(session, instance=row, data=data)

    def close(
        self,
        session: Session,
        *,
        handoff_id: int,
        operator_id: int | None = None,
    ) -> Handoff:
        row = self._handoffs.get(session, handoff_id)
        if row is None:
            raise HandoffNotFoundError
        if row.status == HANDOFF_STATUS_CLOSED:
            raise HandoffCloseStateError(current_status=row.status)
        self._ensure_operator(session, operator_id)
        data: dict[str, object] = {"status": HANDOFF_STATUS_CLOSED}
        if operator_id is not None:
            data["assigned_operator_id"] = operator_id
        return self._handoffs.update(session, instance=row, data=data)
