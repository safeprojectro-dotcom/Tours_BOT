"""Supplier-admin and central-admin supplier visibility (Track 2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourSalesMode
from tests.unit.base import FoundationDBTestCase


class SupplierAdminRouteTests(FoundationDBTestCase):
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

    def test_admin_bootstrap_supplier_and_central_list_offers(self) -> None:
        admin_headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/suppliers",
            headers=admin_headers,
            json={"code": "ACME", "display_name": "Acme Tours", "credential_label": "test"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        token = body["api_token"]
        sid = body["supplier"]["id"]

        dep = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 6, 1, 20, 0, tzinfo=UTC)
        r2 = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "City break",
                "description": "Short trip",
                "program_text": "Day program",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "vehicle_label": "Bus",
                "seats_total": 40,
                "base_price": "99.00",
                "currency": "EUR",
                "sales_mode": "per_seat",
            },
        )
        self.assertEqual(r2.status_code, 201, r2.text)
        offer_id = r2.json()["id"]

        r3 = self.client.get(f"/admin/suppliers/{sid}/offers", headers=admin_headers)
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["items"][0]["id"], offer_id)

        r4 = self.client.get(f"/admin/supplier-offers/{offer_id}", headers=admin_headers)
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.json()["title"], "City break")

    def test_supplier_cannot_read_other_suppliers_offer(self) -> None:
        admin_headers = {"Authorization": "Bearer test-admin-secret"}
        a = self.client.post("/admin/suppliers", headers=admin_headers, json={"code": "S-A", "display_name": "A"})
        b = self.client.post("/admin/suppliers", headers=admin_headers, json={"code": "S-B", "display_name": "B"})
        self.assertEqual(a.status_code, 201)
        self.assertEqual(b.status_code, 201)
        token_a = a.json()["api_token"]
        token_b = b.json()["api_token"]

        dep = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 7, 1, 18, 0, tzinfo=UTC)
        created = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "title": "B only",
                "description": "d",
                "program_text": "p",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "vehicle_label": "V",
                "seats_total": 10,
                "base_price": "10.00",
                "currency": "EUR",
            },
        )
        self.assertEqual(created.status_code, 201)
        oid = created.json()["id"]

        forbidden = self.client.get(f"/supplier-admin/offers/{oid}", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(forbidden.status_code, 404)

    def test_ready_for_moderation_requires_complete_fields(self) -> None:
        admin_headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/suppliers", headers=admin_headers, json={"code": "READY", "display_name": "R"})
        self.assertEqual(r.status_code, 201)
        token = r.json()["api_token"]
        dep = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 8, 2, 18, 0, tzinfo=UTC)
        c = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "T",
                "description": "",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "seats_total": 0,
            },
        )
        self.assertEqual(c.status_code, 201)
        oid = c.json()["id"]

        bad = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"lifecycle_status": "ready_for_moderation"},
        )
        self.assertEqual(bad.status_code, 400)

        ok = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Full desc",
                "program_text": "Program",
                "seats_total": 30,
                "base_price": "50.00",
                "currency": "EUR",
                "vehicle_label": "Coach",
                "lifecycle_status": "ready_for_moderation",
            },
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json()["lifecycle_status"], "ready_for_moderation")

    def test_core_admin_overview_still_works(self) -> None:
        """Regression guard: Layer A admin overview unchanged for existing flows."""
        from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus

        user = self.create_user()
        tour = self.create_tour(
            code="CORE-ADM-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
            sales_mode=TourSalesMode.PER_SEAT,
        )
        point = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        self.session.commit()

        headers = {"Authorization": "Bearer test-admin-secret"}
        ov = self.client.get("/admin/overview", headers=headers)
        self.assertEqual(ov.status_code, 200)
        self.assertGreaterEqual(ov.json()["tours_total_approx"], 1)
