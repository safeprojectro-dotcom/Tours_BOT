"""A6A: catalog / conversion readiness projection (read-only)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase

from app.schemas.admin_publish_readiness import AdminPublishReadinessRead
from app.schemas.admin_publishing_console import (
    AdminPublishingConsoleItemRead,
    AdminPublishingConsoleOfferDebugRead,
    AdminPublishingConsolePreviewPayloadRead,
    AdminPublishingConsolePreviewRead,
    AdminPublishingConsoleSupplierOfferConversionSummaryRead,
    AdminPublishingConsoleSupplierOfferDetailRead,
    AdminPublishingConsoleSupplierOfferLinkedTourSummaryRead,
    AdminPublishingConsoleSupplierOfferPublicationSummaryRead,
    AdminPublishingConsoleSupplierOfferSafetySummaryRead,
    AdminPublishingConsoleTemplateLibraryRead,
    AdminPublishingConsoleTourDebugRead,
    AdminPublishingConsoleUiCardRead,
)
from app.bot.constants import ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX
from app.services.supplier_offer_catalog_conversion_readiness_service import (
    CatalogConversionReadinessContext,
    SupplierOfferCatalogConversionReadinessService,
)


class SupplierOfferCatalogConversionReadinessServiceTests(TestCase):
    def _ui(self) -> AdminPublishingConsoleUiCardRead:
        return AdminPublishingConsoleUiCardRead(
            status_badge="ready",
            status_label="Ready",
            status_tone="success",
            safety_line="Read-only.",
        )

    def _base_pr(self, **kwargs: object) -> AdminPublishReadinessRead:
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        data = {
            "status": "needs_review",
            "recommended_action": "review",
            "gates_passed_count": 0,
            "gates_failed_count": 0,
            "gates_warning_count": 0,
            "gates": [],
            "can_suggest_manual_publish": False,
            "generated_at": now,
            "summary": "needs_review",
            "badge": "needs_review",
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
            console_status="ready",
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
            cta_safety_status="not_applicable",
            conversion_target_kind="none",
        )
        base.update(overrides)
        return AdminPublishingConsoleItemRead(**base)

    def test_none_for_tour_promotion(self) -> None:
        item = self._minimal_supplier_item(
            kind="tour_promotion",
            candidate_key="tour:9",
            offer_debug=None,
            tour_debug=AdminPublishingConsoleTourDebugRead(
                tour_id=9,
                tour_code="T9",
                tour_status="active",
                sales_mode="per_seat",
                seats_available=10,
                seats_total=40,
                catalog_customer_visible=True,
            ),
        )
        self.assertIsNone(SupplierOfferCatalogConversionReadinessService.build_from_console_item(item))

    def test_needs_preparation_missing_execution_link(self) -> None:
        item = self._minimal_supplier_item(
            console_status="needs_attention",
            cta_safety_status="missing_execution_link",
            conversion_target_kind="exact_tour",
            prepare_conversion_chain_plan_status="partial",
        )
        r = SupplierOfferCatalogConversionReadinessService.build_from_console_item(item)
        assert r is not None
        self.assertEqual(r.version, "a6a_v1")
        self.assertEqual(r.readiness_status, "needs_internal_preparation")
        self.assertEqual(r.status_label_message_key, "admin_a6a_status_needs_preparation")
        self.assertEqual(r.main_blocker_message_key, "admin_a6a_blocker_offer_tour_link")
        self.assertFalse(r.mini_app_cta_safe)
        self.assertEqual(len(r.guided_actions), 1)
        self.assertEqual(
            r.guided_actions[0].callback_data,
            f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}42",
        )
        self.assertIsNone(r.guided_actions[0].url)

    def test_ready_for_review_with_detail(self) -> None:
        item = self._minimal_supplier_item(
            cta_safety_status="exact_tour_ready",
            conversion_target_kind="exact_tour",
            prepare_conversion_chain_plan_status="already_prepared",
        )
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        safety = AdminPublishingConsoleSupplierOfferSafetySummaryRead(note="n")
        detail = AdminPublishingConsoleSupplierOfferDetailRead(
            supplier_offer_id=42,
            candidate_key="supplier_offer:42",
            console_status="ready",
            review_package_path="/rp",
            publish_readiness=self._base_pr(),
            console_preview=item.console_preview,
            template_library=item.template_library,
            preview_payload=item.preview_payload,
            conversion_summary=AdminPublishingConsoleSupplierOfferConversionSummaryRead(
                has_tour_bridge=True,
                has_catalog_visible_tour=True,
                has_active_execution_link=True,
            ),
            linked_tour_summary=AdminPublishingConsoleSupplierOfferLinkedTourSummaryRead(),
            publication_summary=AdminPublishingConsoleSupplierOfferPublicationSummaryRead(
                lifecycle_status="approved",
                published_at=None,
                showcase_chat_id=None,
                showcase_message_id=None,
                already_published=False,
            ),
            safety_summary=safety,
            generated_at=now,
        )
        r = SupplierOfferCatalogConversionReadinessService.build_from_console_item(
            item,
            detail=detail,
            context=CatalogConversionReadinessContext(mini_app_open_url="https://mini.example/app"),
        )
        assert r is not None
        self.assertEqual(r.readiness_status, "ready_for_review")
        self.assertEqual(r.status_label_message_key, "admin_a6a_status_ready_for_review")
        self.assertIsNone(r.main_blocker_message_key)
        self.assertTrue(r.mini_app_cta_safe)
        self.assertTrue(r.has_tour_link)
        self.assertEqual(len(r.guided_actions), 2)
        self.assertEqual(r.guided_actions[0].callback_data, f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}42")
        self.assertEqual(r.guided_actions[1].url, "https://mini.example/app")

    def test_ready_for_review_single_button_without_mini_app_url(self) -> None:
        item = self._minimal_supplier_item(
            cta_safety_status="exact_tour_ready",
            conversion_target_kind="exact_tour",
            prepare_conversion_chain_plan_status="already_prepared",
        )
        now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        safety = AdminPublishingConsoleSupplierOfferSafetySummaryRead(note="n")
        detail = AdminPublishingConsoleSupplierOfferDetailRead(
            supplier_offer_id=42,
            candidate_key="supplier_offer:42",
            console_status="ready",
            review_package_path="/rp",
            publish_readiness=self._base_pr(),
            console_preview=item.console_preview,
            template_library=item.template_library,
            preview_payload=item.preview_payload,
            conversion_summary=AdminPublishingConsoleSupplierOfferConversionSummaryRead(
                has_tour_bridge=True,
                has_catalog_visible_tour=True,
                has_active_execution_link=True,
            ),
            linked_tour_summary=AdminPublishingConsoleSupplierOfferLinkedTourSummaryRead(),
            publication_summary=AdminPublishingConsoleSupplierOfferPublicationSummaryRead(
                lifecycle_status="approved",
                published_at=None,
                showcase_chat_id=None,
                showcase_message_id=None,
                already_published=False,
            ),
            safety_summary=safety,
            generated_at=now,
        )
        r = SupplierOfferCatalogConversionReadinessService.build_from_console_item(
            item,
            detail=detail,
            context=CatalogConversionReadinessContext(mini_app_open_url=None),
        )
        assert r is not None
        self.assertEqual(len(r.guided_actions), 1)
        self.assertEqual(r.guided_actions[0].callback_data, f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}42")

    def test_blocked_media_gate(self) -> None:
        item = self._minimal_supplier_item(
            console_status="blocked",
            cta_safety_status="media_blocked",
        )
        r = SupplierOfferCatalogConversionReadinessService.build_from_console_item(item)
        assert r is not None
        self.assertEqual(r.readiness_status, "blocked")
        self.assertEqual(r.main_blocker_message_key, "admin_a6a_blocker_media_gate")
        self.assertEqual(len(r.guided_actions), 1)
        self.assertEqual(r.guided_actions[0].callback_data, f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}42")

