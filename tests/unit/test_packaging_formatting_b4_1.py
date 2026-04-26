"""B4.1: human-readable packaging formatting (deterministic path)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest import TestCase

from app.models.enums import SupplierOfferPaymentMode, TourSalesMode
from app.services.packaging_formatting import (
    build_telegram_post_draft,
    format_date_range_pretty,
    format_price_for_display,
    label_supplier_payment_mode,
    label_tour_sales_mode,
    format_departure_time_line,
    format_time_hhmm,
)
from app.services.supplier_offer_packaging_service import _as_snapshot, build_deterministic_draft
from tests.unit.base import FoundationDBTestCase

_ISO_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class PackagingFormattingUnitTests(TestCase):
    def test_date_range_pretty_no_iso_in_output(self) -> None:
        dep = datetime(2026, 5, 10, 7, 0, tzinfo=UTC)
        ret = datetime(2026, 5, 12, 18, 0, tzinfo=UTC)
        s = format_date_range_pretty(dep, ret)
        self.assertIn("May 2026", s)
        self.assertNotIn("T", s)
        self.assertNotIn("+00:00", s)
        self.assertIn("10", s)
        self.assertIn("12", s)

    def test_time_hhmm_readable(self) -> None:
        dt = datetime(2026, 3, 1, 7, 5, tzinfo=UTC)
        self.assertEqual(format_time_hhmm(dt), "07:05")
        self.assertIn("07:05", format_departure_time_line(dt))

    def test_price_trims_unnecessary_decimals(self) -> None:
        ph = "[missing]"
        self.assertEqual(
            format_price_for_display("2000.00", "RON", missing_placeholder=ph),
            "2000 RON",
        )
        self.assertEqual(
            format_price_for_display("199.5", "EUR", missing_placeholder=ph),
            "199.5 EUR",
        )

    def test_enum_labels_not_raw_snake_case(self) -> None:
        self.assertEqual(label_tour_sales_mode("per_seat"), "Per seat")
        self.assertEqual(label_tour_sales_mode("full_bus"), "Full bus")
        self.assertEqual(
            label_supplier_payment_mode("assisted_closure"),
            "Reservation / pay at boarding",
        )
        self.assertEqual(
            label_supplier_payment_mode("platform_checkout"),
            "Platform checkout",
        )

    def test_telegram_post_no_iso_and_has_readable_modes(self) -> None:
        dep = datetime(2026, 5, 10, 7, 0, tzinfo=UTC)
        ret = datetime(2026, 5, 12, 9, 0, tzinfo=UTC)
        text = build_telegram_post_draft(
            title="Trip",
            description="Nice",
            dep=dep,
            ret=ret,
            price_line="2000 RON",
            seats_line="28",
            sales_mode=TourSalesMode.FULL_BUS.value,
            payment_mode=SupplierOfferPaymentMode.ASSISTED_CLOSURE.value,
            route="Timișoara, Brașov, Sibiu",
            included="Water",
            excluded="Lunch",
        )
        self.assertIsNone(_ISO_INSTANT.search(text))
        self.assertIn("Full bus", text)
        self.assertIn("Reservation / pay at boarding", text)
        self.assertNotIn("full_bus", text)
        self.assertNotIn("assisted_closure", text)


class DeterministicDraftFormattingIntegrationTests(FoundationDBTestCase):
    def test_build_deterministic_telegram_excludes_iso_timestamps(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 7, 1, 6, 0, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        o = self.create_supplier_offer(
            s,
            title="B4 Trip",
            description="Scenic",
            program_text="Day 1: …",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=12,
            base_price=Decimal("199.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            included_text="Bus",
            excluded_text="Lunch",
            boarding_places_text="A, B, C",
        )
        self.session.commit()
        snap = _as_snapshot(o)
        d = build_deterministic_draft(snap, missing=[], warnings=[])
        t = (d.get("packaging_draft_extras") or {}).get("telegram_post_draft") or ""
        self.assertIsNone(_ISO_INSTANT.search(t), t)
        self.assertIn("1–3 July 2026", t)
        self.assertIn("Per seat", t)
        self.assertIn("Platform checkout", t)
        self.assertIn("A → B → C", t)


if __name__ == "__main__":
    import unittest

    unittest.main()
