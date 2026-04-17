"""Track 5b.1: RFQ booking bridge record — no Layer A execution."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourStatus
from app.models.order import Order
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class CustomRequestBookingBridgeTrack5B1Tests(FoundationDBTestCase):
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
            json={"code": "BR-S1", "display_name": "Bridge Supplier"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def _rfq_with_selected_proposal(self) -> tuple[int, int]:
        self.create_user(telegram_user_id=140_001)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 140_001,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "Bridge test RFQ",
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
                "supplier_message": "We can run this charter.",
                "quoted_price": "1500.00",
                "quoted_currency": "EUR",
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
        return rid, resp_id

    def test_bridge_create_success_and_detail_includes_bridge(self) -> None:
        rid, _ = self._rfq_with_selected_proposal()
        n_orders_before = self.session.scalar(select(func.count()).select_from(Order))

        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"admin_note": "Intent only — no hold."},
        )
        self.assertEqual(br.status_code, 201, br.text)
        body = br.json()
        self.assertEqual(body["request_id"], rid)
        self.assertEqual(body["bridge_status"], "ready")
        self.assertIsNone(body["tour_id"])

        n_orders_after = self.session.scalar(select(func.count()).select_from(Order))
        self.assertEqual(n_orders_before, n_orders_after)

        detail = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        self.assertEqual(detail.status_code, 200)
        bb = detail.json().get("booking_bridge")
        self.assertIsNotNone(bb)
        self.assertEqual(bb["id"], body["id"])

    def test_bridge_rejected_without_selection(self) -> None:
        self.create_user(telegram_user_id=140_002)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": 140_002,
                "request_type": "other",
                "travel_date_start": "2026-11-15",
                "route_notes": "No winner yet",
            },
        )
        rid = r.json()["id"]
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={},
        )
        self.assertEqual(br.status_code, 400, br.text)

    def test_bridge_conflict_when_active_exists(self) -> None:
        rid, _ = self._rfq_with_selected_proposal()
        a = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={},
        )
        self.assertEqual(a.status_code, 201, a.text)
        b = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={},
        )
        self.assertEqual(b.status_code, 409, b.text)

    def test_bridge_with_valid_tour_linked(self) -> None:
        rid, _ = self._rfq_with_selected_proposal()
        dep = datetime.now(UTC) + timedelta(days=90)
        tour = Tour(
            code="BRIDGE-TOUR-1",
            title_default="Bridge link tour",
            short_description_default="x",
            full_description_default="y",
            duration_days=2,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=2),
            base_price=Decimal("120.00"),
            currency="EUR",
            seats_total=40,
            seats_available=20,
            sales_deadline=dep - timedelta(days=1),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.session.add(tour)
        self.session.flush()

        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        self.assertEqual(br.status_code, 201, br.text)
        self.assertEqual(br.json()["bridge_status"], "linked_tour")
        self.assertEqual(br.json()["tour_id"], tour.id)

    def test_bridge_rejects_stale_tour(self) -> None:
        rid, _ = self._rfq_with_selected_proposal()
        dep = datetime.now(UTC) - timedelta(days=1)
        tour = Tour(
            code="BRIDGE-TOUR-PAST",
            title_default="Past",
            short_description_default="x",
            full_description_default="y",
            duration_days=1,
            departure_datetime=dep,
            return_datetime=dep + timedelta(hours=12),
            base_price=Decimal("50.00"),
            currency="EUR",
            seats_total=10,
            seats_available=5,
            sales_deadline=dep - timedelta(days=2),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.session.add(tour)
        self.session.flush()

        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        self.assertEqual(br.status_code, 400, br.text)
        self.assertIn("future", br.json()["detail"].lower())

    def test_patch_bridge_adds_tour(self) -> None:
        rid, _ = self._rfq_with_selected_proposal()
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={},
        )
        dep = datetime.now(UTC) + timedelta(days=60)
        tour = Tour(
            code="BRIDGE-TOUR-PATCH",
            title_default="Patch tour",
            short_description_default="x",
            full_description_default="y",
            duration_days=1,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=1),
            base_price=Decimal("80.00"),
            currency="EUR",
            seats_total=30,
            seats_available=10,
            sales_deadline=dep - timedelta(hours=12),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.session.add(tour)
        self.session.flush()

        p = self.client.patch(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        self.assertEqual(p.status_code, 200, p.text)
        self.assertEqual(p.json()["bridge_status"], "linked_tour")
