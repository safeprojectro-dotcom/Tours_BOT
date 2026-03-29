from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationEventType
from app.services.payment_pending_reminder import PaymentPendingReminderService
from app.workers.payment_pending_reminder import run_once
from tests.unit.base import FoundationDBTestCase


class PaymentPendingReminderServiceTests(FoundationDBTestCase):
    def test_list_due_order_ids_returns_only_active_reservations_due_within_window(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="REM-1", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        due_order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=30),
        )
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(hours=2),
        )
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now - timedelta(minutes=1),
        )
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=20),
        )
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=now + timedelta(minutes=20),
        )

        order_ids = PaymentPendingReminderService().list_due_order_ids(
            self.session,
            now=now,
            due_within=timedelta(hours=1),
        )

        self.assertEqual(order_ids, [due_order.id])

    def test_prepare_due_reminders_builds_payment_pending_dispatches_in_expiry_order(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)

        first_user = self.create_user(preferred_language="ro")
        first_tour = self.create_tour(code="REM-2A", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(first_tour, language_code="ro", title="Belgrad Reminder")
        first_point = self.create_boarding_point(first_tour)
        first_order = self.create_order(
            first_user,
            first_tour,
            first_point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=15),
        )
        self.create_payment(
            first_order,
            external_payment_id="pending-reminder-1",
            status=PaymentStatus.AWAITING_PAYMENT,
        )

        second_user = self.create_user(preferred_language="de")
        second_tour = self.create_tour(code="REM-2B", status=TourStatus.OPEN_FOR_SALE)
        second_point = self.create_boarding_point(second_tour)
        second_order = self.create_order(
            second_user,
            second_tour,
            second_point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=45),
        )
        self.create_payment(
            second_order,
            external_payment_id="pending-reminder-2",
            status=PaymentStatus.AWAITING_PAYMENT,
        )

        dispatches = PaymentPendingReminderService().prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=1),
        )

        self.assertEqual([item.payload.order_id for item in dispatches], [first_order.id, second_order.id])
        self.assertEqual(
            [item.payload.event_type for item in dispatches],
            [
                NotificationEventType.PAYMENT_PENDING,
                NotificationEventType.PAYMENT_PENDING,
            ],
        )
        self.assertEqual(dispatches[0].payload.language_code, "ro")
        self.assertEqual(dispatches[0].payload.title, "Plata este in asteptare")
        self.assertIn("pending-reminder-1", dispatches[0].payload.message)
        self.assertEqual(dispatches[1].payload.language_code, "de")
        self.assertEqual(dispatches[1].dispatch_key, f"telegram_private:payment_pending:{second_order.id}:de")

    def test_prepare_due_reminders_is_repeat_safe_without_state_mutation(self) -> None:
        now = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="REM-3", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=now + timedelta(minutes=25),
        )
        self.create_payment(order, external_payment_id="pending-reminder-repeat", status=PaymentStatus.AWAITING_PAYMENT)

        service = PaymentPendingReminderService()
        first_batch = service.prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=1),
        )
        second_batch = service.prepare_due_reminders(
            self.session,
            now=now,
            due_within=timedelta(hours=1),
        )

        self.assertEqual(
            [item.dispatch_key for item in first_batch],
            [item.dispatch_key for item in second_batch],
        )
        refreshed_order = self.session.get(type(order), order.id)
        assert refreshed_order is not None
        self.assertEqual(refreshed_order.booking_status, BookingStatus.RESERVED)
        self.assertEqual(refreshed_order.payment_status, PaymentStatus.AWAITING_PAYMENT)
        self.assertEqual(refreshed_order.cancellation_status, CancellationStatus.ACTIVE)
        self.assertEqual(refreshed_order.reservation_expires_at, now + timedelta(minutes=25))

    def test_worker_run_once_delegates_to_payment_pending_reminder_service(self) -> None:
        expected_dispatches = ["prepared-dispatch"]
        with patch("app.workers.payment_pending_reminder.PaymentPendingReminderService") as service_cls:
            service_cls.return_value.prepare_due_reminders.return_value = expected_dispatches

            dispatches = run_once(now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC), limit=50)

        self.assertEqual(dispatches, expected_dispatches)
        service_cls.return_value.prepare_due_reminders.assert_called_once()
