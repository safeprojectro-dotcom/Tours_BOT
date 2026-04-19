"""U3: My Requests customer IA — additive read fields + Romanian offers hint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class U3MyRequestsIATests(FoundationDBTestCase):
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

    def test_list_includes_identity_fields(self) -> None:
        tg = 190_001
        self.create_user(telegram_user_id=tg)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": tg,
                "request_type": "custom_route",
                "travel_date_start": "2026-08-10",
                "route_notes": "București – Brașov, weekend",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        lst = self.client.get("/mini-app/custom-requests", params={"telegram_user_id": tg})
        self.assertEqual(lst.status_code, 200, lst.text)
        item = lst.json()["items"][0]
        self.assertIn("created_at", item)
        self.assertEqual(item["request_type"], "custom_route")
        self.assertIn("route_notes_preview", item)
        self.assertIn("București", item["route_notes_preview"])

    def test_detail_includes_route_notes_and_ro_offers_hint(self) -> None:
        tg = 190_002
        self.create_user(telegram_user_id=tg, preferred_language="ro")
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": tg,
                "request_type": "group_trip",
                "travel_date_start": "2026-09-01",
                "route_notes": "Detaliu traseu complet pentru test U3.",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        rid = r.json()["id"]
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": tg})
        self.assertEqual(d.status_code, 200, d.text)
        body = d.json()
        self.assertEqual(body["route_notes"], "Detaliu traseu complet pentru test U3.")
        self.assertIn("Încă nu există", body["offers_received_hint"])
