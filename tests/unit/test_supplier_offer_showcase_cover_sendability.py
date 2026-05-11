"""B15C4: deterministic Telegram sendPhoto sendability for supplier-offer cover references."""

from __future__ import annotations

import unittest

from app.services.supplier_offer_showcase_cover_sendability import (
    is_raw_cover_reference_sendable_for_telegram_sendphoto,
    raw_cover_to_telegram_photo_send_argument,
)


class ShowcaseCoverSendabilityTests(unittest.TestCase):
    def test_telegram_photo_file_id_sendable(self) -> None:
        a = raw_cover_to_telegram_photo_send_argument("telegram_photo:AgACAgIAAxkBAA")
        self.assertEqual(a, "AgACAgIAAxkBAA")

    def test_direct_https_image_sendable(self) -> None:
        u = "https://cdn.example.com/promo/hero.jpg"
        self.assertEqual(raw_cover_to_telegram_photo_send_argument(u), u)
        self.assertTrue(is_raw_cover_reference_sendable_for_telegram_sendphoto(u))

    def test_google_share_not_sendable(self) -> None:
        u = "https://share.google/aslSRRhI6yMkRSuMV"
        self.assertIsNone(raw_cover_to_telegram_photo_send_argument(u))
        self.assertFalse(is_raw_cover_reference_sendable_for_telegram_sendphoto(u))

    def test_drive_google_not_sendable(self) -> None:
        u = "https://drive.google.com/file/d/abc/view"
        self.assertIsNone(raw_cover_to_telegram_photo_send_argument(u))


if __name__ == "__main__":
    unittest.main()
