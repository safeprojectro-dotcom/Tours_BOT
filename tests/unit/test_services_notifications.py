from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.notification import NotificationEventType
from app.services.notification_preparation import NotificationPreparationService
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from tests.unit.base import FoundationDBTestCase


class NotificationPreparationServiceTests(FoundationDBTestCase):
    def test_list_available_event_types_for_active_temporary_reservation(self) -> None:
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(code="NOTIF-1", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="ro", title="Belgrad RO")
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
        self.create_payment(order, external_payment_id="pay-session-1", status=PaymentStatus.AWAITING_PAYMENT)

        events = NotificationPreparationService().list_available_event_types(self.session, order_id=order.id)

        self.assertEqual(
            events,
            [
                NotificationEventType.TEMPORARY_RESERVATION_CREATED,
                NotificationEventType.PAYMENT_PENDING,
            ],
        )

    def test_prepare_payment_pending_notification_uses_user_language_and_payment_reference(self) -> None:
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(code="NOTIF-2", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="ro", title="Belgrad Confirmat")
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
            total_amount="179.00",
        )
        self.create_payment(order, external_payment_id="mockpay-order-2", status=PaymentStatus.AWAITING_PAYMENT)

        payload = NotificationPreparationService().prepare_notification(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_PENDING,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.language_code, "ro")
        self.assertEqual(payload.event_type, NotificationEventType.PAYMENT_PENDING)
        self.assertIn("Belgrad Confirmat", payload.message)
        self.assertIn("mockpay-order-2", payload.message)
        self.assertEqual(payload.metadata["payment_session_reference"], "mockpay-order-2")

    def test_prepare_payment_confirmed_notification_requires_confirmed_paid_order(self) -> None:
        user = self.create_user(preferred_language="de")
        tour = self.create_tour(code="NOTIF-3", status=TourStatus.OPEN_FOR_SALE)
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
        self.create_payment(order, external_payment_id="pay-confirmed", status=PaymentStatus.PAID)

        payload = NotificationPreparationService().prepare_notification(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_CONFIRMED,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.language_code, "de")
        self.assertEqual(payload.title, "Zahlung bestaetigt")
        self.assertIn("199.98 EUR", payload.message)

    def test_prepare_predeparture_notification_for_confirmed_paid_order(self) -> None:
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(
            code="NOTIF-3B",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 4, 5, 9, 30, tzinfo=UTC),
        )
        self.create_translation(tour, language_code="ro", title="Belgrad Plecare")
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
        self.create_payment(order, external_payment_id="pay-predeparture", status=PaymentStatus.PAID)

        payload = NotificationPreparationService().prepare_notification(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PREDEPARTURE_REMINDER,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.language_code, "ro")
        self.assertEqual(payload.title, "Reminder de plecare")
        self.assertIn("Belgrad Plecare", payload.message)
        self.assertIn("2026-04-05 09:30", payload.message)
        self.assertEqual(payload.metadata["departure_datetime"], "2026-04-05 09:30")

    def test_prepare_reservation_expired_notification_respects_current_status_semantics(self) -> None:
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="NOTIF-4", status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )

        payload = NotificationPreparationService().prepare_notification(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.RESERVATION_EXPIRED,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.event_type, NotificationEventType.RESERVATION_EXPIRED)
        self.assertIn("has expired", payload.message)

    def test_prepare_notification_returns_none_for_unsupported_event_in_current_state(self) -> None:
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="NOTIF-5", status=TourStatus.OPEN_FOR_SALE)
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

        payload = NotificationPreparationService().prepare_notification(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_CONFIRMED,
        )

        self.assertIsNone(payload)

    def test_prepare_notification_falls_back_to_english_for_unknown_language(self) -> None:
        user = self.create_user(preferred_language="xx")
        tour = self.create_tour(code="NOTIF-6", status=TourStatus.OPEN_FOR_SALE)
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

        payload = NotificationPreparationService().prepare_notification(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.TEMPORARY_RESERVATION_CREATED,
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.language_code, "en")
        self.assertEqual(payload.title, "Temporary reservation created")
