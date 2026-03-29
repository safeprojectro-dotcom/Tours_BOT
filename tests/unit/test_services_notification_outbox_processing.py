from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.repositories.notification_outbox import NotificationOutboxRepository
from app.schemas.notification import NotificationDeliveryStatus, NotificationOutboxStatus
from app.services.notification_delivery import NotificationDeliveryService
from app.services.notification_outbox import NotificationOutboxService
from app.services.notification_outbox_processing import NotificationOutboxProcessingService
from app.workers.notification_outbox_processing import run_once
from tests.unit.base import FoundationDBTestCase


class _FakeTelegramPrivateAdapter:
    def __init__(self, *, message_id: str | None = "123", error: Exception | None = None) -> None:
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


class NotificationOutboxProcessingServiceTests(FoundationDBTestCase):
    def _create_outbox_entry(self, *, dispatch_key: str, status: str = "pending"):
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        return NotificationOutboxRepository().create(
            self.session,
            data={
                "dispatch_key": dispatch_key,
                "channel": "telegram_private",
                "event_type": "payment_pending",
                "order_id": order.id,
                "user_id": user.id,
                "telegram_user_id": user.telegram_user_id,
                "language_code": "en",
                "title": "Payment pending",
                "message": "Reminder message",
                "payload_metadata": {"order_id": order.id},
                "status": status,
            },
        )

    def test_pickup_pending_entries_marks_only_pending_rows_processing(self) -> None:
        pending = self._create_outbox_entry(dispatch_key="dispatch-pending", status="pending")
        self._create_outbox_entry(dispatch_key="dispatch-delivered", status="delivered")

        picked = NotificationOutboxService().pickup_pending_entries(self.session, limit=10)

        self.assertEqual([item.id for item in picked], [pending.id])
        refreshed = self.session.get(type(pending), pending.id)
        assert refreshed is not None
        self.assertEqual(refreshed.status, NotificationOutboxStatus.PROCESSING)

    def test_process_pending_entries_delivers_and_marks_row_delivered(self) -> None:
        entry = self._create_outbox_entry(dispatch_key="dispatch-success", status="pending")
        adapter = _FakeTelegramPrivateAdapter(message_id="555")
        service = NotificationOutboxProcessingService(
            notification_delivery_service=NotificationDeliveryService(telegram_private_adapter=adapter),
        )

        deliveries = asyncio.run(service.process_pending_entries(self.session, limit=10))

        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0].status, NotificationDeliveryStatus.DELIVERED)
        self.assertEqual(deliveries[0].provider_message_id, "555")
        refreshed = self.session.get(type(entry), entry.id)
        assert refreshed is not None
        self.assertEqual(refreshed.status, NotificationOutboxStatus.DELIVERED)
        self.assertEqual(len(adapter.calls), 1)

    def test_process_pending_entries_marks_failed_and_second_run_skips_entry(self) -> None:
        entry = self._create_outbox_entry(dispatch_key="dispatch-failed", status="pending")
        adapter = _FakeTelegramPrivateAdapter(error=RuntimeError("telegram unavailable"))
        service = NotificationOutboxProcessingService(
            notification_delivery_service=NotificationDeliveryService(telegram_private_adapter=adapter),
        )

        first = asyncio.run(service.process_pending_entries(self.session, limit=10))
        second = asyncio.run(service.process_pending_entries(self.session, limit=10))

        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].status, NotificationDeliveryStatus.FAILED)
        self.assertEqual(first[0].error_message, "telegram unavailable")
        self.assertEqual(second, [])
        refreshed = self.session.get(type(entry), entry.id)
        assert refreshed is not None
        self.assertEqual(refreshed.status, NotificationOutboxStatus.FAILED)

    def test_worker_run_once_delegates_to_async_worker(self) -> None:
        with patch("app.workers.notification_outbox_processing.run_once_async", new_callable=AsyncMock) as run_once_async:
            run_once_async.return_value = ["processed"]

            result = run_once(limit=5)

        self.assertEqual(result, ["processed"])
        run_once_async.assert_awaited_once()
