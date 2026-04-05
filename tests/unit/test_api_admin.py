"""Integration tests for read-only admin API."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.models.handoff import Handoff
from tests.unit.base import FoundationDBTestCase


class AdminRouteTests(FoundationDBTestCase):
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

    def test_admin_disabled_without_token_config(self) -> None:
        get_settings().admin_api_token = None
        response = self.client.get("/admin/overview")
        self.assertEqual(response.status_code, 503)

    def test_admin_unauthorized_without_credentials(self) -> None:
        get_settings().admin_api_token = "test-admin-secret"
        response = self.client.get("/admin/overview")
        self.assertEqual(response.status_code, 401)

    def test_overview_and_lists_with_bearer(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-TOUR-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        self.session.commit()

        headers = {"Authorization": "Bearer test-admin-secret"}
        ov = self.client.get("/admin/overview", headers=headers)
        self.assertEqual(ov.status_code, 200)
        body = ov.json()
        self.assertEqual(body["app_env"], get_settings().app_env)
        self.assertGreaterEqual(body["tours_total_approx"], 1)
        self.assertGreaterEqual(body["orders_total_approx"], 1)

        tours = self.client.get("/admin/tours", headers=headers)
        self.assertEqual(tours.status_code, 200)
        tdata = tours.json()
        self.assertGreaterEqual(len(tdata["items"]), 1)
        self.assertEqual(tdata["items"][0]["code"], "ADM-TOUR-1")

        orders = self.client.get("/admin/orders", headers=headers)
        self.assertEqual(orders.status_code, 200)
        odata = orders.json()
        self.assertGreaterEqual(len(odata["items"]), 1)
        row = odata["items"][0]
        self.assertEqual(row["lifecycle_kind"], "expired_unpaid_hold")
        self.assertIn("Not an active reservation", row["lifecycle_summary"])

    def test_order_detail_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/orders/999999", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_order_detail_requires_auth(self) -> None:
        r = self.client.get("/admin/orders/1")
        self.assertEqual(r.status_code, 401)

    def test_order_detail_expired_unpaid_hold_projection(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-DETAIL-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        self.create_payment(order, status=PaymentStatus.UNPAID)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=order.id,
                reason="Question",
                priority="normal",
                status="open",
            )
        )
        self.session.commit()

        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["lifecycle_kind"], "expired_unpaid_hold")
        self.assertIn("Not an active reservation", body["lifecycle_summary"])
        self.assertEqual(body["persistence_snapshot"]["booking_status"], "reserved")
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "unpaid")
        self.assertEqual(body["persistence_snapshot"]["cancellation_status"], "cancelled_no_payment")
        self.assertEqual(body["tour"]["code"], "ADM-DETAIL-1")
        self.assertEqual(body["boarding_point"]["city"], point.city)
        self.assertEqual(len(body["payments"]), 1)
        self.assertEqual(len(body["handoffs"]), 1)
        self.assertEqual(body["handoffs"][0]["status"], "open")

    def test_tour_detail_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/tours/999999", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_tour_detail_requires_auth(self) -> None:
        r = self.client.get("/admin/tours/1")
        self.assertEqual(r.status_code, 401)

    def test_tour_detail_includes_translation_boarding_orders_count(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-TOUR-DETAIL",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 7, 1, 7, 0, tzinfo=UTC),
        )
        self.create_translation(tour, language_code="ro", title="Tură RO")
        bp1 = self.create_boarding_point(tour, city="CityA")
        self.create_boarding_point(tour, city="CityB")
        point_for_order = bp1
        self.create_order(user, tour, point_for_order)
        self.session.commit()

        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get(f"/admin/tours/{tour.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["code"], "ADM-TOUR-DETAIL")
        self.assertEqual(body["orders_count"], 1)
        self.assertEqual(len(body["translations"]), 1)
        self.assertEqual(body["translations"][0]["language_code"], "ro")
        self.assertEqual(body["translations"][0]["title"], "Tură RO")
        self.assertEqual(len(body["boarding_points"]), 2)
        cities = {x["city"] for x in body["boarding_points"]}
        self.assertEqual(cities, {"CityA", "CityB"})
