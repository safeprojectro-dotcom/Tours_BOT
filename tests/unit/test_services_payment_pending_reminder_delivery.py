from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationDeliveryStatus
from app.services.notification_delivery import NotificationDeliveryService
from app.services.payment_pending_reminder_delivery import PaymentPendingReminderDeliveryService
from app.services.payment_pending_reminder import PaymentPendingReminderService
from app.workers.payment_pending_reminder_delivery import run_once
from tests.unit.base import FoundationDBTestCase


class _FakeTelegramPrivateAdapter:
    def __init__(self, *, message_id: str | None = "777", error: Exception | None = None) -> None:
        self.message_id = message_id
        self.error = error
        self.calls: list[tuple[int, str]] = []

    async def send_message(self, *, telegram_user_id: int, text: str) -> str | None:
        self.calls.append((telegram_user_id, text))
        if self.error is not None:
            raise self.error
        return self.message_id

    async def close(self) -> None:
        return None


class PaymentPendingReminderDeliveryServiceTests(FoundationDBTestCase):
    def test_deliver_due_reminders_sends_due_payment_pending_notification(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(code="REM-DEL-1", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="ro", title="Belgrad Livrare")
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=20),
        )
        self.create_payment(order, external_payment_id="delivery-reminder-1", status=PaymentStatus.AWAITING_PAYMENT)

        adapter = _FakeTelegramPrivateAdapter(message_id="999")
        delivery_service = NotificationDeliveryService(telegram_private_adapter=adapter)
        service = PaymentPendingReminderDeliveryService(
            payment_pending_reminder_service=PaymentPendingReminderService(),
            notification_delivery_service=delivery_service,
        )

        results = asyncio.run(
            service.deliver_due_reminders(
                self.session,
                now=now,
                due_within=timedelta(hours=1),
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, NotificationDeliveryStatus.DELIVERED)
        self.assertEqual(results[0].provider_message_id, "999")
        self.assertEqual(len(adapter.calls), 1)
        telegram_user_id, text = adapter.calls[0]
        self.assertEqual(telegram_user_id, user.telegram_user_id)
        self.assertIn("Plata este in asteptare", text)
        self.assertIn("delivery-reminder-1", text)

    def test_deliver_due_reminders_returns_failed_result_when_delivery_errors(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="REM-DEL-2", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=15),
        )
        self.create_payment(order, external_payment_id="delivery-reminder-2", status=PaymentStatus.AWAITING_PAYMENT)

        adapter = _FakeTelegramPrivateAdapter(error=RuntimeError("network unavailable"))
        service = PaymentPendingReminderDeliveryService(
            notification_delivery_service=NotificationDeliveryService(telegram_private_adapter=adapter),
        )

        results = asyncio.run(
            service.deliver_due_reminders(
                self.session,
                now=now,
                due_within=timedelta(hours=1),
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, NotificationDeliveryStatus.FAILED)
        self.assertEqual(results[0].error_message, "network unavailable")
        refreshed_order = self.session.get(type(order), order.id)
        assert refreshed_order is not None
        self.assertEqual(refreshed_order.payment_status, PaymentStatus.AWAITING_PAYMENT)
        self.assertEqual(refreshed_order.cancellation_status, CancellationStatus.ACTIVE)

    def test_worker_run_once_delegates_to_async_worker(self) -> None:
        with patch("app.workers.payment_pending_reminder_delivery.run_once_async", new_callable=AsyncMock) as run_once_async:
            run_once_async.return_value = ["delivered-result"]

            results = run_once(now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC), limit=20)

        self.assertEqual(results, ["delivered-result"])
        run_once_async.assert_awaited_once()
