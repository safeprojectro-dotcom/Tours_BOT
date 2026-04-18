"""Track 5b.2: RFQ bridge → Layer A preparation + hold (explicit entry only)."""

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


class CustomRequestBookingBridgeExecutionTrack5B2Tests(FoundationDBTestCase):
    TG = 150_001

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

    def _bootstrap_supplier(self, code: str = "EX-S1") -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers=self._headers_admin(),
            json={"code": code, "display_name": "Exec Supplier"},
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
                "route_notes": "Exec test RFQ",
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

    def _rfq_selected_assisted_supplier(self) -> int:
        """Per-seat tour capability later; supplier declares assisted closure (no platform self-serve)."""
        self.create_user(telegram_user_id=self.TG)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": self.TG,
                "request_type": "group_trip",
                "travel_date_start": "2026-12-01",
                "route_notes": "Exec test RFQ assisted",
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
                "supplier_message": "We will close with your team.",
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

    def _make_tour(
        self,
        *,
        code: str,
        sales_mode: TourSalesMode = TourSalesMode.PER_SEAT,
        days_ahead: int = 120,
    ) -> Tour:
        dep = datetime.now(UTC) + timedelta(days=days_ahead)
        tour = Tour(
            code=code,
            title_default="Exec tour",
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
            sales_mode=sales_mode,
        )
        self.session.add(tour)
        self.session.flush()
        return tour

    def test_preparation_404_when_no_active_bridge(self) -> None:
        self.create_user(telegram_user_id=self.TG)
        self.session.commit()
        r = self.client.post(
            "/mini-app/custom-requests",
            json={
                "telegram_user_id": self.TG,
                "request_type": "other",
                "travel_date_start": "2026-11-01",
                "route_notes": "No bridge",
            },
        )
        rid = r.json()["id"]
        prep = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG},
        )
        self.assertEqual(prep.status_code, 404, prep.text)

    def test_preparation_400_when_bridge_has_no_tour(self) -> None:
        rid = self._rfq_selected()
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"admin_note": "no tour"},
        )
        self.assertEqual(br.status_code, 201, br.text)
        prep = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG},
        )
        self.assertEqual(prep.status_code, 400, prep.text)
        self.assertIn("linked tour", prep.json()["detail"].lower())

    def test_preparation_blocked_for_full_bus_tour(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="EX-FULL-BUS", sales_mode=TourSalesMode.FULL_BUS)
        from datetime import time as time_type

        self.session.add(
            BoardingPoint(
                tour_id=tour.id,
                city="City",
                address="Addr",
                time=time_type(6, 0),
            ),
        )
        self.session.flush()
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        self.assertEqual(br.status_code, 201, br.text)
        prep = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG},
        )
        self.assertEqual(prep.status_code, 200, prep.text)
        body = prep.json()
        self.assertFalse(body["self_service_available"])
        self.assertEqual(body["blocked_code"], "operator_assistance_required")
        self.assertIsNone(body["preparation"])
        self.assertFalse(body["sales_mode_policy"]["per_seat_self_service_allowed"])
        eff = body["effective_execution_policy"]
        self.assertFalse(eff["self_service_hold_allowed"])
        self.assertFalse(eff["platform_checkout_allowed"])
        self.assertEqual(eff["blocked_code"], "tour_sales_mode_blocks_self_service")

    def test_preparation_blocked_when_supplier_declares_assisted_on_per_seat_tour(self) -> None:
        rid = self._rfq_selected_assisted_supplier()
        tour = self._make_tour(code="EX-ASSIST-BLOCK", sales_mode=TourSalesMode.PER_SEAT)
        from datetime import time as time_type

        self.session.add(
            BoardingPoint(tour_id=tour.id, city="City", address="Addr", time=time_type(6, 0)),
        )
        self.session.flush()
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        self.assertEqual(br.status_code, 201, br.text)
        prep = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG},
        )
        self.assertEqual(prep.status_code, 200, prep.text)
        body = prep.json()
        self.assertFalse(body["self_service_available"])
        self.assertEqual(body["blocked_code"], "operator_assistance_required")
        eff = body["effective_execution_policy"]
        self.assertFalse(eff["self_service_hold_allowed"])
        self.assertFalse(eff["platform_checkout_allowed"])
        self.assertTrue(eff["assisted_only"])
        self.assertEqual(eff["blocked_code"], "supplier_commercial_intent_blocks_self_service")

    def test_preparation_self_service_returns_layer_a_preparation(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="EX-PER-SEAT", sales_mode=TourSalesMode.PER_SEAT)
        from datetime import time as time_type

        self.session.add(
            BoardingPoint(tour_id=tour.id, city="City", address="Addr", time=time_type(6, 0)),
        )
        self.session.flush()
        br = self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        self.assertEqual(br.status_code, 201, br.text)
        prep = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG, "language_code": "en"},
        )
        self.assertEqual(prep.status_code, 200, prep.text)
        body = prep.json()
        self.assertTrue(body["self_service_available"])
        self.assertIsNotNone(body["preparation"])
        self.assertEqual(body["preparation"]["tour"]["code"], tour.code)
        self.assertTrue(body["sales_mode_policy"]["per_seat_self_service_allowed"])
        eff = body["effective_execution_policy"]
        self.assertTrue(eff["self_service_hold_allowed"])
        self.assertTrue(eff["platform_checkout_allowed"])
        self.assertFalse(eff["assisted_only"])

    def test_reservation_rejected_for_full_bus_no_hold(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="EX-FB-RES", sales_mode=TourSalesMode.FULL_BUS)
        from datetime import time as time_type

        bp = BoardingPoint(tour_id=tour.id, city="City", address="Addr", time=time_type(6, 0))
        self.session.add(bp)
        self.session.flush()
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        n_orders = self.session.scalar(select(func.count()).select_from(Order))
        res = self.client.post(
            f"/mini-app/custom-requests/{rid}/booking-bridge/reservations",
            params={"language_code": "en"},
            json={
                "telegram_user_id": self.TG,
                "seats_count": 1,
                "boarding_point_id": bp.id,
            },
        )
        self.assertEqual(res.status_code, 400, res.text)
        detail = res.json()["detail"]
        self.assertEqual(detail["code"], "operator_assistance_required")
        n_orders_after = self.session.scalar(select(func.count()).select_from(Order))
        self.assertEqual(n_orders, n_orders_after)

    def test_reservation_per_seat_creates_hold_without_payment_rows(self) -> None:
        rid = self._rfq_selected()
        tour = self._make_tour(code="EX-PER-RES", sales_mode=TourSalesMode.PER_SEAT)
        from datetime import time as time_type

        self.session.add(
            TourTranslation(
                tour_id=tour.id,
                language_code="en",
                title="Exec EN",
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
        n_pay = self.session.scalar(select(func.count()).select_from(Payment))
        res = self.client.post(
            f"/mini-app/custom-requests/{rid}/booking-bridge/reservations",
            params={"language_code": "en"},
            json={
                "telegram_user_id": self.TG,
                "seats_count": 2,
                "boarding_point_id": bp.id,
            },
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertIn("order", res.json())
        n_pay_after = self.session.scalar(select(func.count()).select_from(Payment))
        self.assertEqual(n_pay, n_pay_after)

    def test_preparation_rejects_stale_tour_after_departure_passes(self) -> None:
        """Execution-time validation must not use only bridge link-time snapshot."""
        rid = self._rfq_selected()
        tour = self._make_tour(code="EX-STALE", sales_mode=TourSalesMode.PER_SEAT, days_ahead=90)
        from datetime import time as time_type

        self.session.add(
            BoardingPoint(tour_id=tour.id, city="City", address="Addr", time=time_type(6, 0)),
        )
        self.session.flush()
        self.client.post(
            f"/admin/custom-requests/{rid}/booking-bridge",
            headers=self._headers_admin(),
            json={"tour_id": tour.id},
        )
        tour.departure_datetime = datetime.now(UTC) - timedelta(days=1)
        tour.return_datetime = datetime.now(UTC) - timedelta(hours=1)
        self.session.add(tour)
        self.session.flush()
        prep = self.client.get(
            f"/mini-app/custom-requests/{rid}/booking-bridge/preparation",
            params={"telegram_user_id": self.TG},
        )
        self.assertEqual(prep.status_code, 400, prep.text)
