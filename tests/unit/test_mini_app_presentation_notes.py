from __future__ import annotations

import unittest

from app.schemas.mini_app import MiniAppBookingFacadeState
from mini_app.presentation_notes import booking_detail_context_note


class PresentationNotesTests(unittest.TestCase):
    def test_maps_facade_to_distinct_prefix(self) -> None:
        a = booking_detail_context_note("en", MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION)
        c = booking_detail_context_note("en", MiniAppBookingFacadeState.CONFIRMED)
        h = booking_detail_context_note("en", MiniAppBookingFacadeState.CANCELLED_NO_PAYMENT)
        self.assertNotEqual(a, c)
        self.assertNotEqual(c, h)
        self.assertIn("pay", a.lower())
        self.assertIn("paid", c.lower())
        self.assertIn("hold", h.lower())


if __name__ == "__main__":
    unittest.main()
