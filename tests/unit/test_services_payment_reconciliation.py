from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentProviderResult
from app.services.payment_reconciliation import PaymentReconciliationService
from tests.unit.base import FoundationDBTestCase


class PaymentReconciliationServiceTests(FoundationDBTestCase):
    def test_reconcile_provider_result_confirms_reserved_order_on_paid_result(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="PAY-REC-1",
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
        payment = self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-order-1-ok",
            status=PaymentStatus.AWAITING_PAYMENT,
        )
        self.session.commit()

        result = PaymentReconciliationService().reconcile_provider_result(
            self.session,
            provider_result=PaymentProviderResult(
                provider="mockpay",
                external_payment_id="mockpay-order-1-ok",
                verified=True,
                provider_status="succeeded",
                normalized_status=PaymentStatus.PAID,
                amount=payment.amount,
                currency=payment.currency,
                raw_payload={"event": "payment.succeeded"},
            ),
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.reconciliation_applied)
        self.assertTrue(result.payment_confirmed)
        self.assertEqual(result.payment.status, PaymentStatus.PAID)
        self.assertEqual(result.order.payment_status, PaymentStatus.PAID)
        self.assertEqual(result.order.booking_status, BookingStatus.CONFIRMED)

    def test_reconcile_provider_result_is_idempotent_for_duplicate_paid_result(self) -> None:
        user = self.create_user()
        tour = self.create_tour(status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-order-paid",
            status=PaymentStatus.PAID,
        )
        self.session.commit()

        result = PaymentReconciliationService().reconcile_provider_result(
            self.session,
            provider_result=PaymentProviderResult(
                provider="mockpay",
                external_payment_id="mockpay-order-paid",
                verified=True,
                provider_status="succeeded",
                normalized_status=PaymentStatus.PAID,
            ),
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertFalse(result.reconciliation_applied)
        self.assertTrue(result.payment_confirmed)
        self.assertEqual(result.payment.status, PaymentStatus.PAID)
        self.assertEqual(result.order.payment_status, PaymentStatus.PAID)

    def test_reconcile_provider_result_rejects_unknown_unverified_or_mismatched_payload(self) -> None:
        user = self.create_user()
        tour = self.create_tour(status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        payment = self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-order-check",
            status=PaymentStatus.AWAITING_PAYMENT,
        )
        self.session.commit()

        unverified = PaymentReconciliationService().reconcile_provider_result(
            self.session,
            provider_result=PaymentProviderResult(
                provider="mockpay",
                external_payment_id="mockpay-order-check",
                verified=False,
                provider_status="succeeded",
                normalized_status=PaymentStatus.PAID,
            ),
        )
        unknown = PaymentReconciliationService().reconcile_provider_result(
            self.session,
            provider_result=PaymentProviderResult(
                provider="mockpay",
                external_payment_id="missing-session",
                verified=True,
                provider_status="succeeded",
                normalized_status=PaymentStatus.PAID,
            ),
        )
        mismatched = PaymentReconciliationService().reconcile_provider_result(
            self.session,
            provider_result=PaymentProviderResult(
                provider="mockpay",
                external_payment_id="mockpay-order-check",
                verified=True,
                provider_status="succeeded",
                normalized_status=PaymentStatus.PAID,
                amount=payment.amount + 1,
            ),
        )

        self.assertIsNone(unverified)
        self.assertIsNone(unknown)
        self.assertIsNone(mismatched)

    def test_reconcile_provider_result_does_not_regress_paid_state_with_later_non_paid_result(self) -> None:
        user = self.create_user()
        tour = self.create_tour(status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        payment = self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-order-stable",
            status=PaymentStatus.PAID,
        )
        self.session.commit()

        result = PaymentReconciliationService().reconcile_provider_result(
            self.session,
            provider_result=PaymentProviderResult(
                provider="mockpay",
                external_payment_id="mockpay-order-stable",
                verified=True,
                provider_status="pending",
                normalized_status=PaymentStatus.AWAITING_PAYMENT,
                amount=payment.amount,
                currency=payment.currency,
            ),
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertFalse(result.reconciliation_applied)
        self.assertTrue(result.payment_confirmed)
        self.assertEqual(result.payment.status, PaymentStatus.PAID)
        self.assertEqual(result.order.booking_status, BookingStatus.CONFIRMED)
        self.assertEqual(result.order.payment_status, PaymentStatus.PAID)

        payments = PaymentRepository().list_by_order(self.session, order_id=order.id)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].status, PaymentStatus.PAID)
