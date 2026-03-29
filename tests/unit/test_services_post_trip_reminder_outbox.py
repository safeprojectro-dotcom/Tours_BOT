from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationOutboxStatus
from app.services.notification_outbox import NotificationOutboxService
from app.services.post_trip_reminder_outbox import PostTripReminderOutboxService
from app.workers.post_trip_reminder_outbox import run_once
from tests.unit.base import FoundationDBTestCase


class PostTripReminderOutboxServiceTests(FoundationDBTestCase):
    def test_enqueue_due_reminders_persists_due_post_trip_reminder_once(self) -> None:
        now = datetime(2026, 4, 5, 10, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(
            code="POST-OUT-1",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=2),
            return_datetime=now - timedelta(hours=4),
        )
        self.create_translation(tour, language_code="ro", title="Belgrad Final Outbox")
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, external_payment_id="post-outbox", status=PaymentStatus.PAID)

        service = PostTripReminderOutboxService()

        first = service.enqueue_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )
        second = service.enqueue_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(first[0].id, second[0].id)
        self.assertEqual(first[0].status, NotificationOutboxStatus.PENDING)
        pending = NotificationOutboxService().list_pending_entries(self.session)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].dispatch_key, first[0].dispatch_key)

    def test_worker_run_once_delegates_to_outbox_service(self) -> None:
        expected_entries = ["outbox-entry"]
        with patch("app.workers.post_trip_reminder_outbox.PostTripReminderOutboxService") as service_cls:
            service_cls.return_value.enqueue_due_reminders.return_value = expected_entries

            entries = run_once(now=datetime(2026, 4, 5, 10, 0, tzinfo=UTC), limit=10)

        self.assertEqual(entries, expected_entries)
        service_cls.return_value.enqueue_due_reminders.assert_called_once()
