"""Unit tests for supplier-offer deep links (bot /start, Mini App URLs, B15C1 channel startapp)."""

from __future__ import annotations

import unittest

from app.services.supplier_offer_deep_link import (
    mini_app_tour_channel_startapp_url,
    mini_app_tour_detail_url,
)


class SupplierOfferDeepLinkTests(unittest.TestCase):
    def test_mini_app_tour_channel_startapp_url(self) -> None:
        u = mini_app_tour_channel_startapp_url(bot_username="@DemoBot", tour_code="B10-SO13-e9f389")
        self.assertEqual(u, "https://t.me/DemoBot?startapp=tour_B10-SO13-e9f389")

    def test_mini_app_tour_channel_startapp_rejects_bad_tour_code(self) -> None:
        with self.assertRaises(ValueError):
            mini_app_tour_channel_startapp_url(bot_username="b", tour_code="has/slash")

    def test_mini_app_tour_detail_url_unchanged(self) -> None:
        self.assertEqual(
            mini_app_tour_detail_url(mini_app_url="https://h.example/x/", tour_code="ABC-1"),
            "https://h.example/x/tours/ABC-1",
        )


if __name__ == "__main__":
    unittest.main()
