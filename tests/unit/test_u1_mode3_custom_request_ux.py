"""U1: Mode 3 custom-request UX — prefill helpers and copy guardrails (no Flet)."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

from mini_app.custom_request_context import CustomRequestPrefill, prefill_from_reservation_preparation, prefill_from_tour_detail
from mini_app.ui_strings import shell


class U1Mode3CustomRequestUxTests(unittest.TestCase):
    def test_prefill_from_tour_detail_fills_dates_and_keeps_separate_request_semantics(self) -> None:
        tour = SimpleNamespace(
            code="CAT-1",
            departure_datetime=datetime(2026, 7, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 7, 12, 20, 0, tzinfo=UTC),
        )
        detail = SimpleNamespace(
            tour=tour,
            localized_content=SimpleNamespace(title="Alpine weekend", used_fallback=False),
        )
        p = prefill_from_tour_detail(detail)  # type: ignore[arg-type]
        self.assertIsInstance(p, CustomRequestPrefill)
        self.assertEqual(p.tour_code, "CAT-1")
        self.assertEqual(p.departure_date_iso, "2026-07-10")
        self.assertEqual(p.return_date_iso, "2026-07-12")
        self.assertEqual(p.source, "catalog_detail")
        en_banner = shell("en", "custom_request_prefill_banner", code=p.tour_code)
        self.assertIn("CAT-1", en_banner)
        self.assertIn("separate", en_banner.lower())

    def test_prefill_same_calendar_return_optional_end_date(self) -> None:
        d0 = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
        tour = SimpleNamespace(code="DAY", departure_datetime=d0, return_datetime=d0)
        detail = SimpleNamespace(
            tour=tour,
            localized_content=SimpleNamespace(title="Day trip", used_fallback=False),
        )
        p = prefill_from_tour_detail(detail)  # type: ignore[arg-type]
        self.assertEqual(p.return_date_iso, None)

    def test_prefill_from_preparation_matches_tour(self) -> None:
        tour = SimpleNamespace(
            code="PREP-9",
            departure_datetime=datetime(2026, 9, 1, 6, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 5, 22, 0, tzinfo=UTC),
            localized_content=SimpleNamespace(title="Coastal", used_fallback=False),
            id=1,
            base_price="100",
            currency="EUR",
            seats_available_snapshot=40,
        )
        prep = SimpleNamespace(
            tour=tour,
            boarding_points=[],
            seat_count_options=[1, 2],
            preparation_only=True,
            sales_mode_policy=SimpleNamespace(),
        )
        p = prefill_from_reservation_preparation(prep)  # type: ignore[arg-type]
        self.assertEqual(p.source, "catalog_prepare")
        self.assertEqual(p.tour_code, "PREP-9")

    def test_custom_request_intro_distinguishes_reservation_payment_waitlist(self) -> None:
        en = shell("en", "custom_request_intro").lower()
        self.assertTrue("not" in en or "no " in en)
        self.assertNotIn("confirmed booking", en)
        ro = shell("ro", "custom_request_intro").lower()
        self.assertTrue("nu e" in ro or "nu " in ro)
        self.assertNotIn("rezervare confirmat", ro)

    def test_my_requests_subtitle_separates_waitlist(self) -> None:
        en = shell("en", "my_requests_subtitle").lower()
        self.assertIn("waitlist", en)
        self.assertIn("catalog", en)
        ro = shell("ro", "my_requests_subtitle").lower()
        self.assertIn("catalog", ro)
        self.assertIn("list", ro)


if __name__ == "__main__":
    unittest.main()
