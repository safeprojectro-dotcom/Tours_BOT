"""B8: admin recurrence — draft tours from template offer (no bridge, no activation)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

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
from app.models.supplier_offer_recurrence_generated_tour import SupplierOfferRecurrenceGeneratedTour
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class B8SupplierOfferRecurrenceAPITests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b8"
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
        return {"Authorization": "Bearer test-admin-b8"}

    def _approved_offer(self) -> SupplierOffer:
        s = self.create_supplier()
        dep = datetime(2026, 6, 1, 7, 30, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        o = self.create_supplier_offer(
            s,
            title="Recurrence Template",
            description="Long description for the offer.",
            marketing_summary="Short marketing blurb",
            program_text="Program day 1 and 2",
            included_text="Meals, guide",
            excluded_text="Flights, tips",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=50,
            base_price=Decimal("450.00"),
            currency="EUR",
            sales_mode=TourSalesMode.FULL_BUS,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            lifecycle_status=SupplierOfferLifecycle.APPROVED,
            packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
        )
        self.session.flush()
        return o

    def test_post_generates_draft_tours_and_audit_rows(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 2, "interval_days": 7, "start_offset_days": 7},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["source_supplier_offer_id"], o.id)
        self.assertEqual(len(j["items"]), 2)
        for item in j["items"]:
            tr = self.session.get(Tour, item["tour_id"])
            assert tr is not None
            self.assertEqual(tr.status, TourStatus.DRAFT)

        st = select(SupplierOfferRecurrenceGeneratedTour).where(
            SupplierOfferRecurrenceGeneratedTour.source_supplier_offer_id == o.id
        )
        rows = list(self.session.scalars(st).all())
        self.assertEqual(len(rows), 2)
        t0 = j["items"][0]
        t1 = j["items"][1]
        dep0 = datetime.fromisoformat(t0["departure_datetime"].replace("Z", "+00:00"))
        dep1 = datetime.fromisoformat(t1["departure_datetime"].replace("Z", "+00:00"))
        self.assertEqual((dep1 - dep0).days, 7)

    def test_count_out_of_range_422(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 30, "interval_days": 7, "start_offset_days": 0},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_generated_tours_are_draft_not_open_for_sale(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 1, "interval_days": 7, "start_offset_days": 14},
        )
        self.assertEqual(r.status_code, 200, r.text)
        tid = r.json()["items"][0]["tour_id"]
        tr = self.session.get(Tour, tid)
        assert tr is not None
        self.assertEqual(tr.status, TourStatus.DRAFT)
        self.assertNotEqual(tr.status, TourStatus.OPEN_FOR_SALE)

    def test_recurrence_does_not_create_supplier_offer_tour_bridges(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        n_br = self.session.scalar(
            select(func.count()).select_from(SupplierOfferTourBridge).where(
                SupplierOfferTourBridge.supplier_offer_id == o.id
            )
        )
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 2, "interval_days": 1, "start_offset_days": 100},
        )
        self.assertEqual(r.status_code, 200, r.text)
        n_br2 = self.session.scalar(
            select(func.count()).select_from(SupplierOfferTourBridge).where(
                SupplierOfferTourBridge.supplier_offer_id == o.id
            )
        )
        self.assertEqual(n_br, n_br2)

    def test_recurrence_does_not_create_orders_for_new_tours(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 2, "interval_days": 3, "start_offset_days": 5},
        )
        self.assertEqual(r.status_code, 200, r.text)
        tour_ids = [x["tour_id"] for x in r.json()["items"]]
        n_orders = self.session.scalar(
            select(func.count()).select_from(Order).where(Order.tour_id.in_(tour_ids))
        )
        self.assertEqual(n_orders, 0)

    def test_start_offset_zero_first_departure_matches_template(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 1, "interval_days": 7, "start_offset_days": 0},
        )
        self.assertEqual(r.status_code, 200, r.text)
        item = r.json()["items"][0]
        dep = datetime.fromisoformat(item["departure_datetime"].replace("Z", "+00:00"))
        self.assertEqual(dep, o.departure_datetime)
        tr = self.session.get(Tour, item["tour_id"])
        assert tr is not None
        self.assertEqual(tr.departure_datetime, o.departure_datetime)

    def test_duplicate_post_creates_duplicate_draft_tours(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        body = {"count": 1, "interval_days": 1, "start_offset_days": 200}
        r1 = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json=body,
        )
        r2 = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json=body,
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertNotEqual(r1.json()["items"][0]["tour_id"], r2.json()["items"][0]["tour_id"])
        n_gen = self.session.scalar(
            select(func.count()).select_from(SupplierOfferRecurrenceGeneratedTour).where(
                SupplierOfferRecurrenceGeneratedTour.source_supplier_offer_id == o.id
            )
        )
        self.assertEqual(n_gen, 2)

    def test_b8_second_activation_fails_when_sibling_b8_tour_already_open(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        body = {"count": 1, "interval_days": 1, "start_offset_days": 200}
        r1 = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json=body,
        )
        r2 = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json=body,
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r2.status_code, 200, r2.text)
        t1 = r1.json()["items"][0]["tour_id"]
        t2 = r2.json()["items"][0]["tour_id"]
        a1 = self.client.post(
            f"/admin/tours/{t1}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(a1.status_code, 200, a1.text)
        a2 = self.client.post(
            f"/admin/tours/{t2}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(a2.status_code, 400, a2.text)
        self.assertIn("another catalog-active tour", a2.json()["detail"])
        self.session.expire_all()
        self.assertEqual(self.session.get(Tour, t1).status, TourStatus.OPEN_FOR_SALE)
        self.assertEqual(self.session.get(Tour, t2).status, TourStatus.DRAFT)

    def test_duplicate_drafts_same_departure_no_activation_failure(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        body = {"count": 1, "interval_days": 1, "start_offset_days": 200}
        r1 = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json=body,
        )
        r2 = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json=body,
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r2.status_code, 200, r2.text)
        d1 = datetime.fromisoformat(r1.json()["items"][0]["departure_datetime"].replace("Z", "+00:00"))
        d2 = datetime.fromisoformat(r2.json()["items"][0]["departure_datetime"].replace("Z", "+00:00"))
        self.assertEqual(d1, d2)
        t1, t2 = r1.json()["items"][0]["tour_id"], r2.json()["items"][0]["tour_id"]
        for tid in (t1, t2):
            tr = self.session.get(Tour, tid)
            assert tr is not None
            self.assertEqual(tr.status, TourStatus.DRAFT)

    def test_b8_idempotent_activation_replay(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 1, "interval_days": 7, "start_offset_days": 20},
        )
        self.assertEqual(r.status_code, 200, r.text)
        tid = r.json()["items"][0]["tour_id"]
        h = self._headers()
        a1 = self.client.post(f"/admin/tours/{tid}/activate-for-catalog", headers=h, json={})
        self.assertEqual(a1.status_code, 200, a1.text)
        a2 = self.client.post(f"/admin/tours/{tid}/activate-for-catalog", headers=h, json={})
        self.assertEqual(a2.status_code, 200, a2.text)
        self.assertTrue(a2.json()["idempotent_replay"])
        self.assertEqual(self.session.get(Tour, tid).status, TourStatus.OPEN_FOR_SALE)

    def test_non_b8_draft_activates_without_recurrence_guard(self) -> None:
        dep = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
        ret = dep + timedelta(days=3)
        t = self.create_tour(
            code="NON-B8-ACT",
            title_default="Manual draft",
            departure_datetime=dep,
            return_datetime=ret,
            status=TourStatus.DRAFT,
            sales_mode=TourSalesMode.PER_SEAT,
            seats_total=20,
            seats_available=20,
        )
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.session.get(Tour, t.id).status, TourStatus.OPEN_FOR_SALE)

    def test_b8_activation_blocked_when_b10_bridged_tour_already_open_same_departure(self) -> None:
        o = self._approved_offer()
        self.session.commit()
        br = self.client.post(
            f"/admin/supplier-offers/{o.id}/tour-bridge",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(br.status_code, 200, br.text)
        tour_bridge_id = br.json()["tour_id"]
        ar = self.client.post(
            f"/admin/tours/{tour_bridge_id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(ar.status_code, 200, ar.text)
        rec = self.client.post(
            f"/admin/supplier-offers/{o.id}/recurrence/draft-tours",
            headers=self._headers(),
            json={"count": 1, "interval_days": 7, "start_offset_days": 0},
        )
        self.assertEqual(rec.status_code, 200, rec.text)
        b8_tid = rec.json()["items"][0]["tour_id"]
        b8_tour = self.session.get(Tour, b8_tid)
        bridge_tour = self.session.get(Tour, tour_bridge_id)
        assert b8_tour is not None and bridge_tour is not None
        self.assertEqual(b8_tour.departure_datetime, bridge_tour.departure_datetime)
        fail = self.client.post(
            f"/admin/tours/{b8_tid}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(fail.status_code, 400, fail.text)
        self.assertIn("another catalog-active tour", fail.json()["detail"])
        self.assertEqual(self.session.get(Tour, b8_tid).status, TourStatus.DRAFT)
        self.assertEqual(self.session.get(Tour, tour_bridge_id).status, TourStatus.OPEN_FOR_SALE)
