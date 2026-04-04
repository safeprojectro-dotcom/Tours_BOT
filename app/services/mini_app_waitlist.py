"""MVP waitlist join for Mini App — interest only, no auto-promotion."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.models.enums import TourStatus
from app.repositories.waitlist import WaitlistRepository
from app.services.catalog import CatalogLookupService


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
        if tour.seats_available > 0:
            return tour, False
        return tour, True

    def get_status(
        self,
        session: Session,
        *,
        tour_code: str,
        telegram_user_id: int,
    ) -> tuple[bool, bool]:
        """
        Returns (eligible_for_waitlist, on_waitlist).
        eligible = sold-out open tour; on_waitlist = user has an active entry.
        """
        tour, eligible = self._tour_waitlist_eligible(session, tour_code=tour_code)
        if tour is None or not eligible:
            return False, False
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=None,
        )
        existing = self._waitlist.get_active_entry(session, user_id=user.id, tour_id=tour.id)
        return True, existing is not None

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
        existing = self._waitlist.get_active_entry(session, user_id=user.id, tour_id=tour.id)
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
            existing = self._waitlist.get_active_entry(session, user_id=user.id, tour_id=tour.id)
            if existing is not None:
                return MiniAppWaitlistOutcome.ALREADY_EXISTS, existing.id
            return MiniAppWaitlistOutcome.INVALID_TOUR, None

        return MiniAppWaitlistOutcome.CREATED, row.id
