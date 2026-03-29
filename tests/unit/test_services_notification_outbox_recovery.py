from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.repositories.notification_outbox import NotificationOutboxRepository
from app.schemas.notification import NotificationOutboxStatus
from app.services.notification_outbox_recovery import NotificationOutboxRecoveryService
from app.workers.notification_outbox_recovery import run_once
from tests.unit.base import FoundationDBTestCase


class NotificationOutboxRecoveryServiceTests(FoundationDBTestCase):
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

    def test_retry_failed_entries_requeues_failed_rows_to_pending(self) -> None:
        failed = self._create_outbox_entry(dispatch_key="failed-1", status="failed")
        self._create_outbox_entry(dispatch_key="delivered-1", status="delivered")

        recovered = NotificationOutboxRecoveryService().retry_failed_entries(self.session, limit=10)

        self.assertEqual([item.id for item in recovered], [failed.id])
        refreshed = self.session.get(type(failed), failed.id)
        assert refreshed is not None
        self.assertEqual(refreshed.status, NotificationOutboxStatus.PENDING)

    def test_recover_stale_processing_entries_requeues_only_stale_rows(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        stale = self._create_outbox_entry(
            dispatch_key="processing-stale",
            status="processing",
            updated_at=now - timedelta(minutes=30),
        )
        fresh = self._create_outbox_entry(
            dispatch_key="processing-fresh",
            status="processing",
            updated_at=now - timedelta(minutes=5),
        )

        recovered = NotificationOutboxRecoveryService().recover_stale_processing_entries(
            self.session,
            now=now,
            stale_for=timedelta(minutes=15),
            limit=10,
        )

        self.assertEqual([item.id for item in recovered], [stale.id])
        stale_refreshed = self.session.get(type(stale), stale.id)
        fresh_refreshed = self.session.get(type(fresh), fresh.id)
        assert stale_refreshed is not None
        assert fresh_refreshed is not None
        self.assertEqual(stale_refreshed.status, NotificationOutboxStatus.PENDING)
        self.assertEqual(fresh_refreshed.status, NotificationOutboxStatus.PROCESSING)

    def test_recover_retryable_entries_is_repeat_safe(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        failed = self._create_outbox_entry(dispatch_key="failed-repeat", status="failed")
        stale = self._create_outbox_entry(
            dispatch_key="processing-repeat",
            status="processing",
            updated_at=now - timedelta(minutes=45),
        )

        service = NotificationOutboxRecoveryService()
        first = service.recover_retryable_entries(
            self.session,
            now=now,
            stale_for=timedelta(minutes=15),
            failed_limit=10,
            stale_limit=10,
        )
        second = service.recover_retryable_entries(
            self.session,
            now=now,
            stale_for=timedelta(minutes=15),
            failed_limit=10,
            stale_limit=10,
        )

        self.assertEqual({item.id for item in first}, {failed.id, stale.id})
        self.assertEqual(second, [])

    def test_worker_run_once_delegates_to_recovery_service(self) -> None:
        expected_entries = ["recovered-entry"]
        with patch("app.workers.notification_outbox_recovery.NotificationOutboxRecoveryService") as service_cls:
            service_cls.return_value.recover_retryable_entries.return_value = expected_entries

            entries = run_once(now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC), failed_limit=10, stale_limit=5)

        self.assertEqual(entries, expected_entries)
        service_cls.return_value.recover_retryable_entries.assert_called_once()
