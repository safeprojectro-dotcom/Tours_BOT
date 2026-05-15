"""B16D2D: prepare_conversion_chain action affordance metadata (read-only)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.admin_guarded_action import AdminGuardedActionAttempt
from app.services.prepare_conversion_chain_readiness import derive_prepare_conversion_chain_action_affordance
from tests.unit.base import FoundationDBTestCase


class PrepareConversionChainD2dAffordanceTests(FoundationDBTestCase):
    def test_derive_ineligible_disabled(self) -> None:
        aff = derive_prepare_conversion_chain_action_affordance(
            supplier_offer_id=77,
            plan_status_label="ineligible",
            recommended_action=None,
            blockers_count=2,
        )
        self.assertFalse(aff.enabled)
        self.assertIsNotNone(aff.disabled_reason)
        self.assertEqual(aff.method, "POST")
        self.assertEqual(aff.code, "prepare_conversion_chain")
        self.assertTrue(aff.requires_idempotency_key)
        self.assertTrue(aff.requires_confirm_for_live)
        self.assertTrue(aff.supports_dry_run)
        self.assertTrue(aff.requires_admin)
        self.assertEqual(aff.path, "/admin/supplier-offers/77/prepare-conversion-chain")
        self.assertIn("{offer_id}", aff.path_pattern)
        self.assertEqual(aff.plan_path, "/admin/supplier-offers/77/prepare-conversion-chain/plan")
        self.assertEqual(aff.plan_status, "ineligible")

    def test_derive_partial_enabled(self) -> None:
        aff = derive_prepare_conversion_chain_action_affordance(
            supplier_offer_id=3,
            plan_status_label="partial",
            recommended_action="Create tour bridge",
            blockers_count=0,
        )
        self.assertTrue(aff.enabled)
        self.assertIsNone(aff.disabled_reason)
        self.assertEqual(aff.recommended_action, "Create tour bridge")

    def test_derive_blocked_disabled(self) -> None:
        aff = derive_prepare_conversion_chain_action_affordance(
            supplier_offer_id=4,
            plan_status_label="blocked",
            recommended_action=None,
            blockers_count=1,
        )
        self.assertFalse(aff.enabled)
        self.assertIsNotNone(aff.disabled_reason)

    def test_derive_already_prepared_enabled(self) -> None:
        aff = derive_prepare_conversion_chain_action_affordance(
            supplier_offer_id=5,
            plan_status_label="already_prepared",
            recommended_action=None,
            blockers_count=0,
        )
        self.assertTrue(aff.enabled)

    def test_review_package_get_does_not_create_audit_rows(self) -> None:
        from fastapi.testclient import TestClient

        from app.core.config import get_settings
        from app.db.session import get_db
        from app.main import create_app

        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        client = TestClient(self.app)
        try:
            supplier = self.create_supplier()
            offer = self.create_supplier_offer(supplier)
            self.session.flush()
            before = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
            r = client.get(
                f"/admin/supplier-offers/{offer.id}/review-package",
                headers={"Authorization": "Bearer test-admin-secret"},
            )
            self.assertEqual(r.status_code, 200, r.text)
            after = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
            self.assertEqual(before, after)
            act = r.json().get("prepare_conversion_chain_action")
            self.assertIsInstance(act, dict)
            self.assertEqual(act.get("method"), "POST")
        finally:
            client.close()
            self.app.dependency_overrides.clear()
            get_settings().admin_api_token = self._original_admin
