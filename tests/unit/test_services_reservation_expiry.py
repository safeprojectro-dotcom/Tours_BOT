from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.services.reservation_expiry import ReservationExpiryService, lazy_expire_due_reservations
from app.workers.reservation_expiry import run_once
from tests.unit.base import FoundationDBTestCase


class ReservationExpiryServiceTests(FoundationDBTestCase):
    def test_expire_due_reservations_marks_order_and_restores_seats(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="EXP-1",
            seats_total=40,
            seats_available=8,
            status=TourStatus.OPEN_FOR_SALE,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=3,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        self.session.commit()

        expired_count = ReservationExpiryService().expire_due_reservations(
            self.session,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertEqual(expired_count, 1)
        refreshed_order = self.session.get(type(order), order.id)
        refreshed_tour = self.session.get(type(tour), tour.id)
        assert refreshed_order is not None
        assert refreshed_tour is not None
        self.assertEqual(refreshed_order.booking_status, BookingStatus.RESERVED)
        self.assertEqual(refreshed_order.payment_status, PaymentStatus.UNPAID)
        self.assertEqual(refreshed_order.cancellation_status, CancellationStatus.CANCELLED_NO_PAYMENT)
        self.assertIsNone(refreshed_order.reservation_expires_at)
        self.assertEqual(refreshed_tour.seats_available, 11)

    def test_lazy_expire_due_reservations_matches_service_behavior(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="LAZY-WRAP",
            seats_total=40,
            seats_available=8,
            status=TourStatus.OPEN_FOR_SALE,
        )
        point = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            point,
            seats_count=3,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        self.session.commit()

        n = lazy_expire_due_reservations(
            self.session,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        self.assertEqual(n, 1)
        refreshed_tour = self.session.get(type(tour), tour.id)
        assert refreshed_tour is not None
        self.assertEqual(refreshed_tour.seats_available, 11)

    def test_expire_due_reservations_skips_non_eligible_orders(self) -> None:
        user = self.create_user()
        tour = self.create_tour(code="EXP-2", seats_total=40, seats_available=5, status=TourStatus.OPEN_FOR_SALE)
        point = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        self.create_order(
            user,
            tour,
            point,
            seats_count=1,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
        )
        self.create_order(
            user,
            tour,
            point,
            seats_count=1,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 6, 0, tzinfo=UTC),
        )
        self.create_order(
            user,
            tour,
            point,
            seats_count=1,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=datetime(2026, 4, 1, 6, 0, tzinfo=UTC),
        )
        self.session.commit()

        expired_count = ReservationExpiryService().expire_due_reservations(
            self.session,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertEqual(expired_count, 0)
        refreshed_tour = self.session.get(type(tour), tour.id)
        assert refreshed_tour is not None
        self.assertEqual(refreshed_tour.seats_available, 5)

    def test_expire_due_reservations_is_idempotent(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="EXP-3",
            seats_total=40,
            seats_available=6,
            status=TourStatus.OPEN_FOR_SALE,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        self.session.commit()

        service = ReservationExpiryService()
        first_run = service.expire_due_reservations(
            self.session,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        second_run = service.expire_due_reservations(
            self.session,
            now=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
        )

        self.assertEqual(first_run, 1)
        self.assertEqual(second_run, 0)
        refreshed_order = self.session.get(type(order), order.id)
        refreshed_tour = self.session.get(type(tour), tour.id)
        assert refreshed_order is not None
        assert refreshed_tour is not None
        self.assertEqual(refreshed_order.cancellation_status, CancellationStatus.CANCELLED_NO_PAYMENT)
        self.assertEqual(refreshed_tour.seats_available, 8)

    def test_worker_run_once_delegates_to_expiry_service(self) -> None:
        with patch("app.workers.reservation_expiry.ReservationExpiryService") as service_cls:
            service_cls.return_value.expire_due_reservations.return_value = 2

            expired_count = run_once(now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC), limit=50)

        self.assertEqual(expired_count, 2)
        service_cls.return_value.expire_due_reservations.assert_called_once()
