"""Track 5e: bridge supersede/cancel lifecycle — no Layer A mutation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.custom_request_booking_bridge import CustomRequestBookingBridge
from app.models.enums import (
    BookingStatus,
    CustomMarketplaceRequestStatus,
    CustomRequestBookingBridgeStatus,
    TourSalesMode,
    TourStatus,
)
from app.models.order import Order
from app.models.tour import BoardingPoint, Tour
from tests.unit.base import FoundationDBTestCase


class CustomRequestBookingBridgeTrack5ETests(FoundationDBTestCase):
    TG = 160_001

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

    def _bootstrap_supplier(self, code: str = "T5E-S1") -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": code, "display_name": "T5E Supplier"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def _rfq_selected(self) -> int:
        self.create_user(telegram_user_id=self.TG)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": self.TG,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "T5E RFQ",
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
                "supplier_message": "Proposal",
                "quoted_price": "1000.00",
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
        return rid

    def _make_tour(self, *, code: str, days_ahead: int = 120) -> Tour:
        dep = datetime.now(UTC) + timedelta(days=days_ahead)
        tour = Tour(
            code=code,
            title_default="T5E tour",
            short_description_default="x",
            full_description_default="y",
            duration_days=2,
            departure_datetime=dep,
            return_datetime=dep + timedelta(days=2),
            base_price=Decimal("99.00"),
            currency="EUR",
            seats_total=40,
            seats_available=20,
            sales_deadline=dep - timedelta(days=1),
            status=TourStatus.OPEN_FOR_SALE,
            sales_mode=TourSalesMode.PER_SEAT,
        )
        self.session.add(tour)
        self.session.flush()
        bp = BoardingPoint(
            tour_id=tour.id,
            city="City",
            address="Addr",
            time=(dep.replace(tzinfo=None).time()),
        )
        self.session.add(bp)
        self.session.flush()
        return tour

    def _create_linked_bridge(self, rid: int, tour_id: int) -> None:
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour_id, "admin_note": "active"},
        )
        self.assertEqual(br.status_code, 201, br.text)

    def test_close_active_to_superseded(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-SUP")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        cl = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "superseded", "admin_note": "replaced"},
        )
        self.assertEqual(cl.status_code, 200, cl.text)
        body = cl.json()
        self.assertEqual(body["bridge_status"], "superseded")
        self.assertEqual(body["admin_note"], "replaced")

    def test_close_active_to_cancelled(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-CAN")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        cl = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.assertEqual(cl.status_code, 200, cl.text)
        self.assertEqual(cl.json()["bridge_status"], "cancelled")

    def test_close_without_active_returns_404(self) -> None:
        rid = self._rfq_selected()
        self.session.commit()
        cl = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.assertEqual(cl.status_code, 404, cl.text)

    def test_double_close_returns_404(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-DBL")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        cl1 = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.assertEqual(cl1.status_code, 200, cl1.text)
        cl2 = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.assertEqual(cl2.status_code, 404, cl2.text)

    def test_preparation_404_when_bridge_cancelled(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-PREP")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.session.commit()
        pr = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG},
        )
        self.assertEqual(pr.status_code, 404, pr.text)

    def test_reservation_404_when_bridge_superseded(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-RES")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "superseded"},
        )
        self.session.commit()
        bp_id = self.session.scalars(select(BoardingPoint.id).where(BoardingPoint.tour_id == tour.id)).first()
        rv = self.client.post(
            f"/mini-app/custom-requests/{rid}/booking-bridge/reservations",
            json={
                "telegram_user_id": self.TG,
                "seats_count": 1,
                "boarding_point_id": bp_id,
            },
        )
        self.assertEqual(rv.status_code, 404, rv.text)

    def test_payment_eligibility_404_when_bridge_cancelled(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-PAY")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        bp_id = self.session.scalars(select(BoardingPoint.id).where(BoardingPoint.tour_id == tour.id)).first()
        hold = self.client.post(
            f"/mini-app/custom-requests/{rid}/booking-bridge/reservations",
            json={
                "telegram_user_id": self.TG,
                "seats_count": 1,
                "boarding_point_id": bp_id,
            },
        )
        self.assertEqual(hold.status_code, 200, hold.text)
        order_id = hold.json()["order"]["id"]
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.session.commit()
        pe = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": order_id},
        )
        self.assertEqual(pe.status_code, 404, pe.text)

    def test_request_status_unchanged_after_close(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-ST")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        before = self.session.get(CustomMarketplaceRequest, rid)
        assert before is not None
        self.assertEqual(before.status, CustomMarketplaceRequestStatus.SUPPLIER_SELECTED)
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "superseded"},
        )
        self.session.commit()
        self.session.expire_all()
        after = self.session.get(CustomMarketplaceRequest, rid)
        assert after is not None
        self.assertEqual(after.status, CustomMarketplaceRequestStatus.SUPPLIER_SELECTED)

    def test_order_unchanged_after_bridge_close(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-ORD")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        bp_id = self.session.scalars(select(BoardingPoint.id).where(BoardingPoint.tour_id == tour.id)).first()
        hold = self.client.post(
            f"/mini-app/custom-requests/{rid}/booking-bridge/reservations",
            json={
                "telegram_user_id": self.TG,
                "seats_count": 1,
                "boarding_point_id": bp_id,
            },
        )
        self.assertEqual(hold.status_code, 200, hold.text)
        order_id = hold.json()["order"]["id"]
        ord_row = self.session.get(Order, order_id)
        assert ord_row is not None
        bs_before = ord_row.booking_status
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.session.commit()
        self.session.expire_all()
        ord_after = self.session.get(Order, order_id)
        assert ord_after is not None
        self.assertEqual(ord_after.booking_status, bs_before)
        self.assertEqual(ord_after.booking_status, BookingStatus.RESERVED)

    def test_replace_supersedes_and_creates_new_bridge(self) -> None:
        rid = self._rfq_selected()
        t1 = self._make_tour(code="T5E-R1")
        t2 = self._make_tour(code="T5E-R2")
        self.session.commit()
        self._create_linked_bridge(rid, t1.id)
        rep = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/replace",
            headers=self._headers_admin(),
            json={
                "tour_id": t2.id,
                "admin_note": "new row",
                "supersede_note": "moving tour",
            },
        )
        self.assertEqual(rep.status_code, 201, rep.text)
        self.assertEqual(rep.json()["tour_id"], t2.id)
        self.assertEqual(rep.json()["bridge_status"], "linked_tour")
        adm = self.client.get(f"/admin/custom-requests/{rid}", headers=self._headers_admin())
        self.assertEqual(adm.status_code, 200, adm.text)
        bb = adm.json()["booking_bridge"]
        self.assertEqual(bb["tour_id"], t2.id)
        all_br = self.session.scalars(
            select(CustomRequestBookingBridge).where(CustomRequestBookingBridge.request_id == rid)
        ).all()
        self.assertEqual(len(all_br), 2)
        statuses = {b.bridge_status for b in all_br}
        self.assertIn(CustomRequestBookingBridgeStatus.SUPERSEDED, statuses)
        self.assertIn(CustomRequestBookingBridgeStatus.LINKED_TOUR, statuses)

    def test_replace_without_prior_active_creates_bridge(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-REP0")
        self.session.commit()
        rep = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/replace",
            headers=self._headers_admin(),
            json={"tour_id": tour.id, "admin_note": "first via replace"},
        )
        self.assertEqual(rep.status_code, 201, rep.text)
        self.assertEqual(rep.json()["tour_id"], tour.id)

    def test_mini_app_detail_includes_terminal_bridge_status(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="T5E-DET")
        self.session.commit()
        self._create_linked_bridge(rid, tour.id)
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge/close",
            headers=self._headers_admin(),
            json={"terminal_status": "cancelled"},
        )
        self.session.commit()
        d = self.client.get(f"/mini-app/custom-requests/{rid}", params={"telegram_user_id": self.TG})
        self.assertEqual(d.status_code, 200, d.text)
        self.assertEqual(d.json()["latest_booking_bridge_status"], "cancelled")
        self.assertEqual(d.json()["latest_booking_bridge_tour_code"], tour.code)
