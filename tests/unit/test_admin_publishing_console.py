"""B15B/B15D/B15E/B15F/B15K/B15L/B15M/B15P/B17A: GET /admin/publishing-console read-only queue + per-offer detail + editor detail + template library + preview payload + ui_card/ui_sections."""

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

    def test_supplier_offer_detail_401_without_token(self) -> None:
        r = self.client.get("/admin/publishing-console/supplier-offers/1")
        self.assertEqual(r.status_code, 401)

    def test_supplier_offer_detail_404(self) -> None:
        r = self.client.get(
            "/admin/publishing-console/supplier-offers/999999999",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 404)

    def test_supplier_offer_editor_detail_401_without_token(self) -> None:
        r = self.client.get("/admin/publishing-console/supplier-offers/1/editor")
        self.assertEqual(r.status_code, 401)

    def test_supplier_offer_editor_detail_404(self) -> None:
        r = self.client.get(
            "/admin/publishing-console/supplier-offers/999999999/editor",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 404)

    def test_supplier_offer_detail_b15m_read_model(self) -> None:
        """B15M: single-offer detail exposes same nested objects as list rows + summaries + safety flags."""
        supplier = self.create_supplier()
        dep = datetime(2026, 12, 10, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 12, 12, 18, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            supplier,
            title="B15M Detail Row",
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
            list_r = self.client.get(
                "/admin/publishing-console?kind=supplier_offer_initial&limit=20",
                headers=h,
            )
            detail_r = self.client.get(
                f"/admin/publishing-console/supplier-offers/{oid}",
                headers=h,
            )
        self.assertEqual(list_r.status_code, 200, list_r.text)
        self.assertEqual(detail_r.status_code, 200, detail_r.text)
        match = next((it for it in list_r.json()["items"] if it["candidate_key"] == f"supplier_offer:{oid}"), None)
        self.assertIsNotNone(match)
        assert match is not None

        d = detail_r.json()
        self.assertEqual(d["supplier_offer_id"], oid)
        self.assertEqual(d["candidate_key"], f"supplier_offer:{oid}")
        self.assertEqual(d["kind"], "supplier_offer_initial")
        self.assertEqual(d["console_status"], match["console_status"])
        self.assertEqual(d["title"], match["title"])
        self.assertEqual(d["review_package_path"], match["review_package_path"])
        self.assertEqual(d["prepare_conversion_chain_plan_path"], match["prepare_conversion_chain_plan_path"])
        self.assertEqual(d["publish_readiness"]["status"], match["publish_readiness"]["status"])
        self.assertEqual(d["console_preview"]["template_family"], match["console_preview"]["template_family"])
        self.assertEqual(d["template_library"]["family"], match["template_library"]["family"])
        self.assertEqual(d["preview_payload"]["source"], match["preview_payload"]["source"])
        self.assertEqual(len(d["actions"]), len(match["actions"]))
        pca_d = d.get("prepare_conversion_chain_action")
        pca_m = match.get("prepare_conversion_chain_action")
        self.assertEqual((pca_d or {}).get("path"), (pca_m or {}).get("path"))

        cs = d["conversion_summary"]
        self.assertTrue(cs["has_tour_bridge"])
        self.assertTrue(cs["has_catalog_visible_tour"])
        self.assertTrue(cs["has_active_execution_link"])
        od = match.get("offer_debug") or {}
        self.assertEqual(cs["next_missing_step"], od.get("next_missing_step"))

        lt = d["linked_tour_summary"]
        self.assertEqual(lt["tour_id"], tour_id)
        self.assertTrue((lt.get("tour_code") or "").strip())
        self.assertIsNotNone(lt.get("tour_status"))
        self.assertTrue(lt["catalog_listed_for_mini_app"])

        pub = d["publication_summary"]
        self.assertFalse(pub["already_published"])
        self.assertIsNotNone(pub.get("lifecycle_status"))

        safe = d["safety_summary"]
        self.assertTrue(safe["read_only"])
        self.assertTrue(safe["no_telegram_io"])
        self.assertTrue(safe["no_publish_attempt"])
        self.assertTrue(safe["no_prepare_chain_execution"])
        self.assertTrue(safe["no_layer_a_mutation"])
        self.assertTrue(safe["note"])

        self.assertIn("Read-only", d["detail_notice"])
        self.assertTrue(d.get("generated_at"))

        secs = d.get("ui_sections") or []
        self.assertGreaterEqual(len(secs), 8)
        keys = {s["section_key"] for s in secs}
        self.assertIn("publish_readiness", keys)
        self.assertIn("console_preview", keys)
        self.assertIn("safety_summary", keys)
        orders = [s["display_order"] for s in secs]
        self.assertEqual(orders, sorted(orders))

    def test_b17a_editor_detail_read_model(self) -> None:
        """B17A: editor GET mirrors B15M nested data in source_snapshot and exposes section slices."""
        supplier = self.create_supplier()
        dep = datetime(2026, 12, 11, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 12, 13, 18, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            supplier,
            title="B17A Editor Row",
            program_text="Scenic day.",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=36,
            base_price=Decimal("179.00"),
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
            list_r = self.client.get(
                "/admin/publishing-console?kind=supplier_offer_initial&limit=20",
                headers=h,
            )
            detail_r = self.client.get(
                f"/admin/publishing-console/supplier-offers/{oid}",
                headers=h,
            )
            editor_r = self.client.get(
                f"/admin/publishing-console/supplier-offers/{oid}/editor",
                headers=h,
            )
        self.assertEqual(list_r.status_code, 200, list_r.text)
        self.assertEqual(detail_r.status_code, 200, detail_r.text)
        self.assertEqual(editor_r.status_code, 200, editor_r.text)
        match = next((it for it in list_r.json()["items"] if it["candidate_key"] == f"supplier_offer:{oid}"), None)
        self.assertIsNotNone(match)
        assert match is not None

        d = detail_r.json()
        e = editor_r.json()

        self.assertEqual(e["supplier_offer_id"], oid)
        self.assertEqual(e["candidate_key"], f"supplier_offer:{oid}")
        self.assertEqual(e["kind"], "supplier_offer_initial")
        self.assertEqual(e["editor_status"], d["console_status"])
        self.assertEqual(e["title"], d["title"])
        self.assertEqual(e["source_detail_path"], f"/admin/supplier-offers/{oid}")
        self.assertEqual(e["review_package_path"], d["review_package_path"])
        self.assertEqual(e["publishing_console_detail_path"], f"/admin/publishing-console/supplier-offers/{oid}")
        self.assertEqual(e["prepare_conversion_chain_plan_path"], d["prepare_conversion_chain_plan_path"])
        self.assertIn(e["editor_status_tone"], ("neutral", "success", "warning", "danger", "info"))
        self.assertTrue((e.get("editor_status_label") or "").strip())

        snap = e["source_snapshot"]
        pr_snap = dict(snap["publish_readiness"])
        pr_d = dict(d["publish_readiness"])
        pr_snap.pop("generated_at", None)
        pr_d.pop("generated_at", None)
        self.assertEqual(pr_snap, pr_d)

        pay_snap = dict(snap["preview_payload"])
        pay_d = dict(d["preview_payload"])
        pay_snap.pop("generated_at", None)
        pay_d.pop("generated_at", None)
        self.assertEqual(pay_snap, pay_d)

        self.assertEqual(snap["console_preview"], d["console_preview"])
        self.assertEqual(snap["template_library"], d["template_library"])
        self.assertEqual(snap["safety_summary"], d["safety_summary"])
        self.assertEqual(snap["ui_card"], match["ui_card"])

        ch = e["channel_section"]
        self.assertEqual(ch["channel_kind"], match["channel_kind"])
        self.assertEqual(ch["channel_status"], match["channel_status"])
        tpl = e["template_section"]
        self.assertEqual(tpl["template_kind"], match["template_kind"])
        self.assertEqual(tpl["library_family"], match["template_library"]["family"])
        pv = e["preview_section"]
        self.assertEqual(pv["payload_status"], match["preview_payload"]["payload_status"])
        cta = e["cta_section"]
        self.assertEqual(cta["conversion_target_kind"], match["conversion_target_kind"])
        self.assertEqual(cta["cta_safety_status"], match["cta_safety_status"])
        media = e["media_section"]
        self.assertEqual(media["media_policy_status"], match["media_policy_status"])
        rd = e["readiness_section"]
        self.assertEqual(rd["readiness_level"], match["readiness_level"])
        self.assertEqual(rd["console_status"], d["console_status"])
        sf = e["safety_section"]
        self.assertEqual(sf["detail_notice"], d["detail_notice"])
        self.assertLessEqual(
            (sf.get("ui_card_safety_line") or "").count("Publishing console is read-only"),
            1,
        )
        self.assertIsInstance(e.get("future_actions"), list)
        self.assertIn("B17A", e.get("editor_notice") or "")
        self.assertEqual(snap["publish_readiness"]["generated_at"], e["generated_at"])

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
            cp = item["console_preview"]
            self.assertIn(cp["preview_status"], ("available", "placeholder", "blocked", "not_applicable"))
            self.assertIn(
                cp["template_family"],
                ("supplier_offer_showcase", "tour_promotion", "custom_request_cta", "unknown"),
            )
            self.assertTrue(cp["safety_note"])
            self.assertIn("read-only", cp["safety_note"].lower())
            tl = item["template_library"]
            self.assertIn(tl["family"], ("supplier_offer_showcase", "tour_promotion", "unknown"))
            self.assertTrue(tl["safety_note"])
            self.assertIn("read-only", tl["safety_note"].lower())
            self.assertIsInstance(tl["available_templates"], list)
            self.assertGreaterEqual(len(tl["available_templates"]), 1)
            for ent in tl["available_templates"]:
                self.assertIn(ent["status"], ("available", "future", "not_applicable", "blocked"))
                self.assertTrue(ent["template_id"])
            pay = item["preview_payload"]
            self.assertIn(pay["payload_status"], ("available", "placeholder", "blocked", "not_applicable"))
            self.assertIn(
                pay["source"],
                ("showcase_preview", "packaging_draft", "supplier_offer_fields", "tour_placeholder", "none"),
            )
            self.assertTrue(pay["safety_note"])
            self.assertIn("read-only", pay["safety_note"].lower())
            self.assertIsInstance(pay["warnings"], list)
            self.assertIsInstance(pay["blockers"], list)
            if pay.get("publish_readiness_note"):
                self.assertIn("publish_readiness", pay["publish_readiness_note"].lower())
            if pay.get("template_library_note"):
                self.assertIn("template_library", pay["template_library_note"].lower())
            if item["kind"] == "tour_promotion":
                self.assertEqual(pay["source"], "tour_placeholder")
            uc = item["ui_card"]
            self.assertIn(uc["status_tone"], ("neutral", "success", "warning", "danger", "info"))
            self.assertIn(uc["primary_action_kind"], ("safe_read", "guarded_post", "future", "none"))
            self.assertTrue(uc.get("status_badge"))
            self.assertTrue((uc.get("status_label") or "").strip())
            safety_line = (uc.get("safety_line") or "").strip()
            self.assertTrue(safety_line)
            self.assertLessEqual(
                safety_line.count("Publishing console is read-only"),
                1,
                msg=f"ui_card.safety_line should not duplicate read-only lead-in: {safety_line!r}",
            )
            self.assertEqual(uc.get("card_title"), item.get("title"))

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
            cp = item["console_preview"]
            self.assertEqual(cp["template_family"], "tour_promotion")
            self.assertEqual(cp["preview_status"], "placeholder")
            self.assertIn("placeholder", cp["safety_note"].lower())
            tl = item["template_library"]
            self.assertEqual(tl["family"], "tour_promotion")
            self.assertEqual(tl["selected_template_id"], "tour_promotion_placeholder")
            self.assertTrue(any(e["template_id"] == "tour_promotion_placeholder" for e in tl["available_templates"]))
            self.assertTrue(all(e["status"] == "future" for e in tl["available_templates"]))
            pay = item["preview_payload"]
            self.assertEqual(pay["payload_status"], "not_applicable")
            self.assertEqual(pay["source"], "tour_placeholder")
            self.assertIsNone(pay.get("caption_html"))

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
        cp = match["console_preview"]
        self.assertEqual(cp["template_family"], "supplier_offer_showcase")
        self.assertIn(cp["preview_status"], ("available", "placeholder", "blocked"))
        self.assertEqual(cp["next_action_code"], match["publish_readiness"]["next_action_code"])
        self.assertIsNotNone(cp.get("preview_path"))
        tl = match["template_library"]
        self.assertEqual(tl["family"], "supplier_offer_showcase")
        self.assertEqual(tl["selected_template_id"], tl["recommended_template_id"])
        show = next(e for e in tl["available_templates"] if e["template_id"] == "supplier_offer_showcase")
        self.assertEqual(show["status"], "available")
        cr = next(e for e in tl["available_templates"] if e["template_id"] == "custom_request_cta")
        self.assertEqual(cr["status"], "not_applicable")
        pay = match["preview_payload"]
        self.assertIn(pay["payload_status"], ("available", "placeholder"))
        self.assertEqual(pay["source"], "showcase_preview")
        self.assertIsNotNone(pay.get("caption_html"))
        self.assertIsNotNone(pay.get("generated_at"))
        self.assertIn("publish_readiness", (pay.get("publish_readiness_note") or "").lower())
        self.assertIn("template_library", (pay.get("template_library_note") or "").lower())
        uic = match["ui_card"]
        self.assertEqual(uic["primary_action_kind"], "guarded_post")
        self.assertEqual(uic["status_tone"], "success")
        self.assertEqual(uic["primary_action_code"], "prepare_conversion_chain")

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
        ui_card_keys = (
            "card_title",
            "card_subtitle",
            "status_badge",
            "status_label",
            "status_tone",
            "primary_line",
            "secondary_line",
            "primary_action_label",
            "primary_action_code",
            "primary_action_enabled",
            "primary_action_kind",
            "primary_action_path",
            "secondary_action_label",
            "secondary_action_code",
            "secondary_action_enabled",
            "warning_line",
            "blocker_line",
            "safety_line",
        )
        for item in body["items"]:
            for key in (
                "candidate_key",
                "kind",
                "console_status",
                "title",
                "target_summary",
                "human_summary",
                "publish_readiness",
                "console_preview",
                "template_library",
                "preview_payload",
                "admin_tour_path",
                "ui_card",
            ):
                self.assertIn(key, item)
            for uk in ui_card_keys:
                self.assertIn(uk, item["ui_card"])
            for key in enrich_keys:
                self.assertIn(key, item)
            self.assertIsInstance(item["actions"], list)
            for act in item["actions"]:
                for ak in action_keys:
                    self.assertIn(ak, act)
            for hint in item["template_actions"] + item["channel_actions"]:
                for hk in hint_keys:
                    self.assertIn(hk, hint)
