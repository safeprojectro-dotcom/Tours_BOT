from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationEventType
from app.services.post_trip_reminder import PostTripReminderService
from app.workers.post_trip_reminder import run_once
from tests.unit.base import FoundationDBTestCase


class PostTripReminderServiceTests(FoundationDBTestCase):
    def test_list_due_order_ids_returns_only_confirmed_paid_active_orders_returned_recently(self) -> None:
        now = datetime(2026, 4, 5, 10, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        due_tour = self.create_tour(
            code="POST-1",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=2),
            return_datetime=now - timedelta(hours=6),
        )
        due_point = self.create_boarding_point(due_tour)
        due_order = self.create_order(
            user,
            due_tour,
            due_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(due_order, external_payment_id="post-trip-due", status=PaymentStatus.PAID)

        older_tour = self.create_tour(
            code="POST-2",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=4),
            return_datetime=now - timedelta(days=2),
        )
        older_point = self.create_boarding_point(older_tour)
        self.create_order(
            user,
            older_tour,
            older_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )

        future_tour = self.create_tour(
            code="POST-3",
            status=TourStatus.IN_PROGRESS,
            departure_datetime=now - timedelta(hours=10),
            return_datetime=now + timedelta(hours=4),
        )
        future_point = self.create_boarding_point(future_tour)
        self.create_order(
            user,
            future_tour,
            future_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )

        cancelled_tour = self.create_tour(
            code="POST-4",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=1),
            return_datetime=now - timedelta(hours=3),
        )
        cancelled_point = self.create_boarding_point(cancelled_tour)
        self.create_order(
            user,
            cancelled_tour,
            cancelled_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.CANCELLED_BY_CLIENT,
        )

        order_ids = PostTripReminderService().list_due_order_ids(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual(order_ids, [due_order.id])

    def test_prepare_due_reminders_builds_post_trip_dispatches_in_return_order(self) -> None:
        now = datetime(2026, 4, 5, 10, 0, tzinfo=UTC)

        first_user = self.create_user(preferred_language="ro")
        first_tour = self.create_tour(
            code="POST-5A",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=2),
            return_datetime=now - timedelta(hours=2),
        )
        self.create_translation(first_tour, language_code="ro", title="Belgrad Revenit")
        first_point = self.create_boarding_point(first_tour)
        first_order = self.create_order(
            first_user,
            first_tour,
            first_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(first_order, external_payment_id="post-1", status=PaymentStatus.PAID)

        second_user = self.create_user(preferred_language="de")
        second_tour = self.create_tour(
            code="POST-5B",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=3),
            return_datetime=now - timedelta(hours=5),
        )
        second_point = self.create_boarding_point(second_tour)
        second_order = self.create_order(
            second_user,
            second_tour,
            second_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(second_order, external_payment_id="post-2", status=PaymentStatus.PAID)

        dispatches = PostTripReminderService().prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual([item.payload.order_id for item in dispatches], [first_order.id, second_order.id])
        self.assertEqual(
            [item.payload.event_type for item in dispatches],
            [
                NotificationEventType.POST_TRIP_REMINDER,
                NotificationEventType.POST_TRIP_REMINDER,
            ],
        )
        self.assertEqual(dispatches[0].payload.language_code, "ro")
        self.assertEqual(dispatches[0].payload.title, "Calatorie finalizata")
        self.assertIn("Belgrad Revenit", dispatches[0].payload.message)
        self.assertEqual(
            dispatches[1].dispatch_key,
            f"telegram_private:post_trip_reminder:{second_order.id}:de",
        )

    def test_prepare_due_reminders_is_repeat_safe_without_state_mutation(self) -> None:
        now = datetime(2026, 4, 5, 10, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(
            code="POST-6",
            status=TourStatus.COMPLETED,
            departure_datetime=now - timedelta(days=2),
            return_datetime=now - timedelta(hours=8),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, external_payment_id="post-repeat", status=PaymentStatus.PAID)

        service = PostTripReminderService()
        first_batch = service.prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )
        second_batch = service.prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual(
            [item.dispatch_key for item in first_batch],
            [item.dispatch_key for item in second_batch],
        )
        refreshed_order = self.session.get(type(order), order.id)
        assert refreshed_order is not None
        self.assertEqual(refreshed_order.booking_status, BookingStatus.CONFIRMED)
        self.assertEqual(refreshed_order.payment_status, PaymentStatus.PAID)
        self.assertEqual(refreshed_order.cancellation_status, CancellationStatus.ACTIVE)

    def test_worker_run_once_delegates_to_post_trip_reminder_service(self) -> None:
        expected_dispatches = ["prepared-dispatch"]
        with patch("app.workers.post_trip_reminder.PostTripReminderService") as service_cls:
            service_cls.return_value.prepare_due_reminders.return_value = expected_dispatches

            dispatches = run_once(now=datetime(2026, 4, 5, 10, 0, tzinfo=UTC), limit=50)

        self.assertEqual(dispatches, expected_dispatches)
        service_cls.return_value.prepare_due_reminders.assert_called_once()
