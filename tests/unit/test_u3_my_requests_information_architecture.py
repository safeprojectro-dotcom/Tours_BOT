"""U3: My Requests information architecture — identity/read-side contract + Romanian shell keys."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from mini_app.ui_strings import shell
from tests.unit.base import FoundationDBTestCase


class U3MyRequestsInformationArchitectureTests(FoundationDBTestCase):
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

    def test_my_requests_list_includes_identity_fields(self) -> None:
        self.create_user(telegram_user_id=195_001, preferred_language="ro")
        self.session.commit()
        created = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 195_001,
                "request_type": "custom_route",
                "travel_date_start": "2026-12-04",
                "route_notes": "Cluj - Sibiu - Cluj, grup privat, plecare dimineața",
                "group_size": 18,
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        rid = created.json()["id"]

        listed = self.client.get("/mini-app/custom-requests", params={"telegram_user_id": 195_001})
        self.assertEqual(listed.status_code, 200, listed.text)
        row = next(x for x in listed.json()["items"] if x["id"] == rid)
        self.assertEqual(row["request_type"], "custom_route")
        self.assertEqual(row["travel_date_start"], "2026-12-04")
        self.assertIn("created_at", row)
        self.assertEqual(row["group_size"], 18)
        self.assertTrue((row.get("route_notes_preview") or "").strip())

    def test_my_request_detail_includes_header_identity_fields(self) -> None:
        self.create_user(telegram_user_id=195_002, preferred_language="ro")
        self.session.commit()
        created = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 195_002,
                "request_type": "group_trip",
                "travel_date_start": "2026-11-10",
                "travel_date_end": "2026-11-12",
                "route_notes": "Chișinău - Iași, transfer aeroport",
                "group_size": 12,
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        rid = created.json()["id"]

        detail = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 195_002})
        self.assertEqual(detail.status_code, 200, detail.text)
        body = detail.json()
        self.assertEqual(body["id"], rid)
        self.assertEqual(body["request_type"], "group_trip")
        self.assertIn("created_at", body)
        self.assertEqual(body["group_size"], 12)
        self.assertTrue((body.get("route_notes_preview") or "").strip())

    def test_romanian_u3_shell_keys_exist(self) -> None:
        keys = (
            "my_requests_row_reference",
            "my_requests_row_meta",
            "my_requests_section_what_you_asked",
            "my_requests_section_current_status",
            "my_requests_section_current_update",
            "my_requests_error_load_list",
            "my_requests_error_load_detail",
        )
        for key in keys:
            with self.subTest(key=key):
                self.assertTrue(shell("ro", key).strip())
