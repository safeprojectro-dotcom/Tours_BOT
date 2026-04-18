"""X1: supplier portal request handling clarity (read-only hints)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class SupplierPortalHintsX1Tests(FoundationDBTestCase):
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

    def _bootstrap_supplier(self, code: str, name: str) -> str:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": code, "display_name": name},
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["api_token"]

    def test_open_no_response_actionable_and_no_admin_leak(self) -> None:
        self.create_user(telegram_user_id=200_001)
        self.session.commit()
        cr = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 200_001,
                "request_type": "custom_route",
                "travel_date_start": "2026-11-20",
                "route_notes": "Scenic route with two stops",
                "group_size": 30,
            },
        )
        self.assertEqual(cr.status_code, 201, cr.text)
        rid = cr.json()["id"]
        token = self._bootstrap_supplier("X1-A", "X1 Supplier A")
        sh = {"Authorization": f"Bearer {token}"}
        lst = self.client.get("/supplier-admin/custom-requests", headers=sh)
        self.assertEqual(lst.status_code, 200, lst.text)
        row = next(x for x in lst.json()["items"] if x["id"] == rid)
        self.assertIsNone(row.get("operational_hints"))
        h = row.get("supplier_portal_hints")
        self.assertIsNotNone(h)
        assert isinstance(h, dict)
        self.assertTrue(h.get("can_submit_or_update_response"))
        self.assertFalse(h.get("supplier_has_responded"))
        self.assertEqual(h.get("portal_action_state"), "open_actionable_no_response_yet")
        self.assertIn("custom route", h.get("request_summary_line", "").lower())
        self.assertIn("30", h.get("request_summary_line", ""))
        self.assertNotIn("operational", str(h).lower())
        self.assertNotIn("bridge_continuation", str(h).lower())
        self.assertNotIn("handling_hint", str(h).lower())
        rw = h.get("response_workflow") or {}
        self.assertEqual(rw.get("your_response_state"), "none_yet")
        self.assertIn("no response", (rw.get("response_presence_one_liner") or "").lower())
        self.assertNotIn("operational_hints", str(rw))

        adm = self.client.get("/admin/custom-requests", headers=self._headers_admin())
        adm_row = next(x for x in adm.json()["items"] if x["id"] == rid)
        self.assertIsNone(adm_row.get("supplier_portal_hints"))
        self.assertIsNotNone(adm_row.get("operational_hints"))

    def test_after_proposal_still_actionable_open(self) -> None:
        self.create_user(telegram_user_id=200_002)
        self.session.commit()
        rid = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 200_002,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "Day trip",
            },
        ).json()["id"]
        token = self._bootstrap_supplier("X1-B", "X1 Supplier B")
        sh = {"Authorization": f"Bearer {token}"}
        self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "We can do it",
                "quoted_price": "100.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        lst = self.client.get("/supplier-admin/custom-requests", headers=sh)
        h = next(x for x in lst.json()["items"] if x["id"] == rid)["supplier_portal_hints"]
        self.assertTrue(h.get("supplier_has_responded"))
        self.assertEqual(h.get("supplier_last_response_kind"), "proposed")
        self.assertEqual(h.get("portal_action_state"), "open_actionable_has_response")
        self.assertTrue(h.get("can_submit_or_update_response"))
        rw = h.get("response_workflow") or {}
        self.assertEqual(rw.get("your_response_state"), "proposal_on_file")
        self.assertIn("priced proposal", (rw.get("response_presence_one_liner") or "").lower())
        low = (rw.get("response_kind_explained") or "").lower()
        self.assertNotIn("payment confirmed", low)
        self.assertNotIn("booking confirmed", low)

    def test_under_review_still_actionable(self) -> None:
        self.create_user(telegram_user_id=200_003)
        self.session.commit()
        rid = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 200_003,
                "request_type": "other",
                "travel_date_start": "2026-12-15",
                "route_notes": "Corporate",
            },
        ).json()["id"]
        token = self._bootstrap_supplier("X1-C", "X1 Supplier C")
        sh = {"Authorization": f"Bearer {token}"}
        self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "declined",
                "supplier_message": "No capacity",
            },
        )
        self.client.patch(
            f"/admin/custom-requests/{rid}",
            headers=self._headers_admin(),
            json={"status": "under_review"},
        )
        lst = self.client.get("/supplier-admin/custom-requests", headers=sh)
        h = next(x for x in lst.json()["items"] if x["id"] == rid)["supplier_portal_hints"]
        self.assertEqual(h.get("portal_action_state"), "under_review_actionable")
        self.assertTrue(h.get("can_submit_or_update_response"))
        rw = h.get("response_workflow") or {}
        self.assertEqual(rw.get("your_response_state"), "decline_on_file")
        self.assertIn("edit", (rw.get("editability_one_liner") or "").lower())

    def test_selected_read_only_and_selected_flag(self) -> None:
        self.create_user(telegram_user_id=200_004)
        self.session.commit()
        rid = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 200_004,
                "request_type": "group_trip",
                "travel_date_start": "2026-10-20",
                "route_notes": "Winning bid scenario",
            },
        ).json()["id"]
        token = self._bootstrap_supplier("X1-W", "X1 Winner")
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "Best offer",
                "quoted_price": "500.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        resp_id = put.json()["id"]
        self.client.post(
            f"/admin/custom-requests/{rid}/resolution",
            headers=self._headers_admin(),
            json={"status": "supplier_selected", "selected_supplier_response_id": resp_id},
        )
        detail = self.client.get(f"/supplier-admin/custom-requests/{rid}", headers=sh)
        self.assertEqual(detail.status_code, 200, detail.text)
        h = detail.json()["request"]["supplier_portal_hints"]
        self.assertFalse(h.get("can_submit_or_update_response"))
        self.assertEqual(h.get("portal_action_state"), "read_only_selection_recorded")
        self.assertTrue(h.get("your_response_was_selected"))
        low = (h.get("portal_action_state_detail") or "").lower()
        self.assertNotIn("payment", low)
        self.assertNotIn("checkout", low)
        rw = h.get("response_workflow") or {}
        self.assertEqual(rw.get("your_response_state"), "proposal_was_selected")
        self.assertFalse(h.get("can_submit_or_update_response"))
        rw_low = (rw.get("what_happens_next") or "").lower()
        self.assertNotIn("payment", rw_low)
        self.assertNotIn("ticket", rw_low)

    def test_detail_matches_list_hints(self) -> None:
        self.create_user(telegram_user_id=200_005)
        self.session.commit()
        rid = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 200_005,
                "request_type": "group_trip",
                "travel_date_start": "2026-09-09",
                "route_notes": "Consistency check",
            },
        ).json()["id"]
        token = self._bootstrap_supplier("X1-D", "X1 Supplier D")
        sh = {"Authorization": f"Bearer {token}"}
        lst_h = next(x for x in self.client.get("/supplier-admin/custom-requests", headers=sh).json()["items"] if x["id"] == rid)["supplier_portal_hints"]
        det_h = self.client.get(f"/supplier-admin/custom-requests/{rid}", headers=sh).json()["request"]["supplier_portal_hints"]
        self.assertEqual(lst_h.get("portal_action_state"), det_h.get("portal_action_state"))
        self.assertEqual(lst_h.get("request_summary_line"), det_h.get("request_summary_line"))
        lrw = lst_h.get("response_workflow") or {}
        drw = det_h.get("response_workflow") or {}
        self.assertEqual(lrw.get("your_response_state"), drw.get("your_response_state"))
