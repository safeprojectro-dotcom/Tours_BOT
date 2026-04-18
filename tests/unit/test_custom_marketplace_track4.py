"""Track 4: custom marketplace requests (Layer C) — intake, supplier response, admin oversight."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class CustomMarketplaceTrack4Tests(FoundationDBTestCase):
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

    def _headers_admin(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def _bootstrap_supplier(self) -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": "RFQ-S1", "display_name": "RFQ Supplier"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def test_mini_app_custom_request_requires_known_user(self) -> None:
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 999888777,
                "request_type": "group_trip",
                "travel_date_start": "2026-08-15",
                "route_notes": "Day trip to mountains",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_mini_app_create_admin_and_supplier_flow(self) -> None:
        self.create_user(telegram_user_id=120_001)
        self.session.commit()

        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 120_001,
                "request_type": "custom_route",
                "travel_date_start": "2026-09-01",
                "travel_date_end": "2026-09-03",
                "route_notes": "Timisoara to Black Sea coast",
                "group_size": 40,
                "special_conditions": "Need guide",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        created = r.json()
        rid = created["id"]
        self.assertEqual(created["status"], "open")

        lst = self.client.get("/admin/custom-requests", headers=self._headers_admin())
        self.assertEqual(lst.status_code, 200)
        ids = {x["id"] for x in lst.json()["items"]}
        self.assertIn(rid, ids)

        detail = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        self.assertEqual(detail.status_code, 200)
        body = detail.json()
        self.assertEqual(body["request"]["id"], rid)
        self.assertEqual(body["request"]["source_channel"], "mini_app")
        self.assertEqual(body["customer_telegram_user_id"], 120_001)
        self.assertEqual(body["responses"], [])

        _, token = self._bootstrap_supplier()
        sh = {"Authorization": f"Bearer {token}"}
        sup_list = self.client.get("/supplier-admin/custom-requests", headers=sh)
        self.assertEqual(sup_list.status_code, 200)
        self.assertIn(rid, {x["id"] for x in sup_list.json()["items"]})

        sup_detail = self.client.get(f"/supplier-admin/custom-requests/{rid}", headers=sh)
        self.assertEqual(sup_detail.status_code, 200)

        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "We can offer coach 49 seats at 4200 EUR all-in.",
                "quoted_price": "4200.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(put.status_code, 200, put.text)
        self.assertEqual(put.json()["response_kind"], "proposed")

        detail2 = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        self.assertEqual(len(detail2.json()["responses"]), 1)
        self.assertEqual(detail2.json()["responses"][0]["quoted_currency"], "EUR")
        self.assertEqual(detail2.json()["responses"][0]["supplier_declared_sales_mode"], "per_seat")
        self.assertEqual(detail2.json()["responses"][0]["supplier_declared_payment_mode"], "platform_checkout")

        patch = self.client.patch(
            f"/admin/custom-requests/{rid}",
            headers=self._headers_admin(),
            json={"admin_intervention_note": "Monitor pricing fairness."},
        )
        self.assertEqual(patch.status_code, 200)
        self.assertIn("Monitor", patch.json()["admin_intervention_note"] or "")

    def test_supplier_decline_and_admin_cancel(self) -> None:
        self.create_user(telegram_user_id=120_002)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 120_002,
                "request_type": "other",
                "travel_date_start": "2026-10-01",
                "route_notes": "Corporate outing",
            },
        )
        rid = r.json()["id"]
        _, token = self._bootstrap_supplier()
        sh = {"Authorization": f"Bearer {token}"}
        d = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={"response_kind": "declined", "supplier_message": "No capacity"},
        )
        self.assertEqual(d.status_code, 200)
        self.assertEqual(d.json()["response_kind"], "declined")

        c = self.client.patch(
            f"/admin/custom-requests/{rid}",
            headers=self._headers_admin(),
            json={"status": "cancelled"},
        )
        self.assertEqual(c.status_code, 200)
        self.assertEqual(c.json()["status"], "cancelled")

        blocked = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "Late offer",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(blocked.status_code, 400)
