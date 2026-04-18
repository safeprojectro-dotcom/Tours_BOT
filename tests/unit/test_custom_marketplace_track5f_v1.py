"""Track 5f v1: customer multi-quote aggregate + selected-offer snippet (read-only)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class CustomMarketplaceTrack5F_V1Tests(FoundationDBTestCase):
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

    def _bootstrap_supplier(self, code: str, name: str) -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": code, "display_name": name},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def _create_rfq(self, tg: int = 170_001) -> int:
        self.create_user(telegram_user_id=tg)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": tg,
                "request_type": "group_trip",
                "travel_date_start": "2026-11-01",
                "route_notes": "5f v1",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    def test_proposed_count_zero_open(self) -> None:
        rid = self._create_rfq()
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 170_001})
        self.assertEqual(d.status_code, 200, d.text)
        body = d.json()
        self.assertEqual(body["proposed_response_count"], 0)
        self.assertIn("No supplier proposals", body["offers_received_hint"])
        self.assertIsNone(body["selected_offer_summary"])
        self.assertEqual(body["commercial_mode"], "custom_bus_rental_request")

    def test_proposed_count_excludes_declined(self) -> None:
        rid = self._create_rfq()
        _, token = self._bootstrap_supplier("S5F-A", "Supplier A")
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={"response_kind": "declined", "supplier_message": "No capacity"},
        )
        self.assertEqual(put.status_code, 200, put.text)
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 170_001})
        self.assertEqual(d.json()["proposed_response_count"], 0)

    def test_proposed_count_two_suppliers(self) -> None:
        rid = self._create_rfq()
        _, t1 = self._bootstrap_supplier("S5F-1", "One")
        _, t2 = self._bootstrap_supplier("S5F-2", "Two")
        prop = {
            "response_kind": "proposed",
            "supplier_message": "OK",
            "quoted_price": "900.00",
            "quoted_currency": "EUR",
            "supplier_declared_sales_mode": "per_seat",
            "supplier_declared_payment_mode": "platform_checkout",
        }
        r1 = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers={"Authorization": f"Bearer {t1}"},
            json=prop,
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers={"Authorization": f"Bearer {t2}"},
            json=prop,
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 170_001})
        self.assertEqual(d.json()["proposed_response_count"], 2)
        self.assertIn("2 supplier proposals", d.json()["offers_received_hint"])
        self.assertIsNone(d.json()["selected_offer_summary"])

    def test_selected_offer_snippet_after_resolution(self) -> None:
        rid = self._create_rfq()
        _, token = self._bootstrap_supplier("S5F-W", "Winner Co")
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "We can run this charter for your group.",
                "quoted_price": "1200.50",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(put.status_code, 200, put.text)
        resp_id = put.json()["id"]
        sel = self.client.post(
            f"/admin/custom-requests/{rid}/resolution",
            headers=self._headers_admin(),
            json={"status": "supplier_selected", "selected_supplier_response_id": resp_id},
        )
        self.assertEqual(sel.status_code, 200, sel.text)
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 170_001})
        self.assertEqual(d.status_code, 200, d.text)
        body = d.json()
        self.assertEqual(body["proposed_response_count"], 1)
        sos = body["selected_offer_summary"]
        self.assertIsNotNone(sos)
        assert sos is not None
        self.assertEqual(sos["quoted_price"], "1200.50")
        self.assertEqual(sos["quoted_currency"], "EUR")
        self.assertIn("charter", (sos.get("supplier_message_excerpt") or "").lower())
        self.assertEqual(sos["declared_sales_mode"], "per_seat")
        self.assertEqual(sos["declared_payment_mode"], "platform_checkout")
        self.assertNotIn("supplier", sos)
        self.assertNotIn("Winner", str(sos))

    def test_open_no_selected_snippet(self) -> None:
        rid = self._create_rfq()
        _, token = self._bootstrap_supplier("S5F-P", "Proposer")
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "response_kind": "proposed",
                "supplier_message": "Hi",
                "quoted_price": "1.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(put.status_code, 200, put.text)
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 170_001})
        body = d.json()
        self.assertEqual(body["proposed_response_count"], 1)
        self.assertIsNone(body["selected_offer_summary"])
