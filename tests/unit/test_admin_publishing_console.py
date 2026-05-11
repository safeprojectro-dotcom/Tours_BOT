"""B15B: GET /admin/publishing-console read-only publishing queue."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class AdminPublishingConsoleTests(FoundationDBTestCase):
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

    def test_publishing_console_401_without_token(self) -> None:
        r = self.client.get("/admin/publishing-console")
        self.assertEqual(r.status_code, 401)

    def test_publishing_console_smoke_shape(self) -> None:
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(
                "/admin/publishing-console",
                headers={"Authorization": "Bearer test-admin-secret"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIn("items", body)
        self.assertIn("total_returned", body)
        self.assertIn("console_notice", body)
        self.assertIn("debug_notice", body)
        self.assertIsInstance(body["items"], list)
        self.assertIn("Read-only", body["console_notice"])

    def test_publishing_console_kind_supplier_offer_only(self) -> None:
        mock_cfg = SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(
                "/admin/publishing-console?kind=supplier_offer_initial&limit=5",
                headers={"Authorization": "Bearer test-admin-secret"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        for item in r.json()["items"]:
            self.assertEqual(item["kind"], "supplier_offer_initial")

    def test_publishing_console_kind_tour_only(self) -> None:
        r = self.client.get(
            "/admin/publishing-console?kind=tour_promotion&limit=5",
            headers={"Authorization": "Bearer test-admin-secret"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        for item in r.json()["items"]:
            self.assertEqual(item["kind"], "tour_promotion")
            self.assertIn("tour_debug", item)
            self.assertIsNone(item["offer_debug"])
