"""A3: supplier clarification drafts vs internal tasks (read-only)."""

from __future__ import annotations

from unittest import TestCase

from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead
from app.services.supplier_clarification_draft_service import SupplierClarificationDraftService


class SupplierClarificationDraftServiceTests(TestCase):
    def test_technical_requests_go_internal_ro_supplier_for_program(self) -> None:
        intake = SupplierOfferIntakeValidationRead(
            supplier_offer_id=7,
            headline="test",
            facts_missing_required=["preview_customer_body"],
            facts_weak_or_unclear=[],
            blocks_publication=["gate:media:media_review_replacement_requested"],
            blocks_catalog_conversion=["prepare_chain:blocked:ineligible"],
            suggested_supplier_requests=[
                "Wire payment instructions",
                "CTA target not verified.",
                "Hook is generic.",
            ],
        )
        d = SupplierClarificationDraftService.build_from_intake_validation(intake)
        self.assertEqual(d.draft_version, "a3_v1")
        self.assertEqual(d.supplier_offer_id, 7)
        supplier_joined = " ".join(d.supplier_facing_asks).lower()
        self.assertIn("programul", supplier_joined)
        self.assertNotIn("prepare_chain", supplier_joined)
        self.assertNotIn("cta", supplier_joined)
        self.assertNotIn("wire payment", supplier_joined)
        internal_joined = " ".join(d.internal_admin_tasks).lower()
        self.assertIn("prepare_chain", internal_joined)
        self.assertIn("gate:", internal_joined)

    def test_packaging_weak_adds_internal_row_and_simple_supplier_line(self) -> None:
        intake = SupplierOfferIntakeValidationRead(
            supplier_offer_id=1,
            headline="x",
            facts_missing_required=[],
            facts_weak_or_unclear=["packaging:needs_admin_review"],
            blocks_publication=[],
            blocks_catalog_conversion=[],
            suggested_supplier_requests=[],
        )
        d = SupplierClarificationDraftService.build_from_intake_validation(intake)
        self.assertTrue(any("packaging:" in x for x in d.internal_admin_tasks))
        self.assertTrue(any("descrierea" in x.lower() for x in d.supplier_facing_asks))
