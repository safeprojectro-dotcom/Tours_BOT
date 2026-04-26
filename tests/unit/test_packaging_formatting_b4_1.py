"""B4.1 / B4.2: human-readable and marketing-template packaging (deterministic)."""

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
    format_departure_time_line,
    format_time_hhmm,
    format_marketing_price_line_ro,
    format_discount_block_lines,
    label_supplier_payment_mode,
    label_tour_sales_mode,
)
from app.services.supplier_offer_packaging_service import _as_snapshot, build_deterministic_draft
from tests.unit.base import FoundationDBTestCase

_PH = "[missing]"

_ISO_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class PackagingFormattingUnitTests(TestCase):
    def test_date_range_pretty_no_iso_in_output(self) -> None:
        dep = datetime(2026, 5, 10, 7, 0, tzinfo=UTC)
        ret = datetime(2026, 5, 12, 18, 0, tzinfo=UTC)
        s = format_date_range_pretty(dep, ret)
        self.assertIn("May 2026", s)
        self.assertNotIn("T00:", s)
        self.assertNotIn("+00:00", s)
        self.assertIn("10", s)
        self.assertIn("12", s)

    def test_time_hhmm_readable(self) -> None:
        dt = datetime(2026, 3, 1, 7, 5, tzinfo=UTC)
        self.assertEqual(format_time_hhmm(dt), "07:05")
        self.assertIn("07:05", format_departure_time_line(dt))

    def test_price_trims_unnecessary_decimals(self) -> None:
        self.assertEqual(
            format_price_for_display("2000.00", "RON", missing_placeholder=_PH),
            "2000 RON",
        )
        self.assertEqual(
            format_price_for_display("199.5", "EUR", missing_placeholder=_PH),
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

    def test_telegram_post_no_iso_and_marketing_model_full_bus(self) -> None:
        dep = datetime(2026, 5, 10, 7, 0, tzinfo=UTC)
        ret = datetime(2026, 5, 12, 9, 0, tzinfo=UTC)
        text = build_telegram_post_draft(
            title="Trip",
            description="Nice",
            program_text="Day 1",
            transport_notes="Timisoara, Brasov, Sibiu",
            dep=dep,
            ret=ret,
            base_price="2000",
            currency="RON",
            sales_mode=TourSalesMode.FULL_BUS.value,
            payment_mode=SupplierOfferPaymentMode.ASSISTED_CLOSURE.value,
            vehicle_label="Coach 50",
            seats_total=50,
            discount_code="EARLY",
            discount_percent="10",
            discount_amount=None,
            discount_valid_until_iso=datetime(2026, 5, 20, 23, 0, tzinfo=UTC).isoformat(),
            included="Water",
            excluded="Lunch",
            missing_price_placeholder=_PH,
        )
        self.assertIsNone(_ISO_INSTANT.search(text))
        self.assertIn("tot autobuzul", text)
        self.assertIn("Rezervare exclusiva", text)
        self.assertIn("Cere oferta personalizata", text)
        self.assertIn("10", text)
        self.assertIn("pana la", text)
        self.assertIn("EARLY", text)
        self.assertNotIn("full_bus", text)
        self.assertNotIn("assisted_closure", text)
        self.assertIn("plata", text.lower())
        self.assertIn("Vanzare", text)

    def test_marketing_price_line_per_seat(self) -> None:
        s = format_marketing_price_line_ro("per_seat", "100", "EUR", missing_placeholder=_PH)
        self.assertIn("persoana", s)
        self.assertIn("100", s)

    def test_discount_block_lines(self) -> None:
        d0 = datetime(2026, 6, 1, 0, 0, tzinfo=UTC).isoformat()
        lines = format_discount_block_lines(
            "5",
            "20",
            "MYCODE",
            d0,
            currency="RON",
        )
        self.assertTrue(any("5%" in x for x in lines))
        self.assertTrue(any("20" in x and "reducere" in x for x in lines))
        self.assertIn("MYCODE", "\n".join(lines))


class DeterministicDraftFormattingIntegrationTests(FoundationDBTestCase):
    def test_route_from_description_not_boarding(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 7, 1, 6, 0, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        o = self.create_supplier_offer(
            s,
            title="B4 Trip",
            description="Timisoara, Brasov, Sibiu\n\nScenic",
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
            transport_notes="",
            boarding_places_text="WRONG, X, Y",
        )
        self.session.commit()
        snap = _as_snapshot(o)
        d = build_deterministic_draft(snap, missing=[], warnings=[])
        t = (d.get("packaging_draft_extras") or {}).get("telegram_post_draft") or ""
        self.assertIsNone(_ISO_INSTANT.search(t), t)
        self.assertIn("1–3 July 2026", t)
        self.assertIn("199 EUR / persoana", t)
        self.assertIn("Vanzare", t)
        self.assertIn("→", t)
        self.assertIn("Timisoara", t)
        self.assertNotIn("WRONG", t)
        self.assertIn("Locurile se confirma la rezervare", t)
        self.assertNotIn("disponibil", t.lower(), t)

    def test_full_bus_template_disclaimer(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(hours=8)
        o = self.create_supplier_offer(
            s,
            title="Charter",
            description="Ruta: A, B, C",
            program_text="Ziua 1",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=50,
            base_price=Decimal("1000.00"),
            currency="RON",
            sales_mode=TourSalesMode.FULL_BUS,
            transport_notes="",
            vehicle_label="Autocar 50",
        )
        self.session.commit()
        t = (build_deterministic_draft(_as_snapshot(o), missing=[], warnings=[]).get("packaging_draft_extras") or {}).get(
            "telegram_post_draft"
        ) or ""
        self.assertIn("1000 RON", t)
        self.assertIn("tot autobuzul", t)
        self.assertIn("Rezervare exclusiva", t)
        self.assertNotIn("Locurile se confirma la rezervare", t)


if __name__ == "__main__":
    import unittest

    unittest.main()
