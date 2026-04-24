"""Track 5a: commercial resolution selection (no order / payment bridge)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class CustomMarketplaceTrack5aTests(FoundationDBTestCase):
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

    def _bootstrap_supplier(self, code: str = "RFQ-S5A") -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": code, "display_name": "RFQ Supplier 5a"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def test_select_winning_response_and_customer_read(self) -> None:
        self.create_user(telegram_user_id=130_001)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_001,
                "request_type": "group_trip",
                "travel_date_start": "2026-11-01",
                "route_notes": "School trip",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        rid = r.json()["id"]

        _, token = self._bootstrap_supplier()
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "We can do it.",
                "quoted_price": "1000.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(put.status_code, 200, put.text)
        resp_id = put.json()["id"]

        rev = self.client.post(
            f"/admin/custom-requests/{rid}/resolution",
            headers=self._headers_admin(),
            json={"status": "under_review"},
        )
        self.assertEqual(rev.status_code, 200, rev.text)
        self.assertEqual(rev.json()["status"], "under_review")

        sel = self.client.post(
            f"/admin/custom-requests/{rid}/resolution",
            headers=self._headers_admin(),
            json={"status": "supplier_selected", "selected_supplier_response_id": resp_id},
        )
        self.assertEqual(sel.status_code, 200, sel.text)
        body = sel.json()
        self.assertEqual(body["status"], "supplier_selected")
        self.assertEqual(body["selected_supplier_response_id"], resp_id)

        detail = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        self.assertEqual(detail.status_code, 200)
        responses = detail.json()["responses"]
        self.assertEqual(len(responses), 1)
        self.assertTrue(responses[0]["is_selected"])

        cust = self.client.get(
            "/mini-app/custom-requests",
            params={"telegram_user_id": 130_001},
        )
        self.assertEqual(cust.status_code, 200, cust.text)
        items = cust.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "supplier_selected")
        self.assertIn("selected", items[0]["customer_visible_summary"].lower())

        one = self.client.get(
            f"/mini-app/custom-requests/{rid}",
            params={"telegram_user_id": 130_001},
        )
        self.assertEqual(one.status_code, 200, one.text)
        self.assertEqual(one.json()["status"], "supplier_selected")

    def test_reject_selection_from_other_request(self) -> None:
        self.create_user(telegram_user_id=130_002)
        self.session.commit()
        r1 = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_002,
                "request_type": "other",
                "travel_date_start": "2026-12-01",
                "route_notes": "Trip A",
            },
        )
        r2 = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_002,
                "request_type": "other",
                "travel_date_start": "2026-12-02",
                "route_notes": "Trip B",
            },
        )
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]
        _, token = self._bootstrap_supplier("S5A-2")
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{id1}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "For A",
                "quoted_price": "1.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        wrong_resp_id = put.json()["id"]

        bad = self.client.post(
            f"/admin/custom-requests/{id2}/resolution",
            headers=self._headers_admin(),
            json={"status": "supplier_selected", "selected_supplier_response_id": wrong_resp_id},
        )
        self.assertEqual(bad.status_code, 400, bad.text)

    def test_patch_cannot_set_resolution_status(self) -> None:
        self.create_user(telegram_user_id=130_003)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_003,
                "request_type": "group_trip",
                "travel_date_start": "2026-10-10",
                "route_notes": "Patch guard",
            },
        )
        rid = r.json()["id"]
        p = self.client.patch(
            f"/admin/custom-requests/{rid}",
            headers=self._headers_admin(),
            json={"status": "closed_assisted"},
        )
        self.assertEqual(p.status_code, 422)

    def test_track4_supplier_flow_still_works_under_review(self) -> None:
        self.create_user(telegram_user_id=130_004)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_004,
                "request_type": "custom_route",
                "travel_date_start": "2026-09-15",
                "route_notes": "Regression path",
            },
        )
        rid = r.json()["id"]
        ur = self.client.post(
            f"/admin/custom-requests/{rid}/resolution",
            headers=self._headers_admin(),
            json={"status": "under_review"},
        )
        self.assertEqual(ur.status_code, 200, ur.text)

        _, token = self._bootstrap_supplier("S5A-REG")
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "Ok",
                "quoted_price": "10.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(put.status_code, 200, put.text)

    def test_my_requests_is_isolated_between_telegram_users(self) -> None:
        self.create_user(telegram_user_id=130_010)
        self.create_user(telegram_user_id=130_011)
        self.session.commit()

        r_a = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_010,
                "request_type": "other",
                "travel_date_start": "2026-11-20",
                "route_notes": "Request A",
            },
        )
        r_b = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 130_011,
                "request_type": "custom_route",
                "travel_date_start": "2026-11-21",
                "route_notes": "Request B",
            },
        )
        self.assertEqual(r_a.status_code, 201, r_a.text)
        self.assertEqual(r_b.status_code, 201, r_b.text)
        req_a = r_a.json()["id"]
        req_b = r_b.json()["id"]

        list_a = self.client.get("/mini-app/custom-requests", params={"telegram_user_id": 130_010})
        list_b = self.client.get("/mini-app/custom-requests", params={"telegram_user_id": 130_011})
        self.assertEqual(list_a.status_code, 200, list_a.text)
        self.assertEqual(list_b.status_code, 200, list_b.text)
        ids_a = {it["id"] for it in list_a.json()["items"]}
        ids_b = {it["id"] for it in list_b.json()["items"]}
        self.assertIn(req_a, ids_a)
        self.assertNotIn(req_b, ids_a)
        self.assertIn(req_b, ids_b)
        self.assertNotIn(req_a, ids_b)

        other_user_detail = self.client.get(
            f"/mini-app/custom-requests/{req_a}",
            params={"telegram_user_id": 130_011},
        )
        self.assertEqual(other_user_detail.status_code, 404)
