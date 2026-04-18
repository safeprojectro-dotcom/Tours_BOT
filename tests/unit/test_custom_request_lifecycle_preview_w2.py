"""W2: Mini App read surface for Mode 3 lifecycle preview (W1-backed; no delivery)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import CustomMarketplaceRequestStatus, CustomRequestBookingBridgeStatus
from app.repositories.custom_marketplace import CustomMarketplaceRequestRepository
from app.services.custom_request_lifecycle_preview import CustomRequestLifecyclePreviewService
from tests.unit.base import FoundationDBTestCase


class CustomRequestLifecyclePreviewW2Tests(FoundationDBTestCase):
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

    def _create_open_rfq(self, tg: int = 180_001) -> int:
        self.create_user(telegram_user_id=tg, preferred_language="en")
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": tg,
                "request_type": "group_trip",
                "travel_date_start": "2026-11-10",
                "route_notes": "W2 preview",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    def test_service_preview_open_matches_recorded(self) -> None:
        rid = self._create_open_rfq()
        svc = CustomRequestLifecyclePreviewService()
        prev = svc.detail_activity_preview(
            self.session,
            request_id=rid,
            bridge_status=None,
            language_code="en",
        )
        self.assertIsNotNone(prev)
        assert prev is not None
        self.assertEqual(prev.notification_event, "custom_request_recorded")
        self.assertTrue(prev.in_app_preview_only)
        low = prev.preview_disclaimer.lower()
        self.assertIn("mini app", low)
        self.assertNotIn("we sent", low)
        self.assertNotIn("notified you", low)

    def test_service_list_title_supplier_selected_without_followup_bridge(self) -> None:
        rid = self._create_open_rfq()
        _, token = self._bootstrap_supplier("W2-S1", "W2 Supp")
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "response_kind": "proposed",
                "supplier_message": "OK",
                "quoted_price": "100.00",
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
        svc = CustomRequestLifecyclePreviewService()
        title = svc.list_activity_title(self.session, request_id=rid, language_code="en")
        self.assertIsNotNone(title)
        detail = svc.detail_activity_preview(
            self.session,
            request_id=rid,
            bridge_status=None,
            language_code="en",
        )
        assert detail is not None
        self.assertEqual(detail.notification_event, "custom_request_selection_recorded")
        self.assertEqual(title, detail.title)

    def test_service_detail_followup_when_bridge_ready(self) -> None:
        rid = self._create_open_rfq()
        _, token = self._bootstrap_supplier("W2-S2", "W2 Supp2")
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "response_kind": "proposed",
                "supplier_message": "OK",
                "quoted_price": "200.00",
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
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"admin_note": "W2 test"},
        )
        self.assertEqual(br.status_code, 201, br.text)
        self.assertEqual(br.json()["bridge_status"], "ready")
        svc = CustomRequestLifecyclePreviewService()
        detail = svc.detail_activity_preview(
            self.session,
            request_id=rid,
            bridge_status=CustomRequestBookingBridgeStatus.READY,
            language_code="en",
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail.notification_event, "custom_request_app_followup_may_exist")
        list_title = svc.list_activity_title(self.session, request_id=rid, language_code="en")
        self.assertNotEqual((list_title or "").lower(), detail.title.lower())

    def test_mini_app_api_detail_and_list_include_preview_fields(self) -> None:
        rid = self._create_open_rfq(tg=180_002)
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": 180_002})
        self.assertEqual(d.status_code, 200, d.text)
        body = d.json()
        ap = body.get("activity_preview")
        self.assertIsNotNone(ap)
        assert isinstance(ap, dict)
        self.assertEqual(ap.get("notification_event"), "custom_request_recorded")
        self.assertTrue(ap.get("in_app_preview_only"))
        self.assertIn("title", ap)
        self.assertIn("message", ap)
        self.assertIn("preview_disclaimer", ap)

        lst = self.client.get("/mini-app/custom-requests", params={"telegram_user_id": 180_002})
        self.assertEqual(lst.status_code, 200, lst.text)
        items = lst.json().get("items") or []
        self.assertEqual(len(items), 1)
        self.assertIn("activity_preview_title", items[0])
        self.assertIsNotNone(items[0]["activity_preview_title"])

    def test_preview_message_does_not_claim_booking_confirmed(self) -> None:
        rid = self._create_open_rfq(tg=180_003)
        row = CustomMarketplaceRequestRepository().get(self.session, request_id=rid)
        assert row is not None
        row.status = CustomMarketplaceRequestStatus.UNDER_REVIEW
        self.session.commit()
        prev = CustomRequestLifecyclePreviewService().detail_activity_preview(
            self.session,
            request_id=rid,
            bridge_status=None,
            language_code="en",
        )
        assert prev is not None
        low = prev.message.lower()
        self.assertNotIn("booking is confirmed", low)
        self.assertNotIn("payment is ready", low)
