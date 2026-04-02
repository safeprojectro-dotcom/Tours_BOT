from __future__ import annotations

from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.schemas.prepared import OrderSummaryRead, PaymentEntryRead
from app.services.catalog import CatalogLookupService
from app.services.order_read import OrderReadService
from app.services.order_summary import OrderSummaryService
from app.services.payment_entry import PaymentEntryService
from app.services.reservation_creation import TemporaryReservationService
from app.services.reservation_expiry import lazy_expire_due_reservations

MINI_APP_SOURCE_CHANNEL = "mini_app"


class MiniAppBookingService:
    """Adapts existing reservation and payment-entry services for Mini App HTTP entry (no auth yet)."""

    def __init__(
        self,
        *,
        catalog_lookup_service: CatalogLookupService | None = None,
        reservation_service: TemporaryReservationService | None = None,
        order_summary_service: OrderSummaryService | None = None,
        order_read_service: OrderReadService | None = None,
        payment_entry_service: PaymentEntryService | None = None,
    ) -> None:
        self.catalog_lookup_service = catalog_lookup_service or CatalogLookupService()
        self.reservation_service = reservation_service or TemporaryReservationService()
        self.order_summary_service = order_summary_service or OrderSummaryService()
        self.order_read_service = order_read_service or OrderReadService()
        self.payment_entry_service = payment_entry_service or PaymentEntryService()

    def _user_sync(self) -> TelegramUserContextService:
        settings = get_settings()
        return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)

    def create_temporary_reservation(
        self,
        session: Session,
        *,
        tour_code: str,
        telegram_user_id: int,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead | None:
        lazy_expire_due_reservations(session)
        tour = self.catalog_lookup_service.get_tour_by_code(session, code=tour_code)
        if tour is None:
            return None

        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=language_code,
        )

        order = self.reservation_service.create_temporary_reservation(
            session,
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=boarding_point_id,
            seats_count=seats_count,
            source_channel=MINI_APP_SOURCE_CHANNEL,
        )
        if order is None:
            return None

        return self.order_summary_service.get_order_summary(
            session,
            order_id=order.id,
            language_code=language_code,
        )

    def start_payment_entry(
        self,
        session: Session,
        *,
        order_id: int,
        telegram_user_id: int,
    ) -> PaymentEntryRead | None:
        lazy_expire_due_reservations(session)
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=None,
        )
        entry = self.payment_entry_service.start_payment_entry(
            session,
            order_id=order_id,
            user_id=user.id,
        )
        if entry is None:
            return None
        return entry

    def get_reservation_overview_for_user(
        self,
        session: Session,
        *,
        order_id: int,
        telegram_user_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead | None:
        """Read-only overview for Mini App reservation-success screen; ownership and state from persisted order."""
        lazy_expire_due_reservations(session)
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=language_code,
        )
        order = self.order_read_service.get_order(session, order_id=order_id)
        if order is None or order.user_id != user.id:
            return None
        if order.booking_status != BookingStatus.RESERVED:
            return None
        if order.payment_status != PaymentStatus.AWAITING_PAYMENT:
            return None
        if order.cancellation_status != CancellationStatus.ACTIVE:
            return None

        return self.order_summary_service.get_order_summary(
            session,
            order_id=order_id,
            language_code=language_code,
        )
