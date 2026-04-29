"""Deterministic content quality review (admin visibility only)."""

from __future__ import annotations

from decimal import Decimal

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.services.supplier_offer_content_quality_review import evaluate_content_quality_review
from tests.unit.base import FoundationDBTestCase


class SupplierOfferContentQualityReviewTests(FoundationDBTestCase):
    def test_detects_orphan_discount_code(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
            discount_code="Ura",
            discount_percent=None,
            discount_amount=None,
        )
        r = evaluate_content_quality_review(offer)
        codes = {w.code for w in r.warnings}
        self.assertIn("orphan_promo_code", codes)
        self.assertTrue(r.has_quality_warnings)

    def test_detects_thin_description_and_short_hook_issues(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            title="Trip X",
            description="Hi",
            short_hook="Trip X",
            marketing_summary="x" * 50,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        r = evaluate_content_quality_review(offer)
        codes = {w.code for w in r.warnings}
        self.assertIn("description_thin", codes)
        self.assertIn("short_hook_equals_title", codes)
        self.assertIn("marketing_summary_thin", codes)

    def test_empty_short_hook_skips_hook_specific_rules(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            title="Long enough title for tests here",
            description="y" * 120,
            short_hook=None,
            marketing_summary="z" * 200,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        r = evaluate_content_quality_review(offer)
        codes = {w.code for w in r.warnings}
        self.assertNotIn("short_hook_equals_title", codes)
        self.assertNotIn("short_hook_very_short", codes)
