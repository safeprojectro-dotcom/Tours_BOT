"""Track 5g.3: Mini App catalog charter (Mode 2) copy must not read as RFQ (Mode 3)."""

from __future__ import annotations

import unittest

from mini_app.ui_strings import shell

_MODE2_KEYS = (
    "catalog_card_assisted_notice",
    "detail_assisted_booking_title",
    "detail_assisted_booking_body",
    "btn_request_full_bus_assistance",
    "preparation_assisted_title",
    "preparation_assisted_body",
)

# Phrases that imply Mode 3 / marketplace RFQ — must not appear in Mode 2 catalog-charter strings (English).
_MODE2_FORBIDDEN_EN_SUBSTRINGS = (
    "suppliers",
    "supplier bidding",
    "request offers",
    "rfq",
    "structured assistance request",
    "custom trip request",
)


class Track5G3CatalogCharterCopyTests(unittest.TestCase):
    def test_mode2_en_uses_catalog_charter_framing(self) -> None:
        for key in _MODE2_KEYS:
            text = shell("en", key).lower()
            self.assertTrue(
                "catalog" in text or "charter" in text or "listing" in text,
                f"{key} should mention catalog/charter/listing framing",
            )

    def test_mode2_en_avoids_rfq_leakage(self) -> None:
        for key in _MODE2_KEYS:
            lower = shell("en", key).lower()
            for bad in _MODE2_FORBIDDEN_EN_SUBSTRINGS:
                self.assertNotIn(bad, lower, f"{key} must not imply RFQ: found {bad!r}")

    def test_mode2_ro_uses_catalog_charter_framing(self) -> None:
        for key in _MODE2_KEYS:
            text = shell("ro", key).lower()
            self.assertTrue(
                "catalog" in text or "charter" in text or "ofert" in text,
                f"{key} (ro) should mention catalog/charter or listing (ofertă)",
            )

    def test_mode3_en_strings_unchanged_rfq_semantics(self) -> None:
        intro = shell("en", "custom_request_intro").lower()
        self.assertIn("suppliers", intro)
        self.assertIn("request", intro)
        bridge = shell("en", "rfq_bridge_intro").lower()
        self.assertTrue("custom" in bridge or "request" in bridge, bridge)

