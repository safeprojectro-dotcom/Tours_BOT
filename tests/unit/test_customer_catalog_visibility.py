"""Unit tests for customer-facing catalog time-window visibility (read-side)."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible


class CustomerCatalogVisibilityTests(unittest.TestCase):
    def test_visible_when_departure_future_and_no_sales_deadline(self) -> None:
        ref = datetime(2026, 4, 17, 12, 0, tzinfo=UTC)
        self.assertTrue(
            tour_is_customer_catalog_visible(
                departure_datetime=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
                sales_deadline=None,
                now=ref,
            )
        )

    def test_hidden_when_departure_in_past(self) -> None:
        ref = datetime(2026, 4, 17, 12, 0, tzinfo=UTC)
        self.assertFalse(
            tour_is_customer_catalog_visible(
                departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
                sales_deadline=None,
                now=ref,
            )
        )

    def test_hidden_when_sales_deadline_in_past_even_if_departure_future(self) -> None:
        ref = datetime(2026, 4, 17, 12, 0, tzinfo=UTC)
        self.assertFalse(
            tour_is_customer_catalog_visible(
                departure_datetime=datetime(2026, 12, 1, 8, 0, tzinfo=UTC),
                sales_deadline=datetime(2026, 4, 1, 23, 0, tzinfo=UTC),
                now=ref,
            )
        )
