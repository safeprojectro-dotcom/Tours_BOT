"""Unit tests for supplier-offer deep links (bot /start, Mini App URLs, B15C1 channel startapp)."""

from __future__ import annotations

import unittest

from app.services.supplier_offer_deep_link import (
    mini_app_tour_channel_startapp_url,
    mini_app_tour_detail_url,
    normalize_telegram_mini_app_short_name_for_url,
)


class SupplierOfferDeepLinkTests(unittest.TestCase):
    def test_mini_app_tour_channel_startapp_url(self) -> None:
        u = mini_app_tour_channel_startapp_url(bot_username="@DemoBot", tour_code="B10-SO13-e9f389")
        self.assertEqual(u, "https://t.me/DemoBot?startapp=tour_B10-SO13-e9f389")

    def test_mini_app_tour_channel_startapp_url_with_short_name_b15c5(self) -> None:
        u = mini_app_tour_channel_startapp_url(
            bot_username="previewbot",
            tour_code="B10-X-1",
            mini_app_short_name="appshort",
        )
        self.assertEqual(u, "https://t.me/previewbot/appshort?startapp=tour_B10-X-1")

    def test_mini_app_tour_channel_startapp_rejects_bad_bot_username(self) -> None:
        with self.assertRaises(ValueError):
            mini_app_tour_channel_startapp_url(bot_username="evil/bot", tour_code="ABC")

    def test_mini_app_tour_channel_startapp_rejects_bad_short_name(self) -> None:
        with self.assertRaises(ValueError):
            mini_app_tour_channel_startapp_url(
                bot_username="b",
                tour_code="OK-1",
                mini_app_short_name="has/slash",
            )

    def test_normalize_short_name_rejects_injection_and_returns_none(self) -> None:
        self.assertIsNone(normalize_telegram_mini_app_short_name_for_url(None))
        self.assertIsNone(normalize_telegram_mini_app_short_name_for_url("   "))
        self.assertIsNone(normalize_telegram_mini_app_short_name_for_url("bad?name"))
        self.assertIsNone(normalize_telegram_mini_app_short_name_for_url("a/b"))
        self.assertEqual(normalize_telegram_mini_app_short_name_for_url("banattours"), "banattours")

    def test_mini_app_tour_detail_url_unchanged(self) -> None:
        self.assertEqual(
            mini_app_tour_detail_url(mini_app_url="https://h.example/x/", tour_code="ABC-1"),
            "https://h.example/x/tours/ABC-1",
        )


if __name__ == "__main__":
    unittest.main()
