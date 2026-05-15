"""B15B/B15D/B15E/B15F: GET /admin/publishing-console read-only queue + rich read-model + affordances + template/channel read model."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    TourSalesMode,
    TourStatus,
)
from tests.unit.base import FoundationDBTestCase


class AdminPublishingConsoleTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction) -> None:
            parent = getattr(transaction, "_parent", None)
            if transaction.nested and not getattr(parent, "nested", False):
                self.nested = self.connection.begin_nested()

        self._restart_savepoint = restart_savepoint
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def _publishing_console_settings(self) -> SimpleNamespace:
        return SimpleNamespace(
            telegram_bot_username="pubconsolebot",
            telegram_mini_app_url="https://pubconsole.example/mini",
            telegram_mini_app_short_name="appshort",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_token="tok",
        )

    @contextmanager
    def _review_console_settings(self, cfg: SimpleNamespace):
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=cfg),
            patch("app.services.supplier_offer_review_package_service.get_settings", return_value=cfg),
            patch("app.services.admin_publishing_console_service.get_settings", return_value=cfg),
        ):
            yield

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_publishing_console_401_without_token(self) -> None:
        r = self.client.get("/admin/publishing-console")
        self.assertEqual(r.status_code, 401)

    def test_publishing_console_smoke_shape(self) -> None:
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(
                "/admin/publishing-console",
                headers={"Authorization": "Bearer test-admin-secret"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIn("items", body)
        self.assertIn("total_returned", body)
        self.assertIn("console_notice", body)
        self.assertIn("debug_notice", body)
        self.assertIsInstance(body["items"], list)
        self.assertIn("Read-only", body["console_notice"])
        for item in body["items"]:
            pr = item["publish_readiness"]
            self.assertFalse(pr["can_auto_publish"])
            self.assertEqual(pr["auto_publish_mode"], "disabled")
            self.assertIn("summary", pr)
            self.assertIn("badge", pr)
            self.assertIn("gate_summary", pr)

    def test_publishing_console_kind_supplier_offer_only(self) -> None:
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(
                "/admin/publishing-console?kind=supplier_offer_initial&limit=5",
                headers={"Authorization": "Bearer test-admin-secret"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        for item in r.json()["items"]:
            self.assertEqual(item["kind"], "supplier_offer_initial")

    def test_publishing_console_kind_tour_only(self) -> None:
        r = self.client.get(
            "/admin/publishing-console?kind=tour_promotion&limit=5",
            headers={"Authorization": "Bearer test-admin-secret"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        for item in r.json()["items"]:
            self.assertEqual(item["kind"], "tour_promotion")
            self.assertIn("tour_debug", item)
            self.assertIsNone(item["offer_debug"])
            self.assertIsNone(item.get("prepare_conversion_chain_plan_path"))
            self.assertIsNone(item.get("prepare_conversion_chain_plan_status"))
            self.assertIsNone(item.get("prepare_conversion_chain_recommended_action"))
            self.assertIsNone(item.get("prepare_conversion_chain_blockers_count"))
            pr = item["publish_readiness"]
            self.assertEqual(pr["status"], "not_applicable")
            self.assertFalse(pr["can_auto_publish"])
            self.assertEqual(pr["auto_publish_mode"], "disabled")

    def test_b15d_supplier_offer_ready_exact_tour_cta(self) -> None:
        """Ready supplier row: B15C gate green, conversion target is exact tour, CTA safety exact_tour_ready."""
        supplier = self.create_supplier()
        dep = datetime(2026, 12, 10, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 12, 12, 18, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            supplier,
            title="B15D Ready Row",
            program_text="Day one walk.",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=40,
            base_price=Decimal("199.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
            packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
        )
        self.session.commit()
        oid = offer.id
        h = self._headers()

        self.assertEqual(
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=h).status_code,
            200,
        )
        br = self.client.post(f"/admin/supplier-offers/{oid}/tour-bridge", headers=h, json={})
        self.assertEqual(br.status_code, 200, br.text)
        tour_id = br.json()["tour_id"]
        act = self.client.post(f"/admin/tours/{tour_id}/activate-for-catalog", headers=h, json={})
        self.assertEqual(act.status_code, 200, act.text)
        lk = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=h,
            json={"tour_id": tour_id},
        )
        self.assertEqual(lk.status_code, 200, lk.text)

        cfg = self._publishing_console_settings()
        with self._review_console_settings(cfg):
            r = self.client.get(
                "/admin/publishing-console?kind=supplier_offer_initial&limit=20",
                headers=h,
            )
        self.assertEqual(r.status_code, 200, r.text)
        match = next((it for it in r.json()["items"] if it["candidate_key"] == f"supplier_offer:{oid}"), None)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match["console_status"], "ready")
        self.assertEqual(match["readiness_level"], "ready")
        self.assertEqual(match["conversion_target_kind"], "exact_tour")
        self.assertEqual(match["cta_safety_status"], "exact_tour_ready")
        self.assertTrue(match["readiness_summary"].endswith("b15c_exact_tour_ready=True"))
        self.assertIsNotNone(match.get("conversion_target_url"))
        self.assertIn("appshort", match["conversion_target_url"] or "")
        self.assertGreater(len(match.get("actions") or []), 0)
        ow_actions = [a for a in match["actions"] if a.get("source") == "operator_workflow"]
        self.assertGreater(len(ow_actions), 0)
        preview = next((a for a in ow_actions if a["code"] == "get_showcase_preview"), None)
        self.assertIsNotNone(preview)
        assert preview is not None
        self.assertEqual(preview["kind"], "safe_read")
        self.assertTrue(preview["implemented"])
        self.assertIn(str(oid), preview["admin_path"])

        self.assertEqual(match["source_kind"], "supplier_offer")
        self.assertEqual(match["source_id"], oid)
        self.assertEqual(
            match["prepare_conversion_chain_plan_path"],
            f"/admin/supplier-offers/{oid}/prepare-conversion-chain/plan",
        )
        self.assertIn(
            match["prepare_conversion_chain_plan_status"],
            ("ineligible", "blocked", "partial", "already_prepared"),
        )
        self.assertIsInstance(match["prepare_conversion_chain_blockers_count"], int)
        self.assertGreaterEqual(match["prepare_conversion_chain_blockers_count"], 0)
        pca = match.get("prepare_conversion_chain_action")
        self.assertIsInstance(pca, dict)
        self.assertEqual(pca.get("method"), "POST")
        self.assertEqual(
            pca.get("path"),
            f"/admin/supplier-offers/{oid}/prepare-conversion-chain",
        )
        self.assertTrue(pca.get("requires_idempotency_key"))
        self.assertTrue(pca.get("requires_confirm_for_live"))
        self.assertTrue(pca.get("supports_dry_run"))
        self.assertEqual(match["template_kind"], "supplier_offer_showcase")
        self.assertTrue(match["template_preview_available"])
        self.assertIn("/showcase-preview", match.get("template_preview_path") or "")
        self.assertEqual(match["channel_kind"], "telegram_showcase_channel")
        self.assertIn("template_actions", match)
        self.assertIn("channel_actions", match)

    def test_b15d_supplier_offer_missing_execution_link(self) -> None:
        """Blocked bridge path: no execution link — CTA safety missing_execution_link, next action execution-link."""
        supplier = self.create_supplier()
        dep = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)
        ret = datetime(2026, 11, 7, 19, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            supplier,
            title="B15D No Exec Link",
            program_text="Itinerary.",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=30,
            base_price=Decimal("149.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
            packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
        )
        self.session.commit()
        oid = offer.id
        h = self._headers()

        self.assertEqual(
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=h).status_code,
            200,
        )
        br = self.client.post(f"/admin/supplier-offers/{oid}/tour-bridge", headers=h, json={})
        self.assertEqual(br.status_code, 200, br.text)
        tour_id = br.json()["tour_id"]
        act = self.client.post(f"/admin/tours/{tour_id}/activate-for-catalog", headers=h, json={})
        self.assertEqual(act.status_code, 200, act.text)

        cfg = self._publishing_console_settings()
        with self._review_console_settings(cfg):
            r = self.client.get(
                "/admin/publishing-console?kind=supplier_offer_initial&limit=20",
                headers=h,
            )
        self.assertEqual(r.status_code, 200, r.text)
        match = next((it for it in r.json()["items"] if it["candidate_key"] == f"supplier_offer:{oid}"), None)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match["console_status"], "needs_attention")
        self.assertEqual(match["readiness_level"], "needs_action")
        self.assertEqual(match["cta_safety_status"], "missing_execution_link")
        self.assertEqual(match["conversion_target_kind"], "exact_tour")
        pb = (match.get("primary_blocker") or "").lower()
        self.assertTrue("execution" in pb or "execution link" in pb or bool(match.get("next_action_code")))
        self.assertIn("create_execution_link", match["blocker_codes"])
        self.assertEqual(match["next_action_code"], "create_execution_link")
        self.assertIn("execution-link", match.get("admin_action_path") or "")

    def test_b15d_tour_promotion_row_safe_summary(self) -> None:
        """Tour promotion keeps B15B role; supplier-offer CTA semantics are not misleading."""
        dep = datetime.now(UTC) + timedelta(days=40)
        tour = self.create_tour(
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=2),
            sales_deadline=dep - timedelta(days=1),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=4,
            code="B15D-T-PROMO",
        )
        self.session.commit()

        cfg = self._publishing_console_settings()
        with self._review_console_settings(cfg):
            r = self.client.get(
                "/admin/publishing-console?kind=tour_promotion&limit=10",
                headers=self._headers(),
            )
        self.assertEqual(r.status_code, 200, r.text)
        match = next((it for it in r.json()["items"] if it.get("tour_debug", {}).get("tour_id") == tour.id), None)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match["kind"], "tour_promotion")
        self.assertEqual(match["conversion_target_kind"], "exact_tour")
        self.assertEqual(match["cta_safety_status"], "exact_tour_ready")
        self.assertNotIn("missing_execution_link", match["blocker_codes"])
        self.assertIn("not apply", (match.get("audit_hint") or "").lower())
        self.assertIsNone(match.get("next_action_code"))
        codes = [a["code"] for a in match["actions"]]
        self.assertIn("open_tour_admin", codes)
        self.assertIn("compose_tour_promotion_draft", codes)
        future = next(a for a in match["actions"] if a["code"] == "compose_tour_promotion_draft")
        self.assertFalse(future["enabled"])
        self.assertFalse(future["implemented"])
        self.assertEqual(future["source"], "future")
        self.assertEqual(match["source_kind"], "tour")
        self.assertEqual(match["source_id"], tour.id)
        self.assertEqual(match["template_kind"], "tour_promotion_placeholder")
        self.assertFalse(match["template_preview_available"])
        self.assertEqual(match["channel_kind"], "none")
        self.assertFalse(match["template_actions"][0]["implemented"])

    def test_b15b_response_shape_backward_compatible(self) -> None:
        """Original B15B top-level and per-item keys remain present (B15D is additive)."""
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ), patch(
            "app.services.supplier_offer_review_package_service.get_settings",
            return_value=mock_cfg,
        ), patch(
            "app.services.admin_publishing_console_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get("/admin/publishing-console?limit=3", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        for key in ("items", "total_returned", "console_notice", "debug_notice"):
            self.assertIn(key, body)
        enrich_keys = (
            "readiness_summary",
            "readiness_level",
            "conversion_target_kind",
            "cta_safety_status",
            "blocker_codes",
            "admin_action_path",
            "actions",
            "source_kind",
            "source_id",
            "source_title",
            "template_kind",
            "template_version",
            "template_source_status",
            "template_source_summary",
            "template_preview_available",
            "template_preview_path",
            "channel_kind",
            "channel_status",
            "channel_ref",
            "channel_summary",
            "media_policy_status",
            "media_summary",
            "template_actions",
            "channel_actions",
        )
        action_keys = (
            "code",
            "label",
            "kind",
            "enabled",
            "requires_confirmation",
            "danger_level",
            "admin_path",
            "method",
            "implemented",
            "disabled_reason",
            "source",
        )
        hint_keys = ("code", "label", "implemented", "enabled", "disabled_reason")
        for item in body["items"]:
            for key in (
                "candidate_key",
                "kind",
                "console_status",
                "title",
                "target_summary",
                "human_summary",
            ):
                self.assertIn(key, item)
            for key in enrich_keys:
                self.assertIn(key, item)
            self.assertIsInstance(item["actions"], list)
            for act in item["actions"]:
                for ak in action_keys:
                    self.assertIn(ak, act)
            for hint in item["template_actions"] + item["channel_actions"]:
                for hk in hint_keys:
                    self.assertIn(hk, hint)
