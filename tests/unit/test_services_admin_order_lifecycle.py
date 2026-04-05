"""Unit tests for admin order lifecycle labels."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest import TestCase

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind, describe_order_admin_lifecycle


class DescribeOrderAdminLifecycleTests(TestCase):
    def test_expired_unpaid_hold_pattern(self) -> None:
        o = Order(
            id=1,
            user_id=1,
            tour_id=1,
            boarding_point_id=1,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
            total_amount=Decimal("10.00"),
            currency="EUR",
        )
        kind, summary = describe_order_admin_lifecycle(o)
        self.assertEqual(kind, AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD)
        self.assertIn("Not an active reservation", summary)

    def test_active_temporary_hold(self) -> None:
        o = Order(
            id=2,
            user_id=1,
            tour_id=1,
            boarding_point_id=1,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 6, 1, 12, 0, tzinfo=UTC),
            total_amount=Decimal("10.00"),
            currency="EUR",
        )
        kind, summary = describe_order_admin_lifecycle(o)
        self.assertEqual(kind, AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD)
        self.assertIn("payment pending", summary.lower())

    def test_confirmed_paid(self) -> None:
        o = Order(
            id=3,
            user_id=1,
            tour_id=1,
            boarding_point_id=1,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=None,
            total_amount=Decimal("10.00"),
            currency="EUR",
        )
        kind, _ = describe_order_admin_lifecycle(o)
        self.assertEqual(kind, AdminOrderLifecycleKind.CONFIRMED_PAID)
