"""B10.2: admin activates draft tour for Mini App catalog (`open_for_sale`); no orders/Telegram/supplier lifecycle."""

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
    TourSalesMode,
    TourStatus,
)
from app.models.order import Order
from app.models.payment import Payment
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from app.services.mini_app_catalog import MiniAppCatalogService
from tests.unit.base import FoundationDBTestCase


class B10_2AdminTourActivateForCatalogAPITests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b10-2"
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
        return {"Authorization": "Bearer test-admin-b10-2"}

    def _draft_tour(self, **overrides) -> Tour:
        dep = datetime(2026, 11, 5, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        return self.create_tour(
            departure_datetime=dep,
            return_datetime=ret,
            status=TourStatus.DRAFT,
            sales_mode=overrides.pop("sales_mode", TourSalesMode.PER_SEAT),
            seats_total=overrides.pop("seats_total", 45),
            seats_available=overrides.pop("seats_available", 45),
            **overrides,
        )

    def test_draft_activates_to_open_for_sale(self) -> None:
        t = self._draft_tour()
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["status"], "open_for_sale")
        self.assertEqual(j["idempotent_replay"], False)
        self.session.expire_all()
        row = self.session.get(Tour, t.id)
        self.assertEqual(row.status, TourStatus.OPEN_FOR_SALE)

    def test_idempotent_replay(self) -> None:
        t = self._draft_tour()
        self.session.commit()
        h = self._headers()
        r1 = self.client.post(f"/admin/tours/{t.id}/activate-for-catalog", headers=h, json={})
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = self.client.post(f"/admin/tours/{t.id}/activate-for-catalog", headers=h, json={})
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertTrue(r2.json()["idempotent_replay"])
        self.assertEqual(r2.json()["status"], "open_for_sale")

    def test_missing_title_fails_422(self) -> None:
        t = self._draft_tour()
        t.title_default = "   "
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn("title_default", r.json()["detail"]["errors"])

    def test_full_bus_policy_not_per_seat_self_serve(self) -> None:
        t = self._draft_tour(
            sales_mode=TourSalesMode.FULL_BUS,
            seats_total=50,
            seats_available=50,
        )
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["sales_mode"], "full_bus")
        self.assertFalse(j["per_seat_self_service_allowed"])
        self.assertTrue(j["operator_path_required"])
        self.session.expire_all()
        row = self.session.get(Tour, t.id)
        self.assertEqual(row.seats_available, 50)

    def test_no_orders_or_payments_created(self) -> None:
        t = self._draft_tour()
        s = self.create_supplier()
        self.create_supplier_offer(s)
        self.session.commit()
        o0 = self.session.execute(select(func.count()).select_from(Order)).scalar_one()
        p0 = self.session.execute(select(func.count()).select_from(Payment)).scalar_one()
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        o1 = self.session.execute(select(func.count()).select_from(Order)).scalar_one()
        p1 = self.session.execute(select(func.count()).select_from(Payment)).scalar_one()
        self.assertEqual(o0, o1)
        self.assertEqual(p0, p1)

    def test_supplier_offer_unchanged(self) -> None:
        sup = self.create_supplier()
        o = self.create_supplier_offer(
            sup,
            lifecycle_status=SupplierOfferLifecycle.APPROVED,
            packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
            published_at=None,
        )
        o.showcase_message_id = 999888777
        t = self._draft_tour()
        self.session.commit()
        life_before = o.lifecycle_status
        sm_before = o.showcase_message_id
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, o.id)
        self.assertEqual(row.lifecycle_status, life_before)
        self.assertEqual(row.showcase_message_id, sm_before)

    def test_mini_app_catalog_status_scope_unchanged(self) -> None:
        self.assertEqual(MiniAppCatalogService.STATUS_SCOPE, (TourStatus.OPEN_FOR_SALE,))

    def test_non_draft_fails(self) -> None:
        t = self._draft_tour()
        t.status = TourStatus.COLLECTING_GROUP
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{t.id}/activate-for-catalog",
            headers=self._headers(),
            json={},
        )
        self.assertEqual(r.status_code, 400, r.text)
