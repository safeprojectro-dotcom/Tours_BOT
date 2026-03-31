from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingListItemRead,
    MiniAppBookingsListRead,
)
from app.services.mini_app_booking_facade import resolve_mini_app_booking_facade
from app.services.order_read import OrderReadService
from app.services.order_summary import OrderSummaryService
from app.services.payment_summary import PaymentSummaryService


class MiniAppBookingsService:
    """Read-only Mini App bookings list and detail with user-facing state translation."""

    def __init__(
        self,
        *,
        order_read_service: OrderReadService | None = None,
        order_summary_service: OrderSummaryService | None = None,
        payment_summary_service: PaymentSummaryService | None = None,
    ) -> None:
        self.order_read_service = order_read_service or OrderReadService()
        self.order_summary_service = order_summary_service or OrderSummaryService()
        self.payment_summary_service = payment_summary_service or PaymentSummaryService()

    def _user_sync(self) -> TelegramUserContextService:
        settings = get_settings()
        return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)

    def list_bookings(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        language_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
        now: datetime | None = None,
    ) -> MiniAppBookingsListRead:
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=language_code,
        )
        clock = now or datetime.now(UTC)
        summaries = self.order_summary_service.list_user_order_summaries(
            session,
            user_id=user.id,
            language_code=language_code,
            limit=limit,
            offset=offset,
        )
        items: list[MiniAppBookingListItemRead] = []
        for summary in summaries:
            booking_label, payment_label, state, cta = resolve_mini_app_booking_facade(summary.order, now=clock)
            items.append(
                MiniAppBookingListItemRead(
                    summary=summary,
                    user_visible_booking_label=booking_label,
                    user_visible_payment_label=payment_label,
                    facade_state=state,
                    primary_cta=cta,
                )
            )
        return MiniAppBookingsListRead(items=items)

    def get_booking_detail(
        self,
        session: Session,
        *,
        order_id: int,
        telegram_user_id: int,
        language_code: str | None = None,
        now: datetime | None = None,
    ) -> MiniAppBookingDetailRead | None:
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

        summary = self.order_summary_service.get_order_summary(
            session,
            order_id=order_id,
            language_code=language_code,
        )
        if summary is None:
            return None

        clock = now or datetime.now(UTC)
        booking_label, payment_label, state, cta = resolve_mini_app_booking_facade(summary.order, now=clock)

        payment_hint: str | None = None
        pay_summary = self.payment_summary_service.get_order_payment_summary(session, order_id=order_id)
        if pay_summary and pay_summary.latest_payment is not None:
            lp = pay_summary.latest_payment
            payment_hint = f"Latest payment record: {lp.status.value} ({lp.provider})"

        return MiniAppBookingDetailRead(
            summary=summary,
            user_visible_booking_label=booking_label,
            user_visible_payment_label=payment_label,
            facade_state=state,
            primary_cta=cta,
            payment_session_hint=payment_hint,
        )
