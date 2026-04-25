"""Y36.6: admin Telegram custom request travel date display (read-only formatting)."""

from __future__ import annotations

import unittest
from datetime import date

from app.bot.handlers import admin_moderation
from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.enums import (
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
)
from app.services.custom_marketplace_request_service import (
    CustomMarketplaceRequestService,
)
from tests.unit.base import FoundationDBTestCase


class TestAdminRequestTravelDateFormat(unittest.TestCase):
    def test_start_only(self) -> None:
        s = date(2026, 4, 28)
        self.assertEqual(admin_moderation._format_admin_request_travel_dates(s, None), "2026-04-28")

    def test_start_equals_end_shows_one_date(self) -> None:
        s = date(2026, 4, 28)
        self.assertEqual(admin_moderation._format_admin_request_travel_dates(s, s), "2026-04-28")

    def test_range_uses_arrow(self) -> None:
        a = date(2026, 4, 28)
        b = date(2026, 4, 30)
        self.assertEqual(
            admin_moderation._format_admin_request_travel_dates(a, b),
            "2026-04-28 \u2192 2026-04-30",
        )

    def test_bad_distant_end_year_shows_honest_range(self) -> None:
        """If DB/seed has a far-future end year, show it; do not mutate."""
        a = date(2026, 4, 28)
        b = date(2926, 4, 28)
        self.assertEqual(
            admin_moderation._format_admin_request_travel_dates(a, b),
            "2026-04-28 \u2192 2926-04-28",
        )

    def test_start_missing_renders_dash(self) -> None:
        self.assertEqual(admin_moderation._format_admin_request_travel_dates(None, date(2026, 1, 1)), "-")


class TestAdminRequestTravelDateDetailIntegration(FoundationDBTestCase):
    def test_detail_equal_start_end_no_duplicate_date_in_line(self) -> None:
        u = self.create_user(telegram_user_id=353_601)
        row = CustomMarketplaceRequest(
            user_id=u.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 4, 28),
            travel_date_end=date(2026, 4, 28),
            route_notes="Same start end",
            group_size=2,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
        )
        self.session.add(row)
        self.session.commit()
        detail = CustomMarketplaceRequestService().get_admin_detail(self.session, request_id=row.id)
        text = admin_moderation._admin_ops_request_detail_text(
            "en",
            detail,
            viewer_telegram_user_id=990001,
        )
        low = text.lower()
        self.assertIn("travel date: 2026-04-28", low)
        self.assertNotIn("2026-04-28 - 2026-04-28", text)
        self.assertNotIn(f"2026-04-28 {chr(0x2192)} 2026-04-28", text)
