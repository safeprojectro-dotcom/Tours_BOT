from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationChannel, NotificationDispatchStatus, NotificationEventType
from app.services.notification_dispatch import NotificationDispatchService
from tests.unit.base import FoundationDBTestCase


class NotificationDispatchServiceTests(FoundationDBTestCase):
    def test_prepare_dispatch_builds_telegram_private_envelope(self) -> None:
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(code="DISPATCH-1", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="ro", title="Belgrad Dispatch")
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
        )
        self.create_payment(order, external_payment_id="dispatch-payment-1", status=PaymentStatus.AWAITING_PAYMENT)

        dispatch = NotificationDispatchService().prepare_dispatch(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_PENDING,
        )

        self.assertIsNotNone(dispatch)
        assert dispatch is not None
        self.assertEqual(dispatch.channel, NotificationChannel.TELEGRAM_PRIVATE)
        self.assertEqual(dispatch.status, NotificationDispatchStatus.PREPARED)
        self.assertEqual(
            dispatch.dispatch_key,
            "telegram_private:payment_pending:" + str(order.id) + ":ro",
        )
        self.assertEqual(dispatch.payload.telegram_user_id, user.telegram_user_id)
        self.assertIn("dispatch-payment-1", dispatch.payload.message)

    def test_prepare_available_dispatches_returns_current_lifecycle_events(self) -> None:
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="DISPATCH-2", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
        )
        self.create_payment(order, external_payment_id="dispatch-payment-2", status=PaymentStatus.AWAITING_PAYMENT)

        dispatches = NotificationDispatchService().prepare_available_dispatches(
            self.session,
            order_id=order.id,
        )

        self.assertEqual(len(dispatches), 2)
        self.assertEqual(
            [item.payload.event_type for item in dispatches],
            [
                NotificationEventType.TEMPORARY_RESERVATION_CREATED,
                NotificationEventType.PAYMENT_PENDING,
            ],
        )
        self.assertEqual(len({item.dispatch_key for item in dispatches}), 2)

    def test_prepare_dispatch_returns_none_for_unsupported_event_state(self) -> None:
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="DISPATCH-3", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
        )

        dispatch = NotificationDispatchService().prepare_dispatch(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_CONFIRMED,
        )

        self.assertIsNone(dispatch)

    def test_prepare_dispatch_respects_explicit_language_override(self) -> None:
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(code="DISPATCH-4", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
            total_amount="199.98",
        )
        self.create_payment(order, external_payment_id="dispatch-payment-4", status=PaymentStatus.PAID)

        dispatch = NotificationDispatchService().prepare_dispatch(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_CONFIRMED,
            language_code="de",
        )

        self.assertIsNotNone(dispatch)
        assert dispatch is not None
        self.assertEqual(dispatch.payload.language_code, "de")
        self.assertEqual(
            dispatch.dispatch_key,
            "telegram_private:payment_confirmed:" + str(order.id) + ":de",
        )
        self.assertEqual(dispatch.payload.title, "Zahlung bestaetigt")
