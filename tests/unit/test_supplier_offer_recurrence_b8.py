"""B8: admin recurrence — draft tours from template offer (no bridge, no activation)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import event

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
from app.models.supplier import SupplierOffer
from app.models.supplier_offer_recurrence_generated_tour import SupplierOfferRecurrenceGeneratedTour
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
