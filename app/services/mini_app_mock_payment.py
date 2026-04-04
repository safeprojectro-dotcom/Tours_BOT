"""Staging/local mock completion for Mini App — delegates to PaymentReconciliationService only."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.models.enums import BookingStatus, PaymentStatus
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentProviderResult, PaymentReconciliationRead
from app.services.payment_entry import PaymentEntryService
from app.services.payment_reconciliation import PaymentReconciliationService
from app.services.reservation_expiry import lazy_expire_due_reservations


class MiniAppMockPaymentCompletionService:
    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        payment_repository: PaymentRepository | None = None,
    ) -> None:
        self.order_repository = order_repository or OrderRepository()
        self.payment_repository = payment_repository or PaymentRepository()

    def _user_sync(self) -> TelegramUserContextService:
        settings = get_settings()
        return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)

    def complete_mock_payment_for_order(
        self,
        session: Session,
        *,
        order_id: int,
        telegram_user_id: int,
    ) -> PaymentReconciliationRead | None:
        if not get_settings().enable_mock_payment_completion:
            return None

        lazy_expire_due_reservations(session)
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=None,
        )

        order = self.order_repository.get_for_update(session, order_id=order_id)
        if order is None or order.user_id != user.id:
            return None

        payment = self.payment_repository.get_latest_by_order(session, order_id=order.id)
        if payment is None or payment.external_payment_id is None:
            return None
        if payment.provider != PaymentEntryService.DEFAULT_PROVIDER:
            return None

        entry = PaymentEntryService(
            order_repository=self.order_repository,
            payment_repository=self.payment_repository,
        )
        if order.payment_status == PaymentStatus.PAID and order.booking_status == BookingStatus.CONFIRMED:
            pass
        elif not entry._is_order_valid_for_payment_entry(  # noqa: SLF001
            order=order,
            user_id=user.id,
            now=datetime.now(UTC),
        ):
            return None

        provider_result = PaymentProviderResult(
            provider=payment.provider,
            external_payment_id=payment.external_payment_id,
            verified=True,
            provider_status="paid",
            normalized_status=PaymentStatus.PAID,
            amount=payment.amount,
            currency=payment.currency,
            raw_payload={"kind": "mock_payment_completion", "source": "mini_app"},
        )
        return PaymentReconciliationService(
            order_repository=self.order_repository,
            payment_repository=self.payment_repository,
        ).reconcile_provider_result(session, provider_result=provider_result)
