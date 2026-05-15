"""B15H: read-only publish readiness derivation (suggest-only; no Telegram I/O)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.admin_guarded_action import AdminGuardedActionAttempt
from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.models.supplier import SupplierOffer
from app.services.supplier_offer_publish_readiness import (
    derive_supplier_offer_publish_readiness,
    publish_readiness_for_tour_promotion,
)
from app.services.supplier_offer_review_package_service import SupplierOfferReviewPackageService
from tests.unit.base import FoundationDBTestCase


class SupplierOfferPublishReadinessTests(FoundationDBTestCase):
    def test_publish_readiness_tour_promotion_row_not_applicable(self) -> None:
        t = datetime.now(UTC)
        pr = publish_readiness_for_tour_promotion(generated_at=t)
        self.assertEqual(pr.status, "not_applicable")
        self.assertFalse(pr.can_suggest_manual_publish)
        self.assertFalse(pr.can_auto_publish)
        self.assertEqual(pr.auto_publish_mode, "disabled")
        self.assertEqual(pr.badge, "not_applicable")
        self.assertEqual(pr.next_action_code, "not_applicable")
        self.assertIsNotNone(pr.summary)
        self.assertIsNotNone(pr.gate_summary)

    def test_derive_matches_review_package_service_snapshot(self) -> None:
        supplier = self.create_supplier()
        dep = datetime.now(UTC)
        offer = SupplierOffer(
            supplier_id=supplier.id,
            supplier_reference="PR-1",
            title="PR Offer",
            description="d",
            program_text="p",
            departure_datetime=dep,
            return_datetime=dep,
            seats_total=10,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        self.session.add(offer)
        self.session.flush()
        svc = SupplierOfferReviewPackageService()
        cfg = SimpleNamespace(
            telegram_bot_username="x",
            telegram_mini_app_url="https://ex/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with patch("app.services.supplier_offer_moderation_service.get_settings", return_value=cfg):
            pkg = svc.review_package(self.session, offer_id=offer.id)
        same = derive_supplier_offer_publish_readiness(pkg, generated_at=pkg.publish_readiness.generated_at)
        self.assertEqual(same.status, pkg.publish_readiness.status)
        self.assertEqual(same.can_suggest_manual_publish, pkg.publish_readiness.can_suggest_manual_publish)
        self.assertFalse(same.can_auto_publish)
        self.assertEqual(same.badge, pkg.publish_readiness.badge)
        self.assertEqual(same.summary, pkg.publish_readiness.summary)

    def test_review_package_get_does_not_create_guarded_action_attempts(self) -> None:
        self.app = create_app()
        orig = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        client = TestClient(self.app)
        try:
            supplier = self.create_supplier()
            dep = datetime.now(UTC)
            offer = SupplierOffer(
                supplier_id=supplier.id,
                supplier_reference="PR-audit",
                title="Audit",
                description="d",
                program_text="p",
                departure_datetime=dep,
                return_datetime=dep,
                seats_total=5,
            )
            self.session.add(offer)
            self.session.flush()
            n_before = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt)) or 0
            r = client.get(
                f"/admin/supplier-offers/{offer.id}/review-package",
                headers={"Authorization": "Bearer test-admin-secret"},
            )
            self.assertEqual(r.status_code, 200, r.text)
            n_after = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt)) or 0
            self.assertEqual(n_before, n_after)
            self.assertIn("publish_readiness", r.json())
        finally:
            client.close()
            self.app.dependency_overrides.clear()
            get_settings().admin_api_token = orig
