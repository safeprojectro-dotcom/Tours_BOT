"""B10: admin supplier offer → tour bridge (idempotent, draft Tour, no orders)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select, func
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
from app.models.order import Order
from app.models.supplier import SupplierOffer
from app.models.tour import Tour, TourTranslation
from tests.unit.base import FoundationDBTestCase


class B10SupplierOfferTourBridgeAPITests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b10"
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

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-b10"}

    def _approved_offer(self, **overrides) -> SupplierOffer:
        s = self.create_supplier()
        dep = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        base_kwargs = {
            "title": "Bridge Offer",
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
        o = self.create_supplier_offer(
            s,
            **base_kwargs,
        )
        o.quality_warnings_json = {"items": ["low_res_cover"]}
        self.session.flush()
        return o

    def test_post_creates_tour_and_bridge(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["supplier_offer_id"], o.id)
        self.assertEqual(j["bridge_status"], "active")
        self.assertEqual(j["bridge_kind"], "created_new_tour")
        self.assertEqual(j["tour_status"], "draft")
        self.assertEqual(j["idempotent_replay"], False)
        self.assertIn("low_res_cover", (j.get("warnings") or []))
        tour_id = j["tour_id"]
        self.session.expire_all()
        tour = self.session.get(Tour, tour_id)
        self.assertIsNotNone(tour)
        self.assertEqual(tour.status, TourStatus.DRAFT)
        self.assertEqual(tour.sales_mode, TourSalesMode.PER_SEAT)
        self.assertEqual(tour.seats_total, 40)
        self.assertEqual(tour.seats_available, 40)

    def test_post_idempotent_replay(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        h = self._headers()
        r1 = self.client.post(f"/admin/supplier-offers/{o.id}/tour-bridge", headers=h, json={})
        self.assertEqual(r1.status_code, 200, r1.text)
        tid = r1.json()["tour_id"]
        r2 = self.client.post(f"/admin/supplier-offers/{o.id}/tour-bridge", headers=h, json={})
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertTrue(r2.json()["idempotent_replay"])
        self.assertEqual(r2.json()["tour_id"], tid)
        c = self.session.execute(select(func.count()).select_from(Tour)).scalar_one()
        # Only one new tour in session store for this test's scope
        self.assertGreaterEqual(c, 1)

    def test_non_approved_packaging_fails_422(self) -> None:
        o = self._approved_offer(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_missing_fields_422(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        o = self.create_supplier_offer(
            s,
            program_text="P",
            included_text="I",
            excluded_text="E",
            departure_datetime=dep,
            return_datetime=ret,
            base_price=Decimal("10.00"),
            currency="EUR",
            seats_total=5,
            packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
            lifecycle_status=SupplierOfferLifecycle.APPROVED,
        )
        o.description = ""
        o.marketing_summary = None
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 422, r.text)
        err = r.json()["detail"]
        self.assertIn("errors", err)
        self.assertIn("description_or_marketing_summary", err["errors"])

    def test_rejected_lifecycle_fails_422(self) -> None:
        o = self._approved_offer(lifecycle_status=SupplierOfferLifecycle.REJECTED)
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_full_bus_maps_sales_mode(self) -> None:
        o = self._approved_offer(sales_mode=TourSalesMode.FULL_BUS)
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        tour = self.session.get(Tour, r.json()["tour_id"])
        self.assertEqual(tour.sales_mode, TourSalesMode.FULL_BUS)
        self.assertEqual(tour.seats_total, 40)
        self.assertEqual(tour.seats_available, 40)

    def test_draft_not_open_for_sale(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        tour = self.session.get(Tour, r.json()["tour_id"])
        self.assertEqual(tour.status, TourStatus.DRAFT)
        self.assertNotEqual(tour.status, TourStatus.OPEN_FOR_SALE)

    def test_no_order_created(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        n0 = self.session.execute(select(func.count()).select_from(Order)).scalar_one()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        n1 = self.session.execute(select(func.count()).select_from(Order)).scalar_one()
        self.assertEqual(n0, n1)

    def test_supplier_offer_showcase_fields_unchanged(self) -> None:
        o = self._approved_offer()
        o.published_at = None
        o.showcase_message_id = None
        self.session.commit()
        pub_before = o.published_at
        sm_before = o.showcase_message_id
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, o.id)
        self.assertEqual(row.published_at, pub_before)
        self.assertEqual(row.showcase_message_id, sm_before)

    def test_get_bridge_returns_active(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        p = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={"notes": "n1"},
        )
        self.assertEqual(p.status_code, 200, p.text)
        g = self.client.get(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
        )
        self.assertEqual(g.status_code, 200, g.text)
        self.assertEqual(g.json()["tour_id"], p.json()["tour_id"])
        self.assertEqual(g.json()["bridge_kind"], "created_new_tour")

    def test_translation_row_created(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        tid = r.json()["tour_id"]
        self.session.expire_all()
        trs = self.session.execute(select(TourTranslation).where(TourTranslation.tour_id == tid)).scalars().all()
        self.assertTrue(len(trs) >= 1)
        self.assertIn("Meals", (trs[0].included_text or ""))

    def test_get_404_without_bridge(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.get(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 404, r.text)
        r2 = self.client.get(
            f"/admin/supplier-offers/{o.id + 10_000}/tour-bridge",
            headers=self._headers(),
        )
        self.assertEqual(r2.status_code, 404, r2.text)
