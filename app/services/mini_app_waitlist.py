"""MVP waitlist join for Mini App — interest only, no auto-promotion."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.models.enums import TourStatus
from app.models.waitlist import WaitlistEntry
from app.repositories.waitlist import WaitlistRepository
from app.services.catalog import CatalogLookupService
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.waitlist_ops_actions import (
    WAITLIST_STATUS_ACTIVE,
    WAITLIST_STATUS_CLOSED,
    WAITLIST_STATUS_IN_REVIEW,
)


class MiniAppWaitlistOutcome(StrEnum):
    CREATED = "created"
    ALREADY_EXISTS = "already_exists"
    INVALID_TOUR = "invalid_tour"
    NOT_ELIGIBLE = "not_eligible"


class MiniAppWaitlistService:
    """Join waitlist when tour is open for sale but has no seats (sold out)."""

    ACTIVE_STATUS = "active"

    def __init__(
        self,
        *,
        catalog_lookup_service: CatalogLookupService | None = None,
        waitlist_repository: WaitlistRepository | None = None,
    ) -> None:
        self._catalog = catalog_lookup_service or CatalogLookupService()
        self._waitlist = waitlist_repository or WaitlistRepository()

    def _user_sync(self) -> TelegramUserContextService:
        settings = get_settings()
        return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)

    def _tour_waitlist_eligible(self, session: Session, *, tour_code: str) -> tuple[object | None, bool]:
        tour = self._catalog.get_tour_by_code(session, code=tour_code)
        if tour is None or tour.status != TourStatus.OPEN_FOR_SALE:
            return None, False
        if not tour_is_customer_catalog_visible(
            departure_datetime=tour.departure_datetime,
            sales_deadline=tour.sales_deadline,
        ):
            return None, False
        if tour.seats_available > 0:
            return tour, False
        return tour, True

    @staticmethod
    def _pick_user_waitlist_row(rows: list[WaitlistEntry]) -> WaitlistEntry | None:
        """Prefer active, then in_review, else most recent closed."""
        if not rows:
            return None
        for want in (WAITLIST_STATUS_ACTIVE, WAITLIST_STATUS_IN_REVIEW):
            for r in rows:
                if r.status == want:
                    return r
        closed_only = [r for r in rows if r.status == WAITLIST_STATUS_CLOSED]
        if not closed_only:
            return None
        return max(closed_only, key=lambda r: r.id)

    def get_status(
        self,
        session: Session,
        *,
        tour_code: str,
        telegram_user_id: int,
    ) -> tuple[bool, bool, str | None, int | None]:
        """
        Returns (eligible, on_waitlist, waitlist_status, waitlist_entry_id).

        eligible = sold-out open tour. on_waitlist = True when status is active or in_review
        (interest still tracked). waitlist_status surfaces active | in_review | closed for UI.
        """
        tour, eligible = self._tour_waitlist_eligible(session, tour_code=tour_code)
        if tour is None or not eligible:
            return False, False, None, None
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=None,
        )
        rows = self._waitlist.list_entries_for_user_tour(session, user_id=user.id, tour_id=tour.id)
        entry = self._pick_user_waitlist_row(rows)
        if entry is None:
            return True, False, None, None
        st = entry.status
        if st == WAITLIST_STATUS_ACTIVE:
            return True, True, st, entry.id
        if st == WAITLIST_STATUS_IN_REVIEW:
            return True, True, st, entry.id
        if st == WAITLIST_STATUS_CLOSED:
            return True, False, st, entry.id
        return True, False, None, None

    def join(
        self,
        session: Session,
        *,
        tour_code: str,
        telegram_user_id: int,
        seats_count: int = 1,
    ) -> tuple[MiniAppWaitlistOutcome, int | None]:
        tour, eligible = self._tour_waitlist_eligible(session, tour_code=tour_code)
        if tour is None:
            return MiniAppWaitlistOutcome.INVALID_TOUR, None
        if not eligible:
            return MiniAppWaitlistOutcome.NOT_ELIGIBLE, None

        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=None,
        )
        existing = self._waitlist.get_pending_entry(session, user_id=user.id, tour_id=tour.id)
        if existing is not None:
            return MiniAppWaitlistOutcome.ALREADY_EXISTS, existing.id

        seats = max(1, min(seats_count, 8))
        try:
            row = self._waitlist.create(
                session,
                data={
                    "user_id": user.id,
                    "tour_id": tour.id,
                    "seats_count": seats,
                    "status": self.ACTIVE_STATUS,
                },
            )
        except IntegrityError:
            session.rollback()
            existing = self._waitlist.get_pending_entry(session, user_id=user.id, tour_id=tour.id)
            if existing is not None:
                return MiniAppWaitlistOutcome.ALREADY_EXISTS, existing.id
            return MiniAppWaitlistOutcome.INVALID_TOUR, None

        return MiniAppWaitlistOutcome.CREATED, row.id
