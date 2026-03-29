from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationEventType
from app.services.departure_day_reminder import DepartureDayReminderService
from app.workers.departure_day_reminder import run_once
from tests.unit.base import FoundationDBTestCase


class DepartureDayReminderServiceTests(FoundationDBTestCase):
    def test_list_due_order_ids_returns_only_confirmed_paid_active_orders_departing_later_today(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        due_tour = self.create_tour(
            code="DAY-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=4),
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
        self.create_payment(due_order, external_payment_id="departure-day-due", status=PaymentStatus.PAID)

        tomorrow_tour = self.create_tour(
            code="DAY-2",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=18),
        )
        tomorrow_point = self.create_boarding_point(tomorrow_tour)
        self.create_order(
            user,
            tomorrow_tour,
            tomorrow_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )

        past_tour = self.create_tour(
            code="DAY-3",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now - timedelta(hours=1),
        )
        past_point = self.create_boarding_point(past_tour)
        self.create_order(
            user,
            past_tour,
            past_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )

        cancelled_tour = self.create_tour(
            code="DAY-4",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=6),
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

        order_ids = DepartureDayReminderService().list_due_order_ids(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual(order_ids, [due_order.id])

    def test_prepare_due_reminders_builds_departure_day_dispatches_in_departure_order(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)

        first_user = self.create_user(preferred_language="ro")
        first_tour = self.create_tour(
            code="DAY-5A",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=1),
        )
        self.create_translation(first_tour, language_code="ro", title="Belgrad Azi")
        first_point = self.create_boarding_point(first_tour)
        first_order = self.create_order(
            first_user,
            first_tour,
            first_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(first_order, external_payment_id="day-1", status=PaymentStatus.PAID)

        second_user = self.create_user(preferred_language="de")
        second_tour = self.create_tour(
            code="DAY-5B",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=7),
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
        self.create_payment(second_order, external_payment_id="day-2", status=PaymentStatus.PAID)

        dispatches = DepartureDayReminderService().prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual([item.payload.order_id for item in dispatches], [first_order.id, second_order.id])
        self.assertEqual(
            [item.payload.event_type for item in dispatches],
            [
                NotificationEventType.DEPARTURE_DAY_REMINDER,
                NotificationEventType.DEPARTURE_DAY_REMINDER,
            ],
        )
        self.assertEqual(dispatches[0].payload.language_code, "ro")
        self.assertEqual(dispatches[0].payload.title, "Plecare astazi")
        self.assertIn("Belgrad Azi", dispatches[0].payload.message)
        self.assertEqual(
            dispatches[1].dispatch_key,
            f"telegram_private:departure_day_reminder:{second_order.id}:de",
        )

    def test_prepare_due_reminders_is_repeat_safe_without_state_mutation(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(
            code="DAY-6",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=5),
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
        self.create_payment(order, external_payment_id="day-repeat", status=PaymentStatus.PAID)

        service = DepartureDayReminderService()
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

    def test_worker_run_once_delegates_to_departure_day_reminder_service(self) -> None:
        expected_dispatches = ["prepared-dispatch"]
        with patch("app.workers.departure_day_reminder.DepartureDayReminderService") as service_cls:
            service_cls.return_value.prepare_due_reminders.return_value = expected_dispatches

            dispatches = run_once(now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC), limit=50)

        self.assertEqual(dispatches, expected_dispatches)
        service_cls.return_value.prepare_due_reminders.assert_called_once()
