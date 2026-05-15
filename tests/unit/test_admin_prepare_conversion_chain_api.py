"""B16D2C: POST /admin/supplier-offers/{id}/prepare-conversion-chain."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.admin_guarded_action import AdminGuardedActionAttempt
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class AdminPrepareConversionChainApiTests(FoundationDBTestCase):
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

    def _approved_offer(self, **overrides):
        s = self.create_supplier()
        dep = datetime.now(UTC) + timedelta(days=30)
        ret = dep + timedelta(days=2)
        base_kwargs = {
            "title": "Chain Offer API",
            "description": "Long description for the offer.",
            "marketing_summary": "Short marketing blurb",
            "program_text": "Day 1: walk; day 2: rest",
            "included_text": "Meals, guide",
            "excluded_text": "Flights, tips",
            "departure_datetime": dep,
            "return_datetime": ret,
            "seats_total": 40,
            "base_price": Decimal("199.00"),
            "currency": "EUR",
            "sales_mode": TourSalesMode.PER_SEAT,
            "payment_mode": SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            "lifecycle_status": SupplierOfferLifecycle.APPROVED,
            "packaging_status": SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
        }
        base_kwargs.update(overrides)
        return self.create_supplier_offer(s, **base_kwargs)

    def test_auth_required(self) -> None:
        r = self.client.post(
            "/admin/supplier-offers/1/prepare-conversion-chain",
            json={"idempotency_key": "k", "confirm": True, "dry_run": False},
        )
        self.assertEqual(r.status_code, 401, r.text)

    def test_post_returns_404_for_missing_offer(self) -> None:
        r = self.client.post(
            "/admin/supplier-offers/999999/prepare-conversion-chain",
            headers=self._headers(),
            json={"idempotency_key": "a-key", "confirm": True, "dry_run": False},
        )
        self.assertEqual(r.status_code, 404, r.text)

    def test_live_requires_confirm(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/prepare-conversion-chain",
            headers=self._headers(),
            json={"idempotency_key": "live-no-confirm", "confirm": False, "dry_run": False},
        )
        self.assertEqual(r.status_code, 422, r.text)
        detail = r.json().get("detail")
        self.assertIsInstance(detail, list)
        self.assertTrue(any("confirm" in str(item.get("loc", [])).lower() for item in detail))

    def test_blank_idempotency_key_422(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/prepare-conversion-chain",
            headers=self._headers(),
            json={"idempotency_key": "   ", "confirm": True, "dry_run": False},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_dry_run_no_audit_attempt(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        before = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/prepare-conversion-chain",
            headers=self._headers(),
            json={"idempotency_key": "dry-api", "confirm": False, "dry_run": True},
        )
        self.assertEqual(r.status_code, 200, r.text)
        after = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
        self.assertEqual(before, after)
        body = r.json()
        self.assertTrue(body["dry_run"])
        self.assertEqual(body["overall_status"], "dry_run_preview")
        self.assertIsNone(body.get("attempt_id"))

    def test_happy_path_live_commits_and_succeeds(self) -> None:
        o = self._approved_offer()
        o.quality_warnings_json = {"items": ["low_res_cover"]}
        self.session.flush()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/prepare-conversion-chain",
            headers=self._headers(),
            json={"idempotency_key": "happy-api-1", "confirm": True, "dry_run": False},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["overall_status"], "succeeded")
        self.assertIsNotNone(body.get("attempt_id"))
        self.assertIsNotNone(body.get("tour_id"))
        tour = self.session.get(Tour, body["tour_id"])
        self.assertIsNotNone(tour)

    def test_idempotent_replay_same_attempt_no_extra_tours(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        payload = {"idempotency_key": "idem-api-1", "confirm": True, "dry_run": False}
        r1 = self.client.post(
            f"/admin/supplier-offers/{o.id}/prepare-conversion-chain",
            headers=self._headers(),
            json=payload,
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        tcount = self.session.scalar(select(func.count()).select_from(Tour))
        r2 = self.client.post(
            f"/admin/supplier-offers/{o.id}/prepare-conversion-chain",
            headers=self._headers(),
            json=payload,
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        b2 = r2.json()
        self.assertEqual(b2["attempt_id"], r1.json()["attempt_id"])
        self.assertIn("replay", (b2.get("message") or "").lower())
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Tour)), tcount)
