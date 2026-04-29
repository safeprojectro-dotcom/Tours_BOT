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

    def test_review_package_execution_link_precheck_when_published_without_link(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
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
