"""B16D1: GET /admin/supplier-offers/{id}/prepare-conversion-chain/plan (read-only)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class AdminPrepareConversionChainPlanTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
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
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def test_prepare_chain_plan_404(self) -> None:
        r = self.client.get(
            "/admin/supplier-offers/999999/prepare-conversion-chain/plan",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 404, r.text)

    def test_prepare_chain_plan_shape_and_three_steps(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        r = self.client.get(
            f"/admin/supplier-offers/{offer.id}/prepare-conversion-chain/plan",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["supplier_offer_id"], offer.id)
        self.assertIn("prepare_conversion_chain_eligible", body)
        self.assertIn("eligibility_blockers", body)
        self.assertEqual(len(body["steps"]), 3)
        codes = [s["code"] for s in body["steps"]]
        self.assertEqual(
            codes,
            ["ensure_tour_bridge", "activate_tour_for_catalog", "ensure_active_execution_link"],
        )
        self.assertTrue(body["will_not_do"])
        joined = " ".join(body["will_not_do"])
        self.assertIn("Telegram", joined)
        self.assertIn("Read-only", body["audit_hint"])
        self.assertEqual(
            body["review_package_path"],
            f"/admin/supplier-offers/{offer.id}/review-package",
        )
        self.assertIn("generated_at", body)
        self.assertIsInstance(body["prepare_conversion_chain_eligible"], bool)
