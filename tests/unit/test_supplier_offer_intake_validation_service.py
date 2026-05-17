"""A2: supplier intake validation from publishing console rows (read-only)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from app.schemas.admin_publish_readiness import AdminPublishReadinessRead
from app.schemas.admin_publishing_console import (
    AdminPublishingConsoleItemRead,
    AdminPublishingConsoleOfferDebugRead,
    AdminPublishingConsolePreviewPayloadRead,
    AdminPublishingConsolePreviewRead,
    AdminPublishingConsoleTemplateLibraryRead,
    AdminPublishingConsoleTourDebugRead,
    AdminPublishingConsoleUiCardRead,
)
from app.services.supplier_offer_intake_validation_service import SupplierOfferIntakeValidationService


class SupplierOfferIntakeValidationServiceTests(TestCase):
    def _ui(self) -> AdminPublishingConsoleUiCardRead:
        return AdminPublishingConsoleUiCardRead(
            status_badge="blocked",
            status_label="Blocked",
            status_tone="danger",
            safety_line="Read-only.",
        )

    def _base_pr(self, **kwargs: object) -> AdminPublishReadinessRead:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        data = {
            "status": "blocked",
            "recommended_action": "review",
            "gates_passed_count": 0,
            "gates_failed_count": 0,
            "gates_warning_count": 0,
            "gates": [],
            "can_suggest_manual_publish": False,
            "generated_at": now,
            "summary": "blocked",
            "badge": "blocked",
            "gate_summary": "0/0",
        }
        data.update(kwargs)
        return AdminPublishReadinessRead(**data)

    def _minimal_supplier_item(self, **overrides: object) -> AdminPublishingConsoleItemRead:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        pr = self._base_pr()
        cp = AdminPublishingConsolePreviewRead(
            preview_status="placeholder",
            template_family="supplier_offer_showcase",
            safety_note="n",
        )
        tl = AdminPublishingConsoleTemplateLibraryRead(
            family="supplier_offer_showcase",
            safety_note="n",
        )
        pp = AdminPublishingConsolePreviewPayloadRead(
            payload_status="placeholder",
            source="supplier_offer_fields",
            body_text="x" * 50,
            primary_cta_url="https://example.test/cta",
            safety_note="n",
        )
        base = dict(
            candidate_key="supplier_offer:42",
            kind="supplier_offer_initial",
            console_status="blocked",
            title="Weekend coach tour",
            subtitle="Sat–Sun",
            target_summary="supplier_offer · bridge",
            next_best_action=None,
            blocked_reasons=[],
            human_summary="Human summary text.",
            review_package_path="/admin/supplier-offers/42/review-package",
            publish_readiness=pr,
            console_preview=cp,
            template_library=tl,
            preview_payload=pp,
            offer_debug=AdminPublishingConsoleOfferDebugRead(
                supplier_offer_id=42,
                lifecycle_status="ready_for_moderation",
                packaging_status="approved_for_publish",
                can_publish_now=False,
                next_missing_step="Wire payment instructions",
            ),
            tour_debug=None,
            ui_card=self._ui(),
        )
        base.update(overrides)
        return AdminPublishingConsoleItemRead(**base)

    def test_none_for_tour_promotion(self) -> None:
        item = self._minimal_supplier_item(
            kind="tour_promotion",
            candidate_key="tour:9",
            tour_debug=AdminPublishingConsoleTourDebugRead(
                tour_id=9,
                tour_code="T9",
                tour_status="active",
                sales_mode="per_seat",
                seats_available=10,
                seats_total=40,
                catalog_customer_visible=True,
            ),
            offer_debug=None,
        )
        self.assertIsNone(SupplierOfferIntakeValidationService.build_from_console_item(item))

    def test_supplier_offer_tracks_missing_body_and_merges_signals(self) -> None:
        pr = self._base_pr(primary_blocker="Cover photo pending review.")
        pp = AdminPublishingConsolePreviewPayloadRead(
            payload_status="blocked",
            source="supplier_offer_fields",
            body_text="tooshort",
            blockers=["CTA target not verified."],
            warnings=["Hook is generic."],
            safety_note="n",
        )
        item = self._minimal_supplier_item(publish_readiness=pr, preview_payload=pp)
        v = SupplierOfferIntakeValidationService.build_from_console_item(item)
        self.assertIsNotNone(v)
        assert v is not None
        self.assertEqual(v.supplier_offer_id, 42)
        self.assertIn("preview_customer_body", v.facts_missing_required)
        self.assertIn("preview_warning:Hook is generic.", v.facts_weak_or_unclear)
        self.assertTrue(any("Cover photo pending" in x for x in v.blocks_publication))
        self.assertTrue(any("CTA target" in x for x in v.blocks_publication))
        self.assertIn("Wire payment instructions", v.suggested_supplier_requests)

