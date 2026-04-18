"""Track 5g.5: Mode 2 -> Mode 3 custom-request CTA copy (no RFQ-as-Mode-2 framing)."""

from __future__ import annotations

import unittest

from mini_app.ui_strings import shell

_5G5_KEYS = (
    "mode2_custom_trip_hint",
    "btn_mode2_request_custom_trip",
    "nav_custom_trip",
)

_FORBIDDEN = ("rfq", "request for quote")


class Track5G5Mode2CustomTripCopyTests(unittest.TestCase):
    def test_mode2_custom_trip_strings_avoid_rfq_token(self) -> None:
        for lang in ("en", "ro"):
            for key in _5G5_KEYS:
                text = shell(lang, key).lower()
                for bad in _FORBIDDEN:
                    self.assertNotIn(bad, text, f"{lang}/{key} must not use RFQ shorthand")

    def test_hint_preserves_catalog_vs_custom_separation(self) -> None:
        for lang in ("en", "ro"):
            hint = shell(lang, "mode2_custom_trip_hint").lower()
            self.assertTrue(
                "catalog" in hint or "charter" in hint or "catalogului" in hint,
                f"{lang}: should anchor ready-made catalog/charter offer",
            )
            self.assertTrue(
                "separate" in hint or "separat" in hint,
                f"{lang}: should state custom path is distinct from this listing",
            )
            self.assertNotIn("waitlist", hint)

    def test_nav_custom_trip_global_label_semantics(self) -> None:
        """Track 5g.5b: shell label must not collapse catalog, waitlist, or RFQ shorthand."""
        for lang in ("en", "ro"):
            text = shell(lang, "nav_custom_trip").lower()
            for bad in _FORBIDDEN:
                self.assertNotIn(bad, text, f"{lang}/nav_custom_trip must not use RFQ shorthand")
            self.assertNotIn("waitlist", text)
            self.assertNotIn("lista de așteptare", text)
            self.assertNotIn("lista de asteptare", text)
