"""B12A: showcase marketing template library — inference, packaging JSON, preview helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.enums import (
    ShowcaseMarketingTemplateId,
    SupplierOfferPaymentMode,
    SupplierServiceComposition,
    TourSalesMode,
)
from app.services.showcase_marketing_template_library import (
    build_preview_fact_lines_for_template,
    build_showcase_marketing_template_library_v1,
    early_bird_grounded,
    infer_showcase_marketing_template,
    last_seats_urgent_allowed,
    merge_showcase_marketing_template_library_v1,
    resolve_effective_showcase_marketing_template,
)
from tests.unit.base import FoundationDBTestCase


class ShowcaseMarketingTemplateLibraryTests(FoundationDBTestCase):
    def test_infer_per_seat_standard(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
        )
        self.assertIs(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.PER_SEAT_STANDARD)

    def test_infer_full_bus(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 2, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.assertIs(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.FULL_BUS_PRIVATE_GROUP)

    def test_infer_early_bird_when_discount_and_deadline(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 3, 8, 0, tzinfo=UTC)
        deadline = dep - timedelta(days=10)
        offer = self.create_supplier_offer(
            sup,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
            discount_percent=Decimal("10"),
            discount_valid_until=deadline,
            discount_code="EARLY",
        )
        self.assertTrue(early_bird_grounded(offer))
        self.assertIs(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.EARLY_BIRD_DISCOUNT)

    def test_infer_custom_request_cta_for_assisted_closure(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.ASSISTED_CLOSURE,
            service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
        )
        self.assertIs(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.CUSTOM_REQUEST_CTA)

    def test_early_bird_wins_over_assisted_and_service_promo(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 5, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.ASSISTED_CLOSURE,
            service_composition=SupplierServiceComposition.TRANSPORT_GUIDE,
            discount_amount=Decimal("25"),
            discount_valid_until=dep - timedelta(days=5),
        )
        self.assertIs(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.EARLY_BIRD_DISCOUNT)

    def test_infer_supplier_service_promo(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 6, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            service_composition=SupplierServiceComposition.TRANSPORT_WATER,
        )
        self.assertIs(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.SUPPLIER_SERVICE_PROMO)

    def test_last_seats_not_inferred_and_gated(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 7, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(sup, departure_datetime=dep, return_datetime=dep + timedelta(days=1))
        self.assertIsNot(infer_showcase_marketing_template(offer), ShowcaseMarketingTemplateId.LAST_SEATS_URGENT)
        self.assertFalse(last_seats_urgent_allowed(live_seats_remaining=None))
        self.assertFalse(last_seats_urgent_allowed(live_seats_remaining=0))
        self.assertTrue(last_seats_urgent_allowed(live_seats_remaining=3))

    def test_merge_preserves_admin_selection_on_regenerate(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 8, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(sup, departure_datetime=dep, return_datetime=dep + timedelta(days=1))
        offer.packaging_draft_json = {
            "telegram_post_draft": "x",
            "showcase_marketing_template_library_v1": {
                "schema_version": 1,
                "inferred_template_id": "per_seat_standard",
                "admin_selected_template_id": "short_announcement",
                "admin_selected_at": "2026-01-01T00:00:00+00:00",
            },
        }
        extras: dict = {"telegram_post_draft": "y"}
        merge_showcase_marketing_template_library_v1(extras, offer)
        block = extras["showcase_marketing_template_library_v1"]
        self.assertEqual(block.get("admin_selected_template_id"), "short_announcement")
        self.assertEqual(block.get("admin_selected_at"), "2026-01-01T00:00:00+00:00")
        self.assertEqual(block.get("inferred_template_id"), ShowcaseMarketingTemplateId.PER_SEAT_STANDARD.value)

    def test_resolve_effective_last_seats_without_verified_seats_falls_back(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(sup, departure_datetime=dep, return_datetime=dep + timedelta(days=1))
        offer.packaging_draft_json = {
            "showcase_marketing_template_library_v1": {
                "admin_selected_template_id": ShowcaseMarketingTemplateId.LAST_SEATS_URGENT.value,
            }
        }
        eff, _sel, notes = resolve_effective_showcase_marketing_template(offer)
        self.assertIs(eff, ShowcaseMarketingTemplateId.PER_SEAT_STANDARD)
        self.assertIn("last_seats_urgent_requires_positive_verified_live_seats_remaining", notes)

    def test_packaging_merge_adds_v1_block(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 8, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(sup, departure_datetime=dep, return_datetime=dep + timedelta(days=1))
        extras: dict = {"telegram_post_draft": "x"}
        merge_showcase_marketing_template_library_v1(extras, offer)
        self.assertIn("showcase_marketing_template_library_v1", extras)
        block = extras["showcase_marketing_template_library_v1"]
        self.assertEqual(block.get("schema_version"), 1)
        self.assertEqual(block.get("inferred_template_id"), ShowcaseMarketingTemplateId.PER_SEAT_STANDARD.value)
        self.assertIn("blocked_auto_inference", block)

    def test_library_record_includes_early_bird_supplement(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 9, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            title="Promo Trip",
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
            discount_percent=Decimal("15"),
            discount_valid_until=dep - timedelta(days=2),
            currency="EUR",
        )
        block = build_showcase_marketing_template_library_v1(offer)
        self.assertEqual(block["inferred_template_id"], ShowcaseMarketingTemplateId.EARLY_BIRD_DISCOUNT.value)
        lines = block.get("safe_supplemental_lines_ro") or []
        self.assertTrue(lines)
        self.assertIn("15%", lines[0])
        self.assertIn("septembrie", lines[0].lower())

    def test_preview_short_announcement_truncates(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            sup,
            title="Long Trip",
            description="D1\nD2\nD3",
            program_text="a\nb\nc\nd\ne",
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=3),
            seats_total=20,
            base_price=Decimal("100"),
            currency="EUR",
        )
        lines = build_preview_fact_lines_for_template(offer, ShowcaseMarketingTemplateId.SHORT_ANNOUNCEMENT)
        self.assertLessEqual(len(lines), 13)

    def test_preview_last_seats_requires_gate(self) -> None:
        sup = self.create_supplier()
        dep = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(sup, departure_datetime=dep, return_datetime=dep + timedelta(days=1))
        without = build_preview_fact_lines_for_template(
            offer, ShowcaseMarketingTemplateId.LAST_SEATS_URGENT, live_seats_remaining=None
        )
        with_seats = build_preview_fact_lines_for_template(
            offer, ShowcaseMarketingTemplateId.LAST_SEATS_URGENT, live_seats_remaining=4
        )
        self.assertEqual(len(without), len(build_preview_fact_lines_for_template(offer, ShowcaseMarketingTemplateId.PER_SEAT_STANDARD)))
        self.assertTrue(any("Locuri disponibile" in ln for ln in with_seats))
