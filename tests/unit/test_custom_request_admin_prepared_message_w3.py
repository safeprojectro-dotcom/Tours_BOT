"""W3: admin/internal prepared Mode 3 lifecycle message surface (no delivery semantics)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from tests.unit.base import FoundationDBTestCase


class CustomRequestAdminPreparedMessageW3Tests(FoundationDBTestCase):
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

    def _create_rfq(self, tg: int = 190_001) -> int:
        self.create_user(telegram_user_id=tg, preferred_language="en")
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": tg,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-05",
                "route_notes": "W3 admin prepared message",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    def test_admin_detail_includes_prepared_message_open(self) -> None:
        rid = self._create_rfq()
        d = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        self.assertEqual(d.status_code, 200, d.text)
        body = d.json()
        pcm = body.get("prepared_customer_lifecycle_message")
        self.assertIsNotNone(pcm)
        assert isinstance(pcm, dict)
        self.assertEqual(pcm.get("notification_event"), "custom_request_recorded")
        self.assertEqual(pcm.get("preparation_scope"), "message_preparation_only")
        self.assertTrue(pcm.get("not_sent_to_customer_channels"))
        self.assertTrue(pcm.get("not_enqueued_to_order_notification_outbox"))
        self.assertTrue(pcm.get("does_not_prove_customer_read_or_receipt"))
        self.assertTrue(pcm.get("matches_mini_app_detail_preview_basis"))
        low = (pcm.get("internal_disclaimer") or "").lower()
        self.assertTrue("internal" in low or "not been sent" in low or "outbox" in low)
        self.assertNotIn("delivered", low)
        self.assertNotIn("customer received", low)
        msg = (pcm.get("message") or "").lower()
        self.assertNotIn("payment is ready", msg)
        self.assertNotIn("booking is confirmed", msg)

    def test_admin_prepared_matches_mini_app_preview_event(self) -> None:
        rid = self._create_rfq(tg=190_002)
        adm = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        mini = self.client.get(
            f"/mini-app/custom-requests/{rid}",
            params={"telegram_user_id": 190_002},
        )
        self.assertEqual(adm.status_code, 200, adm.text)
        self.assertEqual(mini.status_code, 200, mini.text)
        a = adm.json().get("prepared_customer_lifecycle_message") or {}
        m = mini.json().get("activity_preview") or {}
        self.assertEqual(a.get("notification_event"), m.get("notification_event"))
        self.assertEqual(a.get("title"), m.get("title"))

    def test_supplier_detail_omits_prepared_message(self) -> None:
        rid = self._create_rfq(tg=190_003)
        token = self._bootstrap_supplier("W3-SUP", "W3 Supplier")
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "response_kind": "proposed",
                "supplier_message": "We can help",
                "quoted_price": "50.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "platform_checkout",
            },
        )
        self.assertEqual(put.status_code, 200, put.text)
        sup = self.client.get(
            f"/supplier-admin/custom-requests/{rid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(sup.status_code, 200, sup.text)
        self.assertIsNone(sup.json().get("prepared_customer_lifecycle_message"))
