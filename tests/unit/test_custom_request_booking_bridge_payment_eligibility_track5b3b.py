"""Track 5b.3b: bridge-scoped payment eligibility read — Layer A payment-entry unchanged."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourSalesMode, TourStatus
from app.models.order import Order
from app.models.payment import Payment
from app.models.tour import BoardingPoint, Tour, TourTranslation
from tests.unit.base import FoundationDBTestCase


class CustomRequestBookingBridgePaymentEligibilityTrack5B3BTests(FoundationDBTestCase):
    TG = 155_001

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

    def _bootstrap_supplier(self, code: str = "PAY-S1") -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": code, "display_name": "Pay Eligibility Supplier"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def _rfq_selected_platform_checkout(self) -> int:
        self.create_user(telegram_user_id=self.TG)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": self.TG,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "Pay elig RFQ",
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

    def _rfq_selected_assisted(self) -> int:
        self.create_user(telegram_user_id=self.TG)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": self.TG,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "Pay elig assisted",
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        rid = r.json()["id"]
        _, token = self._bootstrap_supplier("PAY-ASST")
        sh = {"Authorization": f"Bearer {token}"}
        put = self.client.put(
            f"/supplier-admin/custom-requests/{rid}/response",
            headers=sh,
            json={
                "response_kind": "proposed",
                "supplier_message": "Assisted",
                "quoted_price": "1000.00",
                "quoted_currency": "EUR",
                "supplier_declared_sales_mode": "per_seat",
                "supplier_declared_payment_mode": "assisted_closure",
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
            title_default="Pay elig tour",
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
        return tour

    def _bridge_hold_order_id(self, rid: int, *, tour_code: str = "PAY-ELIG-T1") -> tuple[int, int]:
        tour = self._make_tour(code=tour_code)
        from datetime import time as time_type

        self.session.add(
            TourTranslation(
                tour_id=tour.id,
                language_code="en",
                title="EN",
                short_description="s",
                full_description="f",
                program_text="p",
                included_text="i",
                excluded_text="e",
            ),
        )
        bp = BoardingPoint(tour_id=tour.id, city="City", address="Addr", time=time_type(6, 0))
        self.session.add(bp)
        self.session.flush()
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        res = self.client.post(
            f"/mini-app/custom-requests/{rid}/booking-bridge/reservations",
            params={"language_code": "en"},
            json={
                "telegram_user_id": self.TG,
                "seats_count": 1,
                "boarding_point_id": bp.id,
            },
        )
        self.assertEqual(res.status_code, 200, res.text)
        oid = res.json()["order"]["id"]
        return oid, tour.id

    def test_payment_eligibility_allowed_then_existing_payment_entry_works(self) -> None:
        rid = self._rfq_selected_platform_checkout()
        oid, _ = self._bridge_hold_order_id(rid)
        elig = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": oid},
        )
        self.assertEqual(elig.status_code, 200, elig.text)
        body = elig.json()
        self.assertTrue(body["payment_entry_allowed"])
        self.assertEqual(body["order_id"], oid)
        self.assertTrue(body["effective_execution_policy"]["platform_checkout_allowed"])
        self.assertIsNone(body["blocked_code"])

        pay = self.client.post(
            f"/mini-app/orders/{oid}/payment-entry",
            json={"telegram_user_id": self.TG},
        )
        self.assertEqual(pay.status_code, 200, pay.text)
        self.assertIn("payment_session_reference", pay.json())

    def test_payment_eligibility_read_does_not_create_payment_rows(self) -> None:
        rid = self._rfq_selected_platform_checkout()
        oid, _ = self._bridge_hold_order_id(rid, tour_code="PAY-ELIG-T2")
        n_before = self.session.scalar(select(func.count()).select_from(Payment))
        r1 = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": oid},
        )
        r2 = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": oid},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        n_after = self.session.scalar(select(func.count()).select_from(Payment))
        self.assertEqual(n_before, n_after)

    def test_assisted_supplier_blocks_payment_eligibility(self) -> None:
        rid = self._rfq_selected_assisted()
        tour = self._make_tour(code="PAY-ASST-T")
        from datetime import time as time_type

        bp = BoardingPoint(tour_id=tour.id, city="C", address="A", time=time_type(7, 0))
        self.session.add(bp)
        self.session.flush()
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        elig = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": 1},
        )
        self.assertEqual(elig.status_code, 200, elig.text)
        b = elig.json()
        self.assertFalse(b["payment_entry_allowed"])
        self.assertIsNone(b["order_id"])
        self.assertFalse(b["effective_execution_policy"]["platform_checkout_allowed"])
        self.assertEqual(b["blocked_code"], "supplier_commercial_intent_blocks_self_service")

    def test_order_not_found_and_expired_and_tour_mismatch(self) -> None:
        rid = self._rfq_selected_platform_checkout()
        oid, tid = self._bridge_hold_order_id(rid, tour_code="PAY-ELIG-T3")

        bad = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": 9_999_999},
        )
        self.assertEqual(bad.status_code, 200, bad.text)
        self.assertEqual(bad.json()["blocked_code"], "order_not_found")

        other = self._make_tour(code="OTHER-TOUR-PAY")
        from datetime import time as time_type

        obp = BoardingPoint(tour_id=other.id, city="O", address="O", time=time_type(8, 0))
        self.session.add(obp)
        self.session.flush()
        o_row = self.session.get(Order, oid)
        assert o_row is not None
        o_row.tour_id = other.id
        self.session.add(o_row)
        self.session.flush()
        mis = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": oid},
        )
        self.assertEqual(mis.status_code, 200, mis.text)
        self.assertEqual(mis.json()["blocked_code"], "order_bridge_tour_mismatch")

        o_row.tour_id = tid
        self.session.add(o_row)
        self.session.flush()
        o_row = self.session.get(Order, oid)
        assert o_row is not None
        o_row.reservation_expires_at = datetime.now(UTC) - timedelta(minutes=1)
        self.session.add(o_row)
        self.session.flush()
        exp = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/payment-eligibility",
            params={"telegram_user_id": self.TG, "order_id": oid},
        )
        self.assertEqual(exp.status_code, 200, exp.text)
        self.assertEqual(exp.json()["blocked_code"], "order_not_valid_for_payment")
