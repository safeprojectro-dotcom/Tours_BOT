"""Track 5g.4c: Mode 2 Mini App presentation copy (no booking/payment logic)."""

from __future__ import annotations

import unittest

from app.models.enums import PaymentStatus
from mini_app.ui_strings import booking_facade_labels, payment_status_label, shell


class Mode2UxPolishCopyTests(unittest.TestCase):
    def test_reservation_hold_intro_keeps_backend_payment_truth(self) -> None:
        intro_en = shell("en", "reservation_hold_intro").lower()
        self.assertIn("pay now", intro_en)
        self.assertTrue(
            "server" in intro_en and "confirm" in intro_en,
            "hold intro should state payment is not final until server confirms",
        )

    def test_payment_pending_label_for_awaiting_status(self) -> None:
        label = payment_status_label("en", PaymentStatus.AWAITING_PAYMENT)
        self.assertEqual(label, "Payment pending")
        self.assertNotIn("awaiting_payment", label.lower())

    def test_active_hold_facade_lines_are_human_readable(self) -> None:
        booking, payment = booking_facade_labels("en", "active_temporary_reservation")
        self.assertNotIn("awaiting_payment", booking.lower())
        self.assertNotIn("awaiting_payment", payment.lower())
        self.assertIn("payment", payment.lower())
        self.assertIn("reserved", booking.lower())
