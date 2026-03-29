from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.repositories.notification_outbox import NotificationOutboxRepository
from app.schemas.notification import NotificationDeliveryStatus, NotificationOutboxStatus
from app.services.notification_delivery import NotificationDeliveryService
from app.services.notification_outbox_retry_execution import NotificationOutboxRetryExecutionService
from app.workers.notification_outbox_retry_execution import run_once
from tests.unit.base import FoundationDBTestCase
from tests.unit.test_services_notification_outbox_processing import _FakeTelegramPrivateAdapter


class NotificationOutboxRetryExecutionServiceTests(FoundationDBTestCase):
    def _create_outbox_entry(
        self,
        *,
        dispatch_key: str,
        status: str,
        updated_at: datetime | None = None,
    ):
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        entry = NotificationOutboxRepository().create(
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
        if updated_at is not None:
            entry = NotificationOutboxRepository().update(
                self.session,
                instance=entry,
                data={"updated_at": updated_at},
            )
        return entry

    def test_execute_retryable_entries_recovers_and_delivers_failed_entry(self) -> None:
        entry = self._create_outbox_entry(dispatch_key="retry-failed", status="failed")
        adapter = _FakeTelegramPrivateAdapter(message_id="777")
        service = NotificationOutboxRetryExecutionService(
            notification_outbox_processing_service=None,
        )
        service.notification_outbox_processing_service.notification_delivery_service = NotificationDeliveryService(
            telegram_private_adapter=adapter,
        )

        deliveries = asyncio.run(
            service.execute_retryable_entries(
                self.session,
                now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
                failed_limit=10,
                stale_limit=10,
            )
        )

        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0].dispatch_key, "retry-failed")
        self.assertEqual(deliveries[0].status, NotificationDeliveryStatus.DELIVERED)
        refreshed = self.session.get(type(entry), entry.id)
        assert refreshed is not None
        self.assertEqual(refreshed.status, NotificationOutboxStatus.DELIVERED)
        self.assertEqual(len(adapter.calls), 1)

    def test_process_retryable_pending_entries_only_reprocesses_selected_pending_ids(self) -> None:
        targeted = self._create_outbox_entry(dispatch_key="retry-pending-target", status="pending")
        untouched = self._create_outbox_entry(dispatch_key="retry-pending-other", status="pending")
        adapter = _FakeTelegramPrivateAdapter(message_id="888")
        service = NotificationOutboxRetryExecutionService()
        service.notification_outbox_processing_service.notification_delivery_service = NotificationDeliveryService(
            telegram_private_adapter=adapter,
        )

        deliveries = asyncio.run(
            service.process_retryable_pending_entries(
                self.session,
                outbox_ids=[targeted.id],
            )
        )

        self.assertEqual([item.dispatch_key for item in deliveries], ["retry-pending-target"])
        targeted_refreshed = self.session.get(type(targeted), targeted.id)
        untouched_refreshed = self.session.get(type(untouched), untouched.id)
        assert targeted_refreshed is not None
        assert untouched_refreshed is not None
        self.assertEqual(targeted_refreshed.status, NotificationOutboxStatus.DELIVERED)
        self.assertEqual(untouched_refreshed.status, NotificationOutboxStatus.PENDING)

    def test_execute_retryable_entries_is_repeat_safe_after_success(self) -> None:
        entry = self._create_outbox_entry(
            dispatch_key="retry-repeat",
            status="processing",
            updated_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        adapter = _FakeTelegramPrivateAdapter(message_id="999")
        service = NotificationOutboxRetryExecutionService()
        service.notification_outbox_processing_service.notification_delivery_service = NotificationDeliveryService(
            telegram_private_adapter=adapter,
        )

        first = asyncio.run(
            service.execute_retryable_entries(
                self.session,
                now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
                stale_for=timedelta(minutes=15),
                failed_limit=10,
                stale_limit=10,
            )
        )
        second = asyncio.run(
            service.execute_retryable_entries(
                self.session,
                now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
                stale_for=timedelta(minutes=15),
                failed_limit=10,
                stale_limit=10,
            )
        )

        self.assertEqual([item.dispatch_key for item in first], ["retry-repeat"])
        self.assertEqual(second, [])
        refreshed = self.session.get(type(entry), entry.id)
        assert refreshed is not None
        self.assertEqual(refreshed.status, NotificationOutboxStatus.DELIVERED)
        self.assertEqual(len(adapter.calls), 1)

    def test_worker_run_once_delegates_to_async_worker(self) -> None:
        with patch("app.workers.notification_outbox_retry_execution.run_once_async", new_callable=AsyncMock) as run_once_async:
            run_once_async.return_value = ["retried"]

            result = run_once(failed_limit=5, stale_limit=3)

        self.assertEqual(result, ["retried"])
        run_once_async.assert_awaited_once()
