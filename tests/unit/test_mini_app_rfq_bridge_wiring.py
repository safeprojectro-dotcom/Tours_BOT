"""Track 5c: Mini App RFQ bridge wiring — pure CTA gating (no Flet)."""

from __future__ import annotations

import unittest

from mini_app.rfq_bridge_logic import rfq_bridge_continue_to_payment_allowed


class RfqBridgeWiringTests(unittest.TestCase):
    def test_continue_payment_requires_hold_and_eligibility(self) -> None:
        self.assertTrue(
            rfq_bridge_continue_to_payment_allowed(hold_active=True, payment_entry_allowed=True)
        )
        self.assertFalse(
            rfq_bridge_continue_to_payment_allowed(hold_active=True, payment_entry_allowed=False)
        )
        self.assertFalse(
            rfq_bridge_continue_to_payment_allowed(hold_active=False, payment_entry_allowed=True)
        )
        self.assertFalse(
            rfq_bridge_continue_to_payment_allowed(hold_active=False, payment_entry_allowed=False)
        )


if __name__ == "__main__":
    unittest.main()
