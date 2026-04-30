"""Admin GET /admin/supplier-offers/{id}/review-package aggregation."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferPackagingStatus
from app.models.supplier import SupplierOffer
from tests.unit.base import FoundationDBTestCase


class SupplierOfferReviewPackageTests(FoundationDBTestCase):
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

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _bootstrap_supplier_token(self) -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers={"Authorization": "Bearer test-admin-secret"},
            json={"code": "REVPKG-1", "display_name": "ReviewPkg"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def _ready_offer(self, token: str) -> int:
        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
        c = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Review Trip",
                "description": "Nice trip",
                "program_text": "Day 1 …",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "vehicle_label": "Coach",
                "seats_total": 40,
                "base_price": "120.00",
                "currency": "EUR",
                "sales_mode": "per_seat",
            },
        )
        self.assertEqual(c.status_code, 201, c.text)
        oid = c.json()["id"]
        u = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"lifecycle_status": "ready_for_moderation"},
        )
        self.assertEqual(u.status_code, 200, u.text)
        return oid

    def test_review_package_404(self) -> None:
        r = self.client.get(
            "/admin/supplier-offers/999991001/review-package",
            headers={"Authorization": "Bearer test-admin-secret"},
        )
        self.assertEqual(r.status_code, 404)

    def test_review_package_surfaces_packaging_and_moderation_axes(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
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
            r = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["offer"]["id"], oid)
        self.assertIn("content_quality_review", body)
        self.assertIn("cover_media_quality_review", body)
        self.assertIn("has_warnings", body["cover_media_quality_review"])
        self.assertIsInstance(body["cover_media_quality_review"]["warnings"], list)
        self.assertIn("has_quality_warnings", body["content_quality_review"])
        self.assertIsInstance(body["content_quality_review"]["warnings"], list)
        self.assertEqual(body["offer"]["lifecycle_status"], "ready_for_moderation")
        self.assertNotEqual(body["offer"]["packaging_status"], "approved_for_publish")
        br = body["bridge_readiness"]
        self.assertIn("packaging_not_approved", br["blocking_codes"])
        self.assertFalse(br["can_attempt_bridge"])
        self.assertEqual(body["showcase_preview"]["supplier_offer_id"], oid)
        self.assertEqual(body["execution_links_review"]["total_links_returned"], 0)
        self.assertFalse(body["execution_links_review"]["can_create_execution_link"])
        self.assertIsNone(body["active_tour_bridge"])
        self.assertIsNone(body["linked_tour_catalog"])
        self.assertFalse(body["mini_app_conversion_preview"]["applicable"])
        self.assertIn("approve_packaging", body["recommended_next_actions"])
        cc = body["conversion_closure"]
        self.assertFalse(cc["has_tour_bridge"])
        self.assertFalse(cc["has_active_execution_link"])
        self.assertEqual(cc["next_missing_step"], "approve_packaging")
        ow = body["operator_workflow"]
        self.assertEqual(ow["state"], "awaiting_packaging_approval")
        self.assertEqual(ow["primary_next_action"], "generate_packaging_draft")
        self.assertIn("Tour bridge blocked:", " ".join(ow["blocking_reasons"]))
        codes = [a["code"] for a in ow["actions"]]
        self.assertIn("activate_tour_for_catalog", codes)
        act = next(a for a in ow["actions"] if a["code"] == "activate_tour_for_catalog")
        self.assertFalse(act["enabled"])
        self.assertIsNotNone(act["disabled_reason"])
        self.assertEqual(act["danger_level"], "conversion_enabling")
        pub = next(a for a in ow["actions"] if a["code"] == "publish_showcase_channel")
        self.assertEqual(pub["danger_level"], "public_dangerous")
        self.assertTrue(pub["requires_confirmation"])
        self.assertFalse(pub["enabled"])
        gen = next(a for a in ow["actions"] if a["code"] == "generate_packaging_draft")
        self.assertEqual(gen["danger_level"], "safe_mutation")
        req_ph = next(a for a in ow["actions"] if a["code"] == "request_cover_photo_replacement")
        self.assertFalse(req_ph["enabled"])

    def test_review_package_request_cover_photo_enabled_when_cover_reference_present(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        u = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"cover_media_reference": "https://cdn.example/hero.jpg"},
        )
        self.assertEqual(u.status_code, 200, u.text)
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        headers = {"Authorization": "Bearer test-admin-secret"}
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        req_ph = next(a for a in r.json()["operator_workflow"]["actions"] if a["code"] == "request_cover_photo_replacement")
        self.assertTrue(req_ph["enabled"])
        self.assertIsNone(req_ph["disabled_reason"])

    def test_review_package_request_cover_photo_disabled_when_media_review_blocks(self) -> None:
        """C2B6 correction: replacement_requested / rejected_* / fallback hides Telegram action."""
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        u = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"cover_media_reference": "https://cdn.example/hero.jpg"},
        )
        self.assertEqual(u.status_code, 200, u.text)
        row = self.session.get(SupplierOffer, oid)
        self.assertIsNotNone(row)
        row.packaging_draft_json = {"media_review": {"status": "replacement_requested"}}
        self.session.commit()

        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        headers = {"Authorization": "Bearer test-admin-secret"}
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        req_ph = next(a for a in r.json()["operator_workflow"]["actions"] if a["code"] == "request_cover_photo_replacement")
        self.assertFalse(req_ph["enabled"])
        self.assertIsNotNone(req_ph["disabled_reason"])
        self.assertIn("replacement_requested", req_ph["disabled_reason"])

    def test_review_package_request_cover_photo_still_enabled_when_media_review_approved(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        u = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"cover_media_reference": "https://cdn.example/hero.jpg"},
        )
        self.assertEqual(u.status_code, 200, u.text)
        row = self.session.get(SupplierOffer, oid)
        self.assertIsNotNone(row)
        row.packaging_draft_json = {"media_review": {"status": "approved_for_card"}}
        self.session.commit()

        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        headers = {"Authorization": "Bearer test-admin-secret"}
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        req_ph = next(a for a in r.json()["operator_workflow"]["actions"] if a["code"] == "request_cover_photo_replacement")
        self.assertTrue(req_ph["enabled"])

    def test_review_package_execution_link_precheck_when_published_without_link(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        sup_offer = self.session.get(SupplierOffer, oid)
        self.assertIsNotNone(sup_offer)
        sup_offer.packaging_status = SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH
        sup_offer.included_text = "Included"
        sup_offer.excluded_text = "Excluded"
        self.session.commit()

        self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="-100",
            telegram_bot_token="tok",
        )
        with (
            patch(
                "app.services.supplier_offer_moderation_service.get_settings",
                return_value=mock_cfg,
            ),
            patch(
                "app.services.supplier_offer_moderation_service.send_showcase_publication",
                return_value=42,
            ),
        ):
            pub = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(pub.status_code, 200, pub.text)

        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["offer"]["lifecycle_status"], "published")
        er = body["execution_links_review"]
        self.assertTrue(er["can_create_execution_link"])
        self.assertIsNone(er["execution_link_precheck_note"])
        actions = body["recommended_next_actions"]
        self.assertIn("create_execution_link", actions)
        cc = body["conversion_closure"]
        self.assertFalse(cc["has_tour_bridge"])
        self.assertFalse(cc["has_active_execution_link"])
        self.assertFalse(cc["supplier_offer_landing_routes_to_tour"])
        self.assertEqual(cc["next_missing_step"], "create_tour_bridge")
        ow = body["operator_workflow"]
        self.assertEqual(ow["primary_next_action"], "create_tour_bridge")
