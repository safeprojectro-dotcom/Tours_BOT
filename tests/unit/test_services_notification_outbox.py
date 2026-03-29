from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.schemas.notification import NotificationDispatchStatus, NotificationEventType, NotificationOutboxStatus
from app.services.notification_dispatch import NotificationDispatchService
from app.services.notification_outbox import NotificationOutboxService
from tests.unit.base import FoundationDBTestCase


class NotificationOutboxServiceTests(FoundationDBTestCase):
    def test_enqueue_dispatch_creates_pending_outbox_entry(self) -> None:
        user = self.create_user(preferred_language="ro")
        tour = self.create_tour(code="OUTBOX-1", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="ro", title="Belgrad Outbox")
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
        self.create_payment(order, external_payment_id="outbox-payment-1", status=PaymentStatus.AWAITING_PAYMENT)
        dispatch = NotificationDispatchService().prepare_dispatch(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_PENDING,
        )

        self.assertIsNotNone(dispatch)
        assert dispatch is not None

        entry = NotificationOutboxService().enqueue_dispatch(self.session, dispatch=dispatch)

        self.assertEqual(entry.dispatch_key, dispatch.dispatch_key)
        self.assertEqual(entry.status, NotificationOutboxStatus.PENDING)
        self.assertEqual(entry.channel, dispatch.channel)
        self.assertEqual(entry.event_type, dispatch.payload.event_type)
        self.assertEqual(entry.payload_metadata["payment_session_reference"], "outbox-payment-1")

    def test_enqueue_dispatch_dedupes_by_deterministic_dispatch_key(self) -> None:
        user = self.create_user(preferred_language="en")
        tour = self.create_tour(code="OUTBOX-2", status=TourStatus.OPEN_FOR_SALE)
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
        self.create_payment(order, external_payment_id="outbox-payment-2", status=PaymentStatus.AWAITING_PAYMENT)
        dispatch = NotificationDispatchService().prepare_dispatch(
            self.session,
            order_id=order.id,
            event_type=NotificationEventType.PAYMENT_PENDING,
        )

        self.assertIsNotNone(dispatch)
        assert dispatch is not None
        service = NotificationOutboxService()

        first = service.enqueue_dispatch(self.session, dispatch=dispatch)
        second = service.enqueue_dispatch(self.session, dispatch=dispatch)
        pending_dispatches = service.list_pending_dispatches(self.session)

        self.assertEqual(first.id, second.id)
        self.assertEqual(len(pending_dispatches), 1)
        self.assertEqual(pending_dispatches[0].dispatch_key, dispatch.dispatch_key)
        self.assertEqual(pending_dispatches[0].status, NotificationDispatchStatus.PREPARED)
