"""B4: admin packaging generate — auth, 404, deterministic draft, no publish side effects."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select, func

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferPackagingStatus
from app.models.order import Order
from app.models.tour import Tour
from app.models.supplier import SupplierOffer
from tests.unit.base import FoundationDBTestCase


class B4PackagingAPITests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b4"
        self.app.dependency_overrides[get_db] = self._db_override
        self.client = TestClient(self.app)

    def _db_override(self):
        yield self.session

    def tearDown(self) -> None:
        get_settings().admin_api_token = self._original_admin
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_packaging_generate_requires_admin_auth(self) -> None:
        r = self.client.post("/admin/supplier-offers/1/packaging/generate")
        self.assertIn(r.status_code, (401, 403, 503))

    def test_packaging_generate_404_unknown_offer(self) -> None:
        h = {"Authorization": "Bearer test-admin-b4"}
        r = self.client.post("/admin/supplier-offers/999999/packaging/generate", headers=h)
        self.assertEqual(r.status_code, 404, r.text)

    def test_packaging_deterministic_updates_fields_and_status(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 7, 1, 6, 0, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        o = self.create_supplier_offer(
            s,
            title="B4 Trip",
            description="Scenic",
            program_text="Day 1: …",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=12,
            base_price=Decimal("199.00"),
            currency="EUR",
            included_text="Bus",
            excluded_text="Lunch",
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        self.session.commit()
        oid = o.id
        h = {"Authorization": "Bearer test-admin-b4"}
        n_tour = self.session.scalar(select(func.count()).select_from(Tour)) or 0
        n_order = self.session.scalar(select(func.count()).select_from(Order)) or 0
        r = self.client.post(f"/admin/supplier-offers/{oid}/packaging/generate", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertIn(j["packaging_status"], ("packaging_generated", "needs_admin_review"))
        self.assertIsNotNone(j.get("short_hook"))
        self.assertIsNotNone(j.get("packaging_draft_json"))
        d = j["packaging_draft_json"]
        self.assertIn("telegram_post_draft", d)
        self.assertIn("mini_app_full_description", d)
        self.assertIn("199", j["marketing_summary"] or "")
        self.assertIn("EUR", j["marketing_summary"] or "")
        self.assertIn("2026", j["marketing_summary"] or "")
        tg = (d.get("telegram_post_draft") or "")
        self.assertNotRegex(tg, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        # no Tour / order churn
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Tour)), n_tour)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Order)), n_order)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, oid)
        assert row is not None
        self.assertIn(row.packaging_status, (SupplierOfferPackagingStatus.PACKAGING_GENERATED, SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW))
        self.assertIsNotNone(row.packaging_draft_json)

    def test_missing_price_needs_admin_review_with_warnings(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(hours=10)
        o = self.create_supplier_offer(
            s,
            title="No price",
            program_text="Some program",
            departure_datetime=dep,
            return_datetime=ret,
            base_price=None,
            currency="EUR",
            included_text="X",
            excluded_text="Y",
        )
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b4"}
        r = self.client.post(f"/admin/supplier-offers/{o.id}/packaging/generate", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["packaging_status"], "needs_admin_review")
        qj = j.get("quality_warnings_json") or {}
        self.assertIsNotNone(qj)
        self.assertIn("not on file", (j.get("marketing_summary") or ""))


class B4PackagingServiceUnitTests(FoundationDBTestCase):
    def test_injected_ai_client_overrides_marketing(self) -> None:
        from app.services.supplier_offer_packaging_service import (
            SupplierOfferPackagingService,
            build_deterministic_draft,
        )

        class _StubAI:
            def generate_draft(
                self,
                snapshot,
                *,
                missing_field_codes: list[str],
                quality_warnings: list[dict[str, str]],
            ):
                d = build_deterministic_draft(
                    snapshot, missing=list(missing_field_codes), warnings=quality_warnings
                )
                d["marketing_summary"] = "AI_DRAFT_MARKER"
                return d

        s = self.create_supplier()
        dep = datetime(2026, 3, 1, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        o = self.create_supplier_offer(
            s,
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
        )
        self.session.commit()
        out = SupplierOfferPackagingService(ai=_StubAI()).generate_and_persist(self.session, offer_id=o.id)  # type: ignore[arg-type]
        self.assertIn("AI_DRAFT_MARKER", out.marketing_summary or "")
