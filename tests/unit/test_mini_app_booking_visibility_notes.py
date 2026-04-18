"""Track 5g.4d: booking detail context notes map facade states to copy (no raw enums)."""

from __future__ import annotations

import unittest

from app.schemas.mini_app import MiniAppBookingFacadeState
from mini_app.presentation_notes import booking_detail_context_note


class BookingVisibilityNotesTests(unittest.TestCase):
    def test_expired_facades_use_inactive_unpaid_note(self) -> None:
        for state in (
            MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION,
            MiniAppBookingFacadeState.CANCELLED_NO_PAYMENT,
        ):
            note = booking_detail_context_note("en", state).lower()
            self.assertIn("no longer active", note)
            self.assertNotIn("cancelled_no_payment", note)

    def test_confirmed_note_not_payment_pending(self) -> None:
        note = booking_detail_context_note("en", MiniAppBookingFacadeState.CONFIRMED).lower()
        self.assertIn("paid", note)
        self.assertNotIn("pay now", note)

    def test_other_facade_uses_generic_note(self) -> None:
        note = booking_detail_context_note("en", MiniAppBookingFacadeState.OTHER).lower()
        self.assertIn("status", note)
