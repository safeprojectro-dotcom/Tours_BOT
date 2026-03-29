from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationEventType
from app.services.predeparture_reminder import PredepartureReminderService
from app.workers.predeparture_reminder import run_once
from tests.unit.base import FoundationDBTestCase


class PredepartureReminderServiceTests(FoundationDBTestCase):
    def test_list_due_order_ids_returns_only_confirmed_paid_active_orders_departing_soon(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        due_tour = self.create_tour(
            code="PRE-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=12),
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
        self.create_payment(due_order, external_payment_id="predeparture-due", status=PaymentStatus.PAID)

        later_tour = self.create_tour(
            code="PRE-2",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(days=2),
        )
        later_point = self.create_boarding_point(later_tour)
        self.create_order(
            user,
            later_tour,
            later_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )

        unpaid_tour = self.create_tour(
            code="PRE-3",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=10),
        )
        unpaid_point = self.create_boarding_point(unpaid_tour)
        self.create_order(
            user,
            unpaid_tour,
            unpaid_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
        )

        cancelled_tour = self.create_tour(
            code="PRE-4",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=8),
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

        order_ids = PredepartureReminderService().list_due_order_ids(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual(order_ids, [due_order.id])

    def test_prepare_due_reminders_builds_predeparture_dispatches_in_departure_order(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)

        first_user = self.create_user(preferred_language="ro")
        first_tour = self.create_tour(
            code="PRE-5A",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=9),
        )
        self.create_translation(first_tour, language_code="ro", title="Belgrad Plecare Reminder")
        first_point = self.create_boarding_point(first_tour)
        first_order = self.create_order(
            first_user,
            first_tour,
            first_point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(first_order, external_payment_id="pre-1", status=PaymentStatus.PAID)

        second_user = self.create_user(preferred_language="de")
        second_tour = self.create_tour(
            code="PRE-5B",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=20),
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
        self.create_payment(second_order, external_payment_id="pre-2", status=PaymentStatus.PAID)

        dispatches = PredepartureReminderService().prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=24),
        )

        self.assertEqual([item.payload.order_id for item in dispatches], [first_order.id, second_order.id])
        self.assertEqual(
            [item.payload.event_type for item in dispatches],
            [
                NotificationEventType.PREDEPARTURE_REMINDER,
                NotificationEventType.PREDEPARTURE_REMINDER,
            ],
        )
        self.assertEqual(dispatches[0].payload.language_code, "ro")
        self.assertEqual(dispatches[0].payload.title, "Reminder de plecare")
        self.assertIn("Belgrad Plecare Reminder", dispatches[0].payload.message)
        self.assertEqual(
            dispatches[1].dispatch_key,
            f"telegram_private:predeparture_reminder:{second_order.id}:de",
        )

    def test_prepare_due_reminders_is_repeat_safe_without_state_mutation(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(
            code="PRE-6",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=now + timedelta(hours=15),
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
        self.create_payment(order, external_payment_id="pre-repeat", status=PaymentStatus.PAID)

        service = PredepartureReminderService()
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

    def test_worker_run_once_delegates_to_predeparture_reminder_service(self) -> None:
        expected_dispatches = ["prepared-dispatch"]
        with patch("app.workers.predeparture_reminder.PredepartureReminderService") as service_cls:
            service_cls.return_value.prepare_due_reminders.return_value = expected_dispatches

            dispatches = run_once(now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC), limit=50)

        self.assertEqual(dispatches, expected_dispatches)
        service_cls.return_value.prepare_due_reminders.assert_called_once()
