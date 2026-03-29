from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.repositories.payment import PaymentRepository
from app.services.payment_entry import PaymentEntryService
from tests.unit.base import FoundationDBTestCase


class PaymentEntryServiceTests(FoundationDBTestCase):
    def test_start_payment_entry_creates_payment_session_for_valid_reserved_order(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="PAY-READY-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 2, 12, 0, tzinfo=UTC),
        )
        self.session.commit()

        result = PaymentEntryService().start_payment_entry(
            self.session,
            order_id=order.id,
            user_id=user.id,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertFalse(result.reused_existing_payment)
        self.assertEqual(result.order.id, order.id)
        self.assertEqual(result.payment.order_id, order.id)
        self.assertEqual(result.payment.provider, "mockpay")
        self.assertEqual(result.payment.status, PaymentStatus.AWAITING_PAYMENT)
        self.assertTrue(result.payment_session_reference.startswith(f"mockpay-order-{order.id}-"))

        payments = PaymentRepository().list_by_order(self.session, order_id=order.id)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].external_payment_id, result.payment_session_reference)
        self.assertEqual(payments[0].raw_payload["kind"], "payment_entry")

    def test_start_payment_entry_rejects_expired_or_invalid_order(self) -> None:
        user = self.create_user()
        other_user = self.create_user()
        tour = self.create_tour(
            code="PAY-EXPIRED-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        self.session.commit()

        expired = PaymentEntryService().start_payment_entry(
            self.session,
            order_id=order.id,
            user_id=user.id,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        wrong_user = PaymentEntryService().start_payment_entry(
            self.session,
            order_id=order.id,
            user_id=other_user.id,
            now=datetime(2026, 4, 1, 6, 0, tzinfo=UTC),
        )

        self.assertIsNone(expired)
        self.assertIsNone(wrong_user)
        self.assertEqual(PaymentRepository().list_by_order(self.session, order_id=order.id), [])

    def test_start_payment_entry_reuses_latest_pending_payment(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="PAY-REUSE-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 2, 12, 0, tzinfo=UTC),
        )
        existing_payment = self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-order-existing",
            status=PaymentStatus.UNPAID,
        )
        self.session.commit()

        result = PaymentEntryService().start_payment_entry(
            self.session,
            order_id=order.id,
            user_id=user.id,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.reused_existing_payment)
        self.assertEqual(result.payment.id, existing_payment.id)
        self.assertEqual(result.payment.status, PaymentStatus.AWAITING_PAYMENT)
        self.assertEqual(result.payment_session_reference, "mockpay-order-existing")
        self.assertEqual(len(PaymentRepository().list_by_order(self.session, order_id=order.id)), 1)
