from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.schemas.mini_app import MiniAppBookingFacadeState, MiniAppBookingPrimaryCta
from app.schemas.order import OrderRead
from app.services.mini_app_booking_facade import (
    format_payment_session_hint,
    resolve_mini_app_booking_facade,
)


def _order(**kwargs) -> OrderRead:
    base = dict(
        id=1,
        user_id=10,
        tour_id=20,
        boarding_point_id=30,
        seats_count=2,
        booking_status=BookingStatus.RESERVED,
        payment_status=PaymentStatus.AWAITING_PAYMENT,
        cancellation_status=CancellationStatus.ACTIVE,
        reservation_expires_at=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        total_amount=Decimal("100.00"),
        currency="EUR",
        source_channel="mini_app",
        assigned_operator_id=None,
        created_at=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
    )
    base.update(kwargs)
    return OrderRead.model_validate(base)


class MiniAppBookingFacadeTests(unittest.TestCase):
    def test_active_temporary_reservation_future_expiry(self) -> None:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        o = _order(reservation_expires_at=now + timedelta(hours=2))
        b, p, state, cta = resolve_mini_app_booking_facade(o, now=now)
        self.assertEqual(state, MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION)
        self.assertEqual(cta, MiniAppBookingPrimaryCta.PAY_NOW)
        self.assertIn("Reserved temporarily", b)
        self.assertIn("Payment pending", p)
        self.assertNotIn("awaiting_payment", b.lower())
        self.assertNotIn("awaiting_payment", p.lower())

    def test_expired_temporary_reservation_before_worker(self) -> None:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        o = _order(reservation_expires_at=now - timedelta(minutes=1))
        b, p, state, cta = resolve_mini_app_booking_facade(o, now=now)
        self.assertEqual(state, MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION)
        self.assertEqual(cta, MiniAppBookingPrimaryCta.BROWSE_TOURS)
        self.assertIn("expired", b.lower())
        self.assertNotIn("cancelled_no_payment", b.lower())

    def test_cancelled_no_payment_after_worker(self) -> None:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        o = _order(
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        b, p, state, cta = resolve_mini_app_booking_facade(o, now=now)
        self.assertEqual(state, MiniAppBookingFacadeState.CANCELLED_NO_PAYMENT)
        self.assertEqual(cta, MiniAppBookingPrimaryCta.BROWSE_TOURS)
        self.assertIn("expired", b.lower())
        self.assertNotIn("cancelled_no_payment", b.lower())

    def test_confirmed_paid(self) -> None:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        o = _order(
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            reservation_expires_at=None,
        )
        _, _, state, cta = resolve_mini_app_booking_facade(o, now=now)
        self.assertEqual(state, MiniAppBookingFacadeState.CONFIRMED)
        self.assertEqual(cta, MiniAppBookingPrimaryCta.BACK_TO_BOOKINGS)

    def test_payment_session_hint_humanizes_status(self) -> None:
        hint = format_payment_session_hint(status=PaymentStatus.AWAITING_PAYMENT, provider="mockpay")
        self.assertIn("Payment pending", hint)
        self.assertNotIn("awaiting_payment", hint.lower())
