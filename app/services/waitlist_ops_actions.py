"""Internal ops actions on waitlist entries (claim / close) — no booking or promotion."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.waitlist import WaitlistEntry
from app.repositories.waitlist import WaitlistRepository

WAITLIST_STATUS_ACTIVE = "active"
WAITLIST_STATUS_IN_REVIEW = "in_review"
WAITLIST_STATUS_CLOSED = "closed"


class WaitlistEntryNotFoundError(Exception):
    """No waitlist row for the given id."""


class WaitlistClaimStateError(Exception):
    """Claim only when status is active."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class WaitlistCloseStateError(Exception):
    """Close not allowed (e.g. already closed)."""

    def __init__(self, *, current_status: str) -> None:
        self.current_status = current_status


class WaitlistOpsActionService:
    """Minimal claim/close; waitlist has no operator assignment column — status only."""

    def __init__(self, *, waitlist_repository: WaitlistRepository | None = None) -> None:
        self._waitlist = waitlist_repository or WaitlistRepository()

    def claim(self, session: Session, *, waitlist_entry_id: int) -> WaitlistEntry:
        row = self._waitlist.get(session, waitlist_entry_id)
        if row is None:
            raise WaitlistEntryNotFoundError
        if row.status != WAITLIST_STATUS_ACTIVE:
            raise WaitlistClaimStateError(current_status=row.status)
        return self._waitlist.update(session, instance=row, data={"status": WAITLIST_STATUS_IN_REVIEW})

    def close(self, session: Session, *, waitlist_entry_id: int) -> WaitlistEntry:
        row = self._waitlist.get(session, waitlist_entry_id)
        if row is None:
            raise WaitlistEntryNotFoundError
        if row.status == WAITLIST_STATUS_CLOSED:
            raise WaitlistCloseStateError(current_status=row.status)
        if row.status not in (WAITLIST_STATUS_ACTIVE, WAITLIST_STATUS_IN_REVIEW):
            raise WaitlistCloseStateError(current_status=row.status)
        return self._waitlist.update(session, instance=row, data={"status": WAITLIST_STATUS_CLOSED})
