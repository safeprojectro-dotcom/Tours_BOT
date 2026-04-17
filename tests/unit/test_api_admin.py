"""Integration tests for read-only admin API."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourSalesMode, TourStatus
from app.models.handoff import Handoff
from app.services.handoff_entry import HandoffEntryService
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

    def test_admin_tour_list_includes_past_departure_tour(self) -> None:
        """Admin read paths are not filtered by customer catalog time windows."""
        past = self.create_tour(
            code="ADM-PAST-DEP-CAT",
            title_default="Legacy departed tour",
            departure_datetime=datetime(2018, 2, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2018, 2, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.create_boarding_point(past)
        self.session.commit()

        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/tours", headers=headers)
        self.assertEqual(r.status_code, 200)
        codes = {item["code"] for item in r.json()["items"]}
        self.assertIn("ADM-PAST-DEP-CAT", codes)

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
        self.assertEqual(body["payment_records_count"], 1)
        self.assertFalse(body["needs_manual_review"])
        self.assertFalse(body["has_multiple_payment_entries"])
        self.assertFalse(body["has_paid_entry"])
        self.assertFalse(body["has_awaiting_payment_entry"])
        self.assertIsNone(body["payment_correction_hint"])
        self.assertEqual(body["latest_payment_status"], "unpaid")
        self.assertEqual(body["latest_payment_provider"], "mockpay")
        self.assertIsNotNone(body["latest_payment_created_at"])
        self.assertEqual(len(body["handoffs"]), 1)
        self.assertEqual(body["handoffs"][0]["status"], "open")
        self.assertEqual(body["suggested_admin_action"], "handoff_follow_up")
        self.assertIn("review_open_handoff", body["allowed_admin_actions"])
        self.assertIn("handoff", body["payment_action_preview"].lower())

    def test_order_detail_payment_correction_multiple_payment_entries(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-PAY-MULTI",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
        )
        self.create_payment(order, status=PaymentStatus.UNPAID, external_payment_id="ext-a")
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT, external_payment_id="ext-b")
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["payment_records_count"], 2)
        self.assertTrue(body["has_multiple_payment_entries"])
        self.assertTrue(body["needs_manual_review"])
        self.assertIsNotNone(body["payment_correction_hint"])
        self.assertIn("Multiple payment entries", body["payment_correction_hint"])
        self.assertEqual(body["suggested_admin_action"], "manual_review")
        self.assertIn("review_payment_records", body["allowed_admin_actions"])

    def test_order_detail_payment_correction_order_paid_without_paid_row(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-PAY-NOPAIDROW",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 6, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
        )
        self.create_payment(order, status=PaymentStatus.UNPAID)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["needs_manual_review"])
        self.assertIn("paid but no payment row has status paid", body["payment_correction_hint"])
        self.assertEqual(body["suggested_admin_action"], "manual_review")

    def test_order_detail_payment_correction_paid_row_order_unpaid(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-PAY-MISMATCH",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 6, 3, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["needs_manual_review"])
        self.assertTrue(body["has_paid_entry"])
        self.assertIn("paid payment row exists while order payment_status is not paid", body["payment_correction_hint"])
        self.assertEqual(body["suggested_admin_action"], "manual_review")

    def test_order_detail_action_preview_confirmed_paid_clean(self) -> None:
        """No ambiguity, no open handoff — preview stays none / routine."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ACTION-CLEAN",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["lifecycle_kind"], "confirmed_paid")
        self.assertFalse(body["needs_manual_review"])
        self.assertEqual(body["suggested_admin_action"], "none")
        self.assertEqual(body["allowed_admin_actions"], [])
        self.assertIn("No payment follow-up", body["payment_action_preview"])
        self.assertTrue(body["can_consider_move"])
        self.assertEqual(body["move_blockers"], [])
        self.assertIn("future narrow move", body["move_readiness_hint"].lower())

    def test_order_detail_lifecycle_ready_for_departure_paid(self) -> None:
        """Step 27: ready_for_departure + paid + active maps to ready_for_departure_paid, not other."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-LC-RFD",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.READY_FOR_DEPARTURE,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["lifecycle_kind"], "ready_for_departure_paid")
        self.assertIn("ready for departure", body["lifecycle_summary"].lower())
        self.assertEqual(body["suggested_admin_action"], "none")
        self.assertIn("lifecycle_kind", body)
        self.assertIn("needs_manual_review", body)
        self.assertIn("payment_correction_hint", body)
        self.assertTrue(body["can_consider_move"])
        self.assertEqual(body["move_blockers"], [])
        self.assertIn("future narrow move", body["move_readiness_hint"].lower())

    def test_order_detail_move_readiness_blocked_open_handoff(self) -> None:
        """Paid confirmed future tour but open handoff — conservative move blocker."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-MV-HO",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 12, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=order.id,
                reason="Need help",
                priority="normal",
                status="open",
            )
        )
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["can_consider_move"])
        self.assertIn("open_handoff_open", body["move_blockers"])
        self.assertIn("blockers", body["move_readiness_hint"].lower())

    def test_order_detail_move_readiness_blocked_past_departure(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-MV-PAST",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2020, 3, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["can_consider_move"])
        self.assertIn("tour_departure_not_in_future", body["move_blockers"])

    def test_order_detail_action_preview_active_hold_await_payment(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ACTION-HOLD",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 7, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC),
        )
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["lifecycle_kind"], "active_temporary_hold")
        self.assertFalse(body["needs_manual_review"])
        self.assertEqual(body["suggested_admin_action"], "await_customer_payment")
        self.assertIn("monitor_reservation_deadline", body["allowed_admin_actions"])
        self.assertFalse(body["can_consider_move"])
        self.assertIn("lifecycle_not_move_candidate", body["move_blockers"])

    def test_post_admin_order_move_requires_auth(self) -> None:
        r = self.client.post("/admin/orders/1/move", json={"target_tour_id": 1, "target_boarding_point_id": 1})
        self.assertEqual(r.status_code, 401)

    def test_post_admin_order_move_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/orders/999999/move",
            headers=headers,
            json={"target_tour_id": 1, "target_boarding_point_id": 1},
        )
        self.assertEqual(r.status_code, 404)

    def test_post_admin_order_move_success_cross_tour_updates_seats_and_tour(self) -> None:
        """Phase 6 Step 29: narrow move when Step 28 readiness is clean — restore source, deduct target."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MV-SRC",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 10, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        point_a = self.create_boarding_point(tour_a)
        tour_b = self.create_tour(
            code="ADM-MV-TGT",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 11, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=30,
            currency="EUR",
        )
        point_b = self.create_boarding_point(tour_b)
        order = self.create_order(
            user,
            tour_a,
            point_a,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
            total_amount=Decimal("199.98"),
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour_b.id, "target_boarding_point_id": point_b.id},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["tour"]["code"], "ADM-MV-TGT")
        self.assertEqual(body["tour"]["id"], tour_b.id)
        self.assertEqual(body["boarding_point"]["id"], point_b.id)
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "paid")
        self.assertEqual(body["persistence_snapshot"]["booking_status"], "confirmed")
        self.assertEqual(Decimal(body["total_amount"]), Decimal("199.98"))
        self.assertTrue(body["can_consider_move"])

        self.session.refresh(tour_a)
        self.session.refresh(tour_b)
        self.assertEqual(tour_a.seats_available, 40)
        self.assertEqual(tour_b.seats_available, 28)

    def test_post_admin_order_move_rejects_not_ready_active_hold(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MV-NR",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        pa = self.create_boarding_point(tour_a)
        tour_b = self.create_tour(
            code="ADM-MV-NR-B",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
        )
        pb = self.create_boarding_point(tour_b)
        order = self.create_order(
            user,
            tour_a,
            pa,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC),
        )
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour_b.id, "target_boarding_point_id": pb.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_move_not_ready")

    def test_post_admin_order_move_rejects_boarding_not_on_target_tour(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MV-BP-A",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 10, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        pa = self.create_boarding_point(tour_a)
        tour_b = self.create_tour(
            code="ADM-MV-BP-B",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 11, 8, 0, tzinfo=UTC),
        )
        pb = self.create_boarding_point(tour_b)
        order = self.create_order(
            user,
            tour_a,
            pa,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour_a.id, "target_boarding_point_id": pb.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_move_boarding_not_on_target_tour")

    def test_post_admin_order_move_rejects_insufficient_seats_on_target(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MV-SEAT-A",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 10, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        pa = self.create_boarding_point(tour_a)
        tour_b = self.create_tour(
            code="ADM-MV-SEAT-B",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 11, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=1,
        )
        pb = self.create_boarding_point(tour_b)
        order = self.create_order(
            user,
            tour_a,
            pa,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour_b.id, "target_boarding_point_id": pb.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_move_insufficient_seats_on_target")

        self.session.refresh(tour_a)
        self.session.refresh(tour_b)
        self.assertEqual(tour_a.seats_available, 38)
        self.assertEqual(tour_b.seats_available, 1)

    def test_post_admin_order_move_rejects_target_tour_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MV-NT",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 12, 20, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        pa = self.create_boarding_point(tour_a)
        order = self.create_order(
            user,
            tour_a,
            pa,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": 999_999, "target_boarding_point_id": pa.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_move_target_tour_not_found")

    def test_post_admin_order_move_same_tour_different_boarding_no_seat_change(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-MV-SAME",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 7, 20, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=36,
        )
        p1 = self.create_boarding_point(tour, city="Alpha")
        p2 = self.create_boarding_point(tour, city="Beta")
        order = self.create_order(
            user,
            tour,
            p1,
            seats_count=4,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()
        seats_before = tour.seats_available

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour.id, "target_boarding_point_id": p2.id},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["boarding_point"]["city"], "Beta")
        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, seats_before)

    def test_post_admin_order_move_rejects_target_not_open_for_sale(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MV-CLS-A",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        pa = self.create_boarding_point(tour_a)
        tour_b = self.create_tour(
            code="ADM-MV-CLS-B",
            status=TourStatus.SALES_CLOSED,
            departure_datetime=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=30,
        )
        pb = self.create_boarding_point(tour_b)
        order = self.create_order(
            user,
            tour_a,
            pa,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour_b.id, "target_boarding_point_id": pb.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_move_target_tour_not_open_for_sale")

    def test_order_detail_move_placement_snapshot_stable_order(self) -> None:
        """Step 30: read-only placement snapshot matches current tour/boarding; no timeline."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-MVPL-STABLE",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour, city="StableCity")
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        mps = body["move_placement_snapshot"]
        self.assertEqual(mps["kind"], "current_placement_only")
        self.assertFalse(mps["timeline_available"])
        self.assertEqual(mps["tour_id"], tour.id)
        self.assertEqual(mps["boarding_point_id"], point.id)
        self.assertEqual(mps["tour_code"], "ADM-MVPL-STABLE")
        self.assertEqual(mps["boarding_city"], "StableCity")
        self.assertIn("not persisted", mps["note"].lower())
        self.assertIn("lifecycle_kind", body)
        self.assertIn("can_consider_move", body)
        self.assertIn("needs_manual_review", body)
        self.assertIn("suggested_admin_action", body)

    def test_order_detail_move_placement_snapshot_after_admin_move(self) -> None:
        """Step 30: after Step 29 move, snapshot reflects **current** target placement only."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour_a = self.create_tour(
            code="ADM-MVPL-SRC",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 15, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        pa = self.create_boarding_point(tour_a, city="SourceCity")
        tour_b = self.create_tour(
            code="ADM-MVPL-TGT",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 16, 9, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=30,
            currency="EUR",
        )
        pb = self.create_boarding_point(tour_b, city="TargetCity")
        order = self.create_order(
            user,
            tour_a,
            pa,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        mv = self.client.post(
            f"/admin/orders/{order.id}/move",
            headers=headers,
            json={"target_tour_id": tour_b.id, "target_boarding_point_id": pb.id},
        )
        self.assertEqual(mv.status_code, 200)

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        mps = body["move_placement_snapshot"]
        self.assertFalse(mps["timeline_available"])
        self.assertEqual(mps["tour_id"], tour_b.id)
        self.assertEqual(mps["boarding_point_id"], pb.id)
        self.assertEqual(mps["tour_code"], "ADM-MVPL-TGT")
        self.assertEqual(mps["boarding_city"], "TargetCity")
        self.assertIn("2026-08-16T09:00:00", mps["tour_departure_datetime"])

    def test_order_mark_cancelled_by_operator_requires_auth(self) -> None:
        r = self.client.post("/admin/orders/1/mark-cancelled-by-operator")
        self.assertEqual(r.status_code, 401)

    def test_order_mark_cancelled_by_operator_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/orders/999999/mark-cancelled-by-operator", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_order_mark_cancelled_by_operator_rejects_paid(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-CXL-PAID",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-cancelled-by-operator",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()
        self.assertEqual(err["detail"]["code"], "order_mark_cancelled_by_operator_not_allowed")
        self.assertEqual(err["detail"]["payment_status"], "paid")

    def test_order_mark_cancelled_by_operator_rejects_expired_hold(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-CXL-EXP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 2, 8, 0, tzinfo=UTC),
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
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-cancelled-by-operator",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json()["detail"]["code"],
            "order_mark_cancelled_by_operator_not_allowed",
        )

    def test_order_mark_cancelled_by_operator_rejects_hold_without_expiry(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-CXL-NOEXP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 3, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=None,
        )
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-cancelled-by-operator",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)

    def test_order_mark_cancelled_by_operator_success_restores_seats(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-CXL-OK",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 4, 8, 0, tzinfo=UTC),
            seats_total=20,
            seats_available=18,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 10, 3, 12, 0, 0, tzinfo=UTC),
        )
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-cancelled-by-operator",
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["persistence_snapshot"]["cancellation_status"], "cancelled_by_operator")
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "unpaid")
        self.assertIsNone(body["reservation_expires_at"])

        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, 20)

    def test_order_mark_cancelled_by_operator_idempotent(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-CXL-IDEM",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 5, 8, 0, tzinfo=UTC),
            seats_total=30,
            seats_available=28,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 10, 4, 12, 0, 0, tzinfo=UTC),
        )
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT)
        self.session.commit()

        r1 = self.client.post(
            f"/admin/orders/{order.id}/mark-cancelled-by-operator",
            headers=headers,
        )
        self.assertEqual(r1.status_code, 200)
        self.session.refresh(tour)
        seats_after_first = tour.seats_available

        r2 = self.client.post(
            f"/admin/orders/{order.id}/mark-cancelled-by-operator",
            headers=headers,
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(
            r2.json()["persistence_snapshot"]["cancellation_status"],
            "cancelled_by_operator",
        )
        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, seats_after_first)

    def test_order_mark_duplicate_requires_auth(self) -> None:
        r = self.client.post("/admin/orders/1/mark-duplicate")
        self.assertEqual(r.status_code, 401)

    def test_order_mark_duplicate_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/orders/999999/mark-duplicate", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_order_mark_duplicate_rejects_paid(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-DUP-PAID",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_mark_duplicate_not_allowed")
        self.assertEqual(r.json()["detail"]["payment_status"], "paid")

    def test_order_mark_duplicate_rejects_cancelled_by_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-DUP-CBO",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_BY_OPERATOR,
            reservation_expires_at=None,
        )
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_mark_duplicate_not_allowed")

    def test_order_mark_duplicate_rejects_hold_without_expiry(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-DUP-NOEXP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 3, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=None,
        )
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)

    def test_order_mark_duplicate_success_active_hold_restores_seats(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-DUP-HOLD",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 4, 8, 0, tzinfo=UTC),
            seats_total=20,
            seats_available=18,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 11, 3, 12, 0, 0, tzinfo=UTC),
        )
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["persistence_snapshot"]["cancellation_status"], "duplicate")
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "unpaid")
        self.assertIsNone(body["reservation_expires_at"])
        self.assertIn("lifecycle_kind", body)
        self.assertIn("needs_manual_review", body)
        self.assertIn("suggested_admin_action", body)

        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, 20)

    def test_order_mark_duplicate_success_expired_unpaid_hold_no_seat_change(self) -> None:
        """Expired hold: seats already returned by expiry semantics; only cancellation_status -> duplicate."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-DUP-EXP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 5, 8, 0, tzinfo=UTC),
            seats_total=24,
            seats_available=24,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        self.session.commit()
        seats_before = tour.seats_available

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["persistence_snapshot"]["cancellation_status"], "duplicate")
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "unpaid")

        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, seats_before)

    def test_order_mark_duplicate_idempotent(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-DUP-IDEM",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 6, 8, 0, tzinfo=UTC),
            seats_total=25,
            seats_available=23,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 11, 5, 12, 0, 0, tzinfo=UTC),
        )
        self.create_payment(order, status=PaymentStatus.AWAITING_PAYMENT)
        self.session.commit()

        r1 = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r1.status_code, 200)
        self.session.refresh(tour)
        seats_after_first = tour.seats_available

        r2 = self.client.post(
            f"/admin/orders/{order.id}/mark-duplicate",
            headers=headers,
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["persistence_snapshot"]["cancellation_status"], "duplicate")
        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, seats_after_first)

    def test_order_mark_no_show_requires_auth(self) -> None:
        r = self.client.post("/admin/orders/1/mark-no-show")
        self.assertEqual(r.status_code, 401)

    def test_order_mark_no_show_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/orders/999999/mark-no-show", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_order_mark_no_show_success_confirmed_paid_after_departure(self) -> None:
        """Policy: CONFIRMED + PAID + ACTIVE, tour.departure in the past; booking+cancellation -> no_show; payment stays paid."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-NS-OK",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2025, 6, 1, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()
        seats_before = tour.seats_available

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-no-show",
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["persistence_snapshot"]["booking_status"], "no_show")
        self.assertEqual(body["persistence_snapshot"]["cancellation_status"], "no_show")
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "paid")
        self.assertIn("lifecycle_kind", body)
        self.assertIn("needs_manual_review", body)
        self.assertIn("suggested_admin_action", body)

        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, seats_before)

    def test_order_mark_no_show_idempotent(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-NS-IDEM",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2025, 7, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r1 = self.client.post(
            f"/admin/orders/{order.id}/mark-no-show",
            headers=headers,
        )
        self.assertEqual(r1.status_code, 200)

        r2 = self.client.post(
            f"/admin/orders/{order.id}/mark-no-show",
            headers=headers,
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["persistence_snapshot"]["booking_status"], "no_show")
        self.assertEqual(r2.json()["persistence_snapshot"]["cancellation_status"], "no_show")

    def test_order_mark_no_show_rejects_future_departure(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-NS-FUT",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2030, 12, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-no-show",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "order_mark_no_show_not_allowed")
        self.assertEqual(err["reason"], "departure_not_in_past")

    def test_order_mark_no_show_rejects_temporary_hold(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-NS-HOLD",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2025, 8, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2025, 7, 31, 12, 0, 0, tzinfo=UTC),
        )
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-no-show",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "order_mark_no_show_not_allowed")

    def test_order_mark_ready_for_departure_requires_auth(self) -> None:
        r = self.client.post("/admin/orders/1/mark-ready-for-departure")
        self.assertEqual(r.status_code, 401)

    def test_order_mark_ready_for_departure_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/orders/999999/mark-ready-for-departure", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_order_mark_ready_for_departure_success_future_departure(self) -> None:
        """Policy: CONFIRMED + PAID + ACTIVE, tour.departure strictly in the future (UTC); booking -> ready_for_dearture only."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-RFD-OK",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2030, 12, 1, 8, 0, tzinfo=UTC),
            seats_total=40,
            seats_available=38,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()
        seats_before = tour.seats_available

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-ready-for-departure",
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["persistence_snapshot"]["booking_status"], "ready_for_departure")
        self.assertEqual(body["persistence_snapshot"]["payment_status"], "paid")
        self.assertEqual(body["persistence_snapshot"]["cancellation_status"], "active")
        self.assertIn("lifecycle_kind", body)
        self.assertIn("needs_manual_review", body)
        self.assertIn("suggested_admin_action", body)

        self.session.refresh(tour)
        self.assertEqual(tour.seats_available, seats_before)

    def test_order_mark_ready_for_departure_idempotent(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-RFD-IDEM",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2030, 11, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r1 = self.client.post(
            f"/admin/orders/{order.id}/mark-ready-for-departure",
            headers=headers,
        )
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(
            f"/admin/orders/{order.id}/mark-ready-for-departure",
            headers=headers,
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["persistence_snapshot"]["booking_status"], "ready_for_departure")

    def test_order_mark_ready_for_departure_rejects_past_departure(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-RFD-PAST",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2025, 6, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.create_payment(order, status=PaymentStatus.PAID)
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-ready-for-departure",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "order_mark_ready_for_departure_not_allowed")
        self.assertEqual(err["reason"], "departure_not_in_future")

    def test_order_mark_ready_for_departure_rejects_temporary_hold(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-ORD-RFD-HOLD",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2030, 8, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2030, 7, 31, 12, 0, 0, tzinfo=UTC),
        )
        self.session.commit()

        r = self.client.post(
            f"/admin/orders/{order.id}/mark-ready-for-departure",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json()["detail"]["code"],
            "order_mark_ready_for_departure_not_allowed",
        )

    def test_handoffs_list_requires_auth(self) -> None:
        r = self.client.get("/admin/handoffs")
        self.assertEqual(r.status_code, 401)

    def test_handoffs_detail_requires_auth(self) -> None:
        r = self.client.get("/admin/handoffs/1")
        self.assertEqual(r.status_code, 401)

    def test_handoffs_list_success_open_and_tour(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Need help",
            priority="high",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertGreaterEqual(body["total_returned"], 1)
        row = next(x for x in body["items"] if x["id"] == h.id)
        self.assertEqual(row["status"], "open")
        self.assertTrue(row["is_open"])
        self.assertTrue(row["needs_attention"])
        self.assertEqual(row["order_id"], order.id)
        self.assertEqual(row["tour_id"], tour.id)
        self.assertEqual(row["tour_code"], "ADM-HO-1")
        self.assertIn(row["age_bucket"], ("within_1h", "within_24h", "older"))

    def test_handoffs_list_no_order_stable_shape(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="General inquiry",
            priority="low",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.json()["items"] if x["id"] == h.id)
        self.assertIsNone(row["order_id"])
        self.assertIsNone(row["tour_id"])
        self.assertIsNone(row["tour_code"])
        self.assertTrue(row["is_open"])
        self.assertFalse(row["is_full_bus_sales_assistance"])
        self.assertIsNone(row["full_bus_sales_assistance_label"])
        self.assertIsNone(row["assistance_context_tour_code"])

    def test_handoffs_list_full_bus_sales_assistance_exposes_context(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        reason = HandoffEntryService.build_full_bus_sales_assistance_reason(
            tour_code="ADM-FB-HO",
            sales_mode="full_bus",
            channel="private",
        )
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason=reason,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.json()["items"] if x["id"] == h.id)
        self.assertTrue(row["is_full_bus_sales_assistance"])
        self.assertIsNotNone(row["full_bus_sales_assistance_label"])
        self.assertIn("ADM-FB-HO", row["full_bus_sales_assistance_label"] or "")
        self.assertEqual(row["assistance_context_tour_code"], "ADM-FB-HO")
        self.assertFalse(row["is_group_followup"])

    def test_handoffs_list_filter_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-CLOSED",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        closed = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Resolved",
            priority="normal",
            status="closed",
        )
        self.session.add(closed)
        self.session.commit()

        r_closed = self.client.get("/admin/handoffs", headers=headers, params={"status": "closed"})
        self.assertEqual(r_closed.status_code, 200)
        ids_closed = {x["id"] for x in r_closed.json()["items"]}
        self.assertIn(closed.id, ids_closed)
        row = next(x for x in r_closed.json()["items"] if x["id"] == closed.id)
        self.assertFalse(row["is_open"])
        self.assertFalse(row["needs_attention"])

    def test_handoff_detail_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-DET",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 8, 3, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Detail test",
            priority="normal",
            status="in_review",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get(f"/admin/handoffs/{h.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], h.id)
        self.assertEqual(body["status"], "in_review")
        self.assertTrue(body["needs_attention"])
        self.assertFalse(body["is_open"])
        self.assertFalse(body["is_assigned_group_followup"])
        self.assertIsNone(body["group_followup_work_label"])

    def test_handoff_detail_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/handoffs/999999", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_handoffs_list_group_followup_start_visibility(self) -> None:
        """Phase 7 / Step 9 — list exposes is_group_followup + source_label for group_followup_start."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        h_gf = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        operator = self.create_user(telegram_user_id=880_101)
        h_gf_assigned = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="in_review",
            assigned_operator_id=operator.id,
        )
        h_other = Handoff(
            user_id=user.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="open",
        )
        self.session.add(h_gf)
        self.session.add(h_gf_assigned)
        self.session.add(h_other)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        items = {x["id"]: x for x in r.json()["items"]}
        row_gf = items[h_gf.id]
        self.assertTrue(row_gf["is_group_followup"])
        self.assertIsNotNone(row_gf["source_label"])
        self.assertIn("grp_followup", row_gf["source_label"])
        self.assertFalse(row_gf["is_assigned_group_followup"])
        self.assertIsNotNone(row_gf["group_followup_work_label"])
        self.assertIn("Awaiting", row_gf["group_followup_work_label"])
        row_gfa = items[h_gf_assigned.id]
        self.assertTrue(row_gfa["is_assigned_group_followup"])
        self.assertIsNotNone(row_gfa["group_followup_work_label"])
        self.assertIn("Assigned", row_gfa["group_followup_work_label"])
        row_o = items[h_other.id]
        self.assertFalse(row_o["is_group_followup"])
        self.assertIsNone(row_o["source_label"])
        self.assertFalse(row_o["is_assigned_group_followup"])
        self.assertIsNone(row_o["group_followup_work_label"])

    def test_handoffs_list_private_contact_assigned_operator_no_group_followup_work_fields(self) -> None:
        """Phase 7 / Step 11 — non-group-followup reasons never get assigned-group-followup triage flags."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        op = self.create_user(telegram_user_id=880_202)
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="open",
            assigned_operator_id=op.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.json()["items"] if x["id"] == h.id)
        self.assertFalse(row["is_group_followup"])
        self.assertFalse(row["is_assigned_group_followup"])
        self.assertIsNone(row["group_followup_work_label"])

    def test_handoff_detail_group_followup_start_visibility(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get(f"/admin/handoffs/{h.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["is_group_followup"])
        self.assertIsNotNone(body["source_label"])
        self.assertEqual(body["reason"], HandoffEntryService.REASON_GROUP_FOLLOWUP_START)
        self.assertFalse(body["is_assigned_group_followup"])
        self.assertIsNotNone(body["group_followup_work_label"])
        self.assertIn("Awaiting", body["group_followup_work_label"])

    def test_handoff_list_detail_group_followup_queue_state_phase7_step15(self) -> None:
        """Phase 7 / Step 15 — derived queue_state; no false signals for non-group-followup."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        op = self.create_user(telegram_user_id=881_501)
        h_resolved = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="closed",
            assigned_operator_id=op.id,
        )
        h_open = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
            assigned_operator_id=None,
        )
        h_pc = Handoff(
            user_id=user.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="closed",
        )
        self.session.add_all([h_resolved, h_open, h_pc])
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        items = {x["id"]: x for x in r.json()["items"]}
        self.assertEqual(items[h_resolved.id]["group_followup_queue_state"], "resolved")
        self.assertIsNotNone(items[h_resolved.id]["group_followup_resolution_label"])
        self.assertEqual(items[h_open.id]["group_followup_queue_state"], "awaiting_assignment")
        self.assertIsNone(items[h_open.id]["group_followup_resolution_label"])
        self.assertIsNone(items[h_pc.id]["group_followup_queue_state"])

        r_d = self.client.get(f"/admin/handoffs/{h_resolved.id}", headers=headers)
        self.assertEqual(r_d.status_code, 200)
        self.assertEqual(r_d.json()["group_followup_queue_state"], "resolved")

    def test_handoffs_list_filter_group_followup_queue_resolved(self) -> None:
        """Phase 7 / Step 15 — optional list filter for resolved group_followup_start only."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        op = self.create_user(telegram_user_id=881_502)
        h_gf_closed = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="closed",
            assigned_operator_id=op.id,
        )
        h_gf_open = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        h_pc_closed = Handoff(
            user_id=user.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="closed",
        )
        self.session.add_all([h_gf_closed, h_gf_open, h_pc_closed])
        self.session.commit()

        r = self.client.get(
            "/admin/handoffs",
            headers=headers,
            params={"group_followup_queue": "resolved"},
        )
        self.assertEqual(r.status_code, 200)
        ids = {x["id"] for x in r.json()["items"]}
        self.assertIn(h_gf_closed.id, ids)
        self.assertNotIn(h_gf_open.id, ids)
        self.assertNotIn(h_pc_closed.id, ids)

    def test_resolve_group_followup_mutation_unchanged_after_step15_read_fields(self) -> None:
        """Regression: resolve endpoint semantics unchanged (read-only Step 15 additions)."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=881_503)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="in_review",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/resolve-group-followup", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "closed")
        self.assertEqual(body["group_followup_queue_state"], "resolved")

    def test_order_detail_handoff_summary_group_followup_visibility(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-GF-ORD",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        ho = next(x for x in r.json()["handoffs"] if x["id"] == h.id)
        self.assertTrue(ho["is_group_followup"])
        self.assertIsNotNone(ho["source_label"])
        self.assertFalse(ho["is_assigned_group_followup"])
        self.assertIsNotNone(ho["group_followup_work_label"])
        self.assertIn("Awaiting", ho["group_followup_work_label"])
        self.assertEqual(ho["group_followup_queue_state"], "awaiting_assignment")

    def test_order_detail_handoff_summary_assigned_group_followup_work_label(self) -> None:
        """Phase 7 / Step 11 — embedded order handoffs expose assignment triage for group_followup_start."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        operator = self.create_user(telegram_user_id=880_303)
        tour = self.create_tour(
            code="ADM-HO-GF-ORD-ASG",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get(f"/admin/orders/{order.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        ho = next(x for x in r.json()["handoffs"] if x["id"] == h.id)
        self.assertTrue(ho["is_assigned_group_followup"])
        self.assertIsNotNone(ho["group_followup_work_label"])
        self.assertIn("Assigned", ho["group_followup_work_label"])
        self.assertEqual(ho["group_followup_queue_state"], "assigned_open")

    def test_handoff_mark_in_review_preserves_group_followup_visibility(self) -> None:
        """Mutation response shape unchanged except new read-only fields; status transition as before."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-GF-MIR",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 11, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-review", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "in_review")
        self.assertTrue(body["is_group_followup"])
        self.assertIsNotNone(body["source_label"])
        self.assertFalse(body["is_assigned_group_followup"])
        self.assertIsNotNone(body["group_followup_work_label"])
        self.assertIn("Awaiting", body["group_followup_work_label"])

    def test_handoff_mark_in_review_requires_auth(self) -> None:
        r = self.client.post("/admin/handoffs/1/mark-in-review")
        self.assertEqual(r.status_code, 401)

    def test_handoff_mark_in_review_success_open_to_in_review(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-MIR",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Review me",
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-review", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], h.id)
        self.assertEqual(body["status"], "in_review")
        self.assertTrue(body["needs_attention"])
        self.assertFalse(body["is_open"])

    def test_handoff_mark_in_review_idempotent_in_review(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-MIR-IDEM",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Already reviewing",
            priority="normal",
            status="in_review",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-review", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "in_review")

    def test_handoff_mark_in_review_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/handoffs/999999/mark-in-review", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_handoff_mark_in_review_rejects_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-MIR-CL",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 3, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Done",
            priority="normal",
            status="closed",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-review", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()
        self.assertEqual(err["detail"]["code"], "handoff_mark_in_review_not_allowed")
        self.assertEqual(err["detail"]["current_status"], "closed")

    def test_handoff_close_requires_auth(self) -> None:
        r = self.client.post("/admin/handoffs/1/close")
        self.assertEqual(r.status_code, 401)

    def test_handoff_close_success_in_review_to_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-CLOSE-IR",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 4, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Close me",
            priority="normal",
            status="in_review",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/close", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], h.id)
        self.assertEqual(body["status"], "closed")
        self.assertFalse(body["is_open"])
        self.assertIn("needs_attention", body)
        self.assertIn("age_bucket", body)

    def test_handoff_close_idempotent_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-CLOSE-IDEM",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Already closed",
            priority="normal",
            status="closed",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/close", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "closed")

    def test_handoff_close_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/handoffs/999999/close", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_handoff_close_rejects_open(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-CLOSE-OP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 6, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        h = Handoff(
            user_id=user.id,
            order_id=order.id,
            reason="Still open",
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/close", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()
        self.assertEqual(err["detail"]["code"], "handoff_close_not_allowed")
        self.assertEqual(err["detail"]["current_status"], "open")

    def test_handoff_assign_requires_auth(self) -> None:
        r = self.client.post("/admin/handoffs/1/assign", json={"assigned_operator_id": 1})
        self.assertEqual(r.status_code, 401)

    def test_handoff_assign_success_open(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=900_001)
        tour = self.create_tour(
            code="ADM-HO-ASGN-OP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 7, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Assign me",
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], h.id)
        self.assertEqual(body["assigned_operator_id"], operator.id)
        self.assertTrue(body["needs_attention"])
        self.assertIn("age_bucket", body)

    def test_handoff_assign_success_in_review(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=900_002)
        tour = self.create_tour(
            code="ADM-HO-ASGN-IR",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 8, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="In review",
            priority="normal",
            status="in_review",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["assigned_operator_id"], operator.id)

    def test_handoff_assign_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/handoffs/999999/assign",
            headers=headers,
            json={"assigned_operator_id": 1},
        )
        self.assertEqual(r.status_code, 404)

    def test_handoff_assign_rejects_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=900_003)
        tour = self.create_tour(
            code="ADM-HO-ASGN-CL",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 9, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Closed",
            priority="normal",
            status="closed",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()
        self.assertEqual(err["detail"]["code"], "handoff_assign_not_allowed")
        self.assertEqual(err["detail"]["current_status"], "closed")

    def test_handoff_assign_idempotent_same_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=900_004)
        tour = self.create_tour(
            code="ADM-HO-ASGN-ID",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 10, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Same op",
            priority="normal",
            status="open",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["assigned_operator_id"], operator.id)

    def test_handoff_assign_rejects_reassign_different_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        op_a = self.create_user(telegram_user_id=900_005)
        op_b = self.create_user(telegram_user_id=900_006)
        tour = self.create_tour(
            code="ADM-HO-ASGN-RS",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 11, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Taken",
            priority="normal",
            status="open",
            assigned_operator_id=op_a.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign",
            headers=headers,
            json={"assigned_operator_id": op_b.id},
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()
        self.assertEqual(err["detail"]["code"], "handoff_reassign_not_allowed")
        self.assertEqual(err["detail"]["current_assigned_operator_id"], op_a.id)
        self.assertEqual(err["detail"]["requested_operator_id"], op_b.id)

    def test_handoff_assign_invalid_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-ASGN-BADOP",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 9, 12, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Bad op",
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign",
            headers=headers,
            json={"assigned_operator_id": 999_999},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "handoff_assign_operator_not_found")

    def test_handoff_assign_operator_requires_auth(self) -> None:
        r = self.client.post(
            "/admin/handoffs/1/assign-operator",
            json={"assigned_operator_id": 1},
        )
        self.assertEqual(r.status_code, 401)

    def test_handoff_assign_operator_success_group_followup_start(self) -> None:
        """Phase 7 / Step 10 — narrow path assigns only ``group_followup_start``."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=920_001)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign-operator",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["assigned_operator_id"], operator.id)
        self.assertTrue(body["is_group_followup"])
        self.assertTrue(body["is_assigned_group_followup"])
        self.assertIsNotNone(body["group_followup_work_label"])
        self.assertIn("Assigned", body["group_followup_work_label"])

    def test_handoff_assign_operator_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/handoffs/999999/assign-operator",
            headers=headers,
            json={"assigned_operator_id": 1},
        )
        self.assertEqual(r.status_code, 404)

    def test_handoff_assign_operator_invalid_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign-operator",
            headers=headers,
            json={"assigned_operator_id": 999_999_999},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "handoff_assign_operator_not_found")

    def test_handoff_assign_operator_rejects_non_group_followup_reason(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=920_002)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign-operator",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "handoff_assign_group_followup_reason_only")
        self.assertEqual(err["current_reason"], "private_contact")

    def test_handoff_assign_operator_idempotent_same_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=920_003)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign-operator",
            headers=headers,
            json={"assigned_operator_id": operator.id},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["assigned_operator_id"], operator.id)

    def test_handoff_assign_operator_rejects_reassign_different_operator(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        op_a = self.create_user(telegram_user_id=920_004)
        op_b = self.create_user(telegram_user_id=920_005)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
            assigned_operator_id=op_a.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(
            f"/admin/handoffs/{h.id}/assign-operator",
            headers=headers,
            json={"assigned_operator_id": op_b.id},
        )
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "handoff_reassign_not_allowed")

    def test_handoff_mark_in_work_requires_auth(self) -> None:
        r = self.client.post("/admin/handoffs/1/mark-in-work")
        self.assertEqual(r.status_code, 401)

    def test_handoff_mark_in_work_success_assigned_group_followup_open_to_in_review(self) -> None:
        """Phase 7 / Step 12 — narrow take-in-work: open → in_review when assigned + group_followup_start."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=930_001)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-work", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "in_review")
        self.assertEqual(body["assigned_operator_id"], operator.id)
        self.assertTrue(body["is_assigned_group_followup"])

    def test_handoff_mark_in_work_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/handoffs/999999/mark-in-work", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_handoff_mark_in_work_rejects_non_group_followup_reason(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=930_002)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="open",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-work", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "handoff_mark_in_work_reason_only")
        self.assertEqual(err["current_reason"], "private_contact")

    def test_handoff_mark_in_work_rejects_unassigned_group_followup(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-work", headers=headers)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["code"], "handoff_mark_in_work_assignment_required")

    def test_handoff_mark_in_work_idempotent_in_review(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=930_003)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="in_review",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-work", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "in_review")

    def test_handoff_mark_in_work_rejects_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=930_004)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="closed",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/mark-in-work", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "handoff_mark_in_work_not_allowed")
        self.assertEqual(err["current_status"], "closed")

    def test_handoff_resolve_group_followup_success_in_review_to_closed(self) -> None:
        """Phase 7 / Steps 13–14 — narrow resolve closes assigned group followup from in_review."""
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=940_001)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="in_review",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/resolve-group-followup", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "closed")
        self.assertIsNotNone(body.get("group_followup_resolution_label"))
        self.assertIn("resolved", body["group_followup_resolution_label"].lower())

    def test_handoff_resolve_group_followup_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/handoffs/999999/resolve-group-followup", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_handoff_resolve_group_followup_rejects_wrong_reason(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="in_review",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/resolve-group-followup", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "handoff_resolve_group_followup_reason_only")

    def test_handoff_resolve_group_followup_rejects_open(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=940_002)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="open",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/resolve-group-followup", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()["detail"]
        self.assertEqual(err["code"], "handoff_resolve_group_followup_not_allowed")
        self.assertEqual(err["current_status"], "open")

    def test_handoff_resolve_group_followup_idempotent_closed(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=940_003)
        h = Handoff(
            user_id=customer.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="closed",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/resolve-group-followup", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "closed")
        self.assertIsNotNone(body.get("group_followup_resolution_label"))

    def test_handoffs_list_closed_group_followup_shows_resolution_label(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            priority="normal",
            status="closed",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.json()["items"] if x["id"] == h.id)
        self.assertIsNotNone(row.get("group_followup_resolution_label"))
        self.assertIn("resolved", row["group_followup_resolution_label"].lower())

    def test_handoffs_list_private_contact_closed_no_resolution_label(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="private_contact",
            priority="normal",
            status="closed",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.get("/admin/handoffs", headers=headers)
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.json()["items"] if x["id"] == h.id)
        self.assertIsNone(row.get("group_followup_resolution_label"))

    def test_handoff_reopen_requires_auth(self) -> None:
        r = self.client.post("/admin/handoffs/1/reopen")
        self.assertEqual(r.status_code, 401)

    def test_handoff_reopen_success_closed_to_open_preserves_assignment(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        operator = self.create_user(telegram_user_id=910_001)
        tour = self.create_tour(
            code="ADM-HO-REOPEN-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Was closed",
            priority="normal",
            status="in_review",
            assigned_operator_id=operator.id,
        )
        self.session.add(h)
        self.session.commit()
        self.client.post(f"/admin/handoffs/{h.id}/close", headers=headers)
        self.session.refresh(h)
        self.assertEqual(h.status, "closed")
        self.assertEqual(h.assigned_operator_id, operator.id)

        r = self.client.post(f"/admin/handoffs/{h.id}/reopen", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "open")
        self.assertEqual(body["assigned_operator_id"], operator.id)
        self.assertTrue(body["needs_attention"])
        self.assertIn("age_bucket", body)

    def test_handoff_reopen_idempotent_open(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-REOPEN-ID",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 2, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="Already open",
            priority="normal",
            status="open",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/reopen", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "open")

    def test_handoff_reopen_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/handoffs/999999/reopen", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_handoff_reopen_rejects_in_review(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        customer = self.create_user()
        tour = self.create_tour(
            code="ADM-HO-REOPEN-IR",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 10, 3, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(customer, tour, point)
        h = Handoff(
            user_id=customer.id,
            order_id=order.id,
            reason="In review",
            priority="normal",
            status="in_review",
        )
        self.session.add(h)
        self.session.commit()

        r = self.client.post(f"/admin/handoffs/{h.id}/reopen", headers=headers)
        self.assertEqual(r.status_code, 400)
        err = r.json()
        self.assertEqual(err["detail"]["code"], "handoff_reopen_not_allowed")
        self.assertEqual(err["detail"]["current_status"], "in_review")

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

    def test_list_tours_filtered_by_status(self) -> None:
        self.create_tour(
            code="ADM-STATUS-OPEN",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        )
        self.create_tour(
            code="ADM-STATUS-DRAFT",
            status=TourStatus.DRAFT,
            departure_datetime=datetime(2026, 6, 2, 8, 0, tzinfo=UTC),
        )
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/tours", headers=headers, params={"status": "draft"})
        self.assertEqual(r.status_code, 200)
        codes = {x["code"] for x in r.json()["items"]}
        self.assertIn("ADM-STATUS-DRAFT", codes)
        self.assertNotIn("ADM-STATUS-OPEN", codes)

    def test_list_tours_guaranteed_only(self) -> None:
        self.create_tour(
            code="ADM-NOT-GUAR",
            status=TourStatus.OPEN_FOR_SALE,
            guaranteed_flag=False,
            departure_datetime=datetime(2026, 8, 1, 8, 0, tzinfo=UTC),
        )
        self.create_tour(
            code="ADM-GUAR",
            status=TourStatus.OPEN_FOR_SALE,
            guaranteed_flag=True,
            departure_datetime=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        )
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/tours", headers=headers, params={"guaranteed_only": "true"})
        self.assertEqual(r.status_code, 200)
        codes = {x["code"] for x in r.json()["items"]}
        self.assertIn("ADM-GUAR", codes)
        self.assertNotIn("ADM-NOT-GUAR", codes)

    def test_list_orders_filtered_by_lifecycle_kind(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-LC-TOUR",
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        exp = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        active = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 5, 11, 12, 0, tzinfo=UTC),
        )
        conf = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}
        r_exp = self.client.get(
            "/admin/orders",
            headers=headers,
            params={"lifecycle_kind": "expired_unpaid_hold"},
        )
        self.assertEqual(r_exp.status_code, 200)
        ids_exp = {x["id"] for x in r_exp.json()["items"]}
        self.assertEqual(ids_exp, {exp.id})

        r_act = self.client.get(
            "/admin/orders",
            headers=headers,
            params={"lifecycle_kind": "active_temporary_hold"},
        )
        self.assertEqual(r_act.status_code, 200)
        ids_act = {x["id"] for x in r_act.json()["items"]}
        self.assertEqual(ids_act, {active.id})

        r_conf = self.client.get(
            "/admin/orders",
            headers=headers,
            params={"lifecycle_kind": "confirmed_paid"},
        )
        self.assertEqual(r_conf.status_code, 200)
        ids_conf = {x["id"] for x in r_conf.json()["items"]}
        self.assertEqual(ids_conf, {conf.id})

    def test_list_orders_filtered_by_lifecycle_kind_ready_for_departure_paid(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="ADM-LC-RFD-FLT",
            departure_datetime=datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        rfd = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.READY_FOR_DEPARTURE,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get(
            "/admin/orders",
            headers=headers,
            params={"lifecycle_kind": "ready_for_departure_paid"},
        )
        self.assertEqual(r.status_code, 200)
        ids = {x["id"] for x in r.json()["items"]}
        self.assertIn(rfd.id, ids)
        self.assertEqual(
            next(x["lifecycle_kind"] for x in r.json()["items"] if x["id"] == rfd.id),
            "ready_for_departure_paid",
        )

    def test_list_orders_filtered_by_tour_id(self) -> None:
        user = self.create_user()
        t1 = self.create_tour(
            code="ADM-TID-1",
            departure_datetime=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        t2 = self.create_tour(
            code="ADM-TID-2",
            departure_datetime=datetime(2026, 4, 2, 8, 0, tzinfo=UTC),
        )
        p1 = self.create_boarding_point(t1)
        p2 = self.create_boarding_point(t2)
        o1 = self.create_order(user, t1, p1)
        o2 = self.create_order(user, t2, p2)
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.get("/admin/orders", headers=headers, params={"tour_id": t1.id})
        self.assertEqual(r.status_code, 200)
        ids = {x["id"] for x in r.json()["items"]}
        self.assertEqual(ids, {o1.id})
        self.assertNotIn(o2.id, ids)

    def test_filtered_admin_lists_require_auth(self) -> None:
        r1 = self.client.get("/admin/tours", params={"status": "draft"})
        self.assertEqual(r1.status_code, 401)
        r2 = self.client.get("/admin/orders", params={"lifecycle_kind": "other"})
        self.assertEqual(r2.status_code, 401)

    def _admin_tour_create_payload(self, *, code: str) -> dict:
        return {
            "code": code,
            "title_default": "Admin created tour",
            "short_description_default": "Short",
            "full_description_default": "Full body",
            "duration_days": 2,
            "departure_datetime": "2026-11-10T08:00:00+00:00",
            "return_datetime": "2026-11-12T20:00:00+00:00",
            "base_price": "149.00",
            "currency": "EUR",
            "seats_total": 33,
            "sales_deadline": "2026-11-08T23:59:59+00:00",
            "status": "draft",
            "guaranteed_flag": False,
        }

    def test_post_admin_tour_requires_auth(self) -> None:
        r = self.client.post("/admin/tours", json=self._admin_tour_create_payload(code="ADM-POST-NO-AUTH"))
        self.assertEqual(r.status_code, 401)

    def test_post_admin_tour_success_and_seats_available(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        code = "ADM-POST-OK-1"
        r = self.client.post(
            "/admin/tours",
            headers=headers,
            json=self._admin_tour_create_payload(code=code),
        )
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["code"], code)
        self.assertEqual(body["seats_total"], 33)
        self.assertEqual(body["seats_available"], 33)
        self.assertEqual(body["title_default"], "Admin created tour")
        self.assertEqual(body["short_description_default"], "Short")
        self.assertEqual(body["full_description_default"], "Full body")
        self.assertEqual(body["status"], "draft")
        self.assertEqual(body["sales_mode"], "per_seat")
        self.assertEqual(body["orders_count"], 0)
        self.assertEqual(len(body["translations"]), 0)
        self.assertEqual(len(body["boarding_points"]), 0)
        self.assertIsNone(body.get("cover_media_reference"))

    def test_post_admin_tour_can_set_sales_mode(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        payload = self._admin_tour_create_payload(code="ADM-POST-FULL-BUS")
        payload["sales_mode"] = "full_bus"

        r = self.client.post("/admin/tours", headers=headers, json=payload)

        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["sales_mode"], "full_bus")

    def test_post_admin_tour_rejects_invalid_sales_mode(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        payload = self._admin_tour_create_payload(code="ADM-POST-BAD-SMODE")
        payload["sales_mode"] = "invalid_mode"

        r = self.client.post("/admin/tours", headers=headers, json=payload)

        self.assertEqual(r.status_code, 422)

    def test_post_admin_tour_duplicate_code(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        code = "ADM-POST-DUP"
        payload = self._admin_tour_create_payload(code=code)
        r1 = self.client.post("/admin/tours", headers=headers, json=payload)
        self.assertEqual(r1.status_code, 201)
        r2 = self.client.post("/admin/tours", headers=headers, json=payload)
        self.assertEqual(r2.status_code, 409)
        self.assertIn("already exists", r2.json()["detail"].lower())

    def test_post_admin_tour_validation_return_not_after_departure(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        p = self._admin_tour_create_payload(code="ADM-POST-BAD-DATES")
        p["return_datetime"] = p["departure_datetime"]
        r = self.client.post("/admin/tours", headers=headers, json=p)
        self.assertEqual(r.status_code, 400)
        self.assertIn("departure", r.json()["detail"].lower())

    def test_post_admin_tour_validation_sales_deadline_not_before_departure(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        p = self._admin_tour_create_payload(code="ADM-POST-BAD-SALES")
        p["sales_deadline"] = "2026-11-10T10:00:00+00:00"
        r = self.client.post("/admin/tours", headers=headers, json=p)
        self.assertEqual(r.status_code, 400)
        self.assertIn("sales_deadline", r.json()["detail"].lower())

    def test_put_admin_tour_cover_requires_auth(self) -> None:
        r = self.client.put(
            "/admin/tours/1/cover",
            json={"cover_media_reference": "https://cdn.example/cover.jpg"},
        )
        self.assertEqual(r.status_code, 401)

    def test_put_admin_tour_cover_success_and_get_detail(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        cr = self.client.post(
            "/admin/tours",
            headers=headers,
            json=self._admin_tour_create_payload(code="ADM-COVER-OK"),
        )
        self.assertEqual(cr.status_code, 201)
        tour_id = cr.json()["id"]
        ref1 = "https://storage.example/bucket/tours/1/cover.webp"
        r1 = self.client.put(
            f"/admin/tours/{tour_id}/cover",
            headers=headers,
            json={"cover_media_reference": ref1},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["cover_media_reference"], ref1)

        ref2 = "s3://my-bucket/keys/tour-cover-2.png"
        r2 = self.client.put(
            f"/admin/tours/{tour_id}/cover",
            headers=headers,
            json={"cover_media_reference": f"  {ref2}  "},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["cover_media_reference"], ref2)

        g = self.client.get(f"/admin/tours/{tour_id}", headers=headers)
        self.assertEqual(g.status_code, 200)
        self.assertEqual(g.json()["cover_media_reference"], ref2)

    def test_put_admin_tour_cover_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.put(
            "/admin/tours/999999/cover",
            headers=headers,
            json={"cover_media_reference": "https://example.com/x.jpg"},
        )
        self.assertEqual(r.status_code, 404)

    def test_put_admin_tour_cover_rejects_blank(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-COVER-BLANK")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/cover",
            headers=headers,
            json={"cover_media_reference": "   "},
        )
        self.assertEqual(r.status_code, 422)

    def test_patch_admin_tour_core_requires_auth(self) -> None:
        r = self.client.patch("/admin/tours/1", json={"title_default": "X"})
        self.assertEqual(r.status_code, 401)

    def test_patch_admin_tour_core_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-PATCH-1", title_default="Old title")
        self.session.commit()
        r = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={"title_default": "New title", "guaranteed_flag": True},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["title_default"], "New title")
        self.assertTrue(body["guaranteed_flag"])
        self.assertEqual(body["sales_mode"], "per_seat")

    def test_patch_admin_tour_core_can_update_sales_mode(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-PATCH-SMODE", title_default="Mode tour")
        self.session.commit()

        r = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={"sales_mode": "full_bus"},
        )

        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["sales_mode"], "full_bus")
        self.assertEqual(body["title_default"], "Mode tour")
        self.assertEqual(body["seats_total"], tour.seats_total)
        self.assertEqual(body["seats_available"], tour.seats_available)

        detail = self.client.get(f"/admin/tours/{tour.id}", headers=headers)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["sales_mode"], "full_bus")

    def test_admin_tour_reads_expose_sales_mode(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        default_tour = self.create_tour(code="ADM-READ-SMODE-DEFAULT")
        full_bus_tour = self.create_tour(
            code="ADM-READ-SMODE-FULL",
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.commit()

        list_response = self.client.get("/admin/tours", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        items_by_code = {item["code"]: item for item in list_response.json()["items"]}
        self.assertEqual(items_by_code["ADM-READ-SMODE-DEFAULT"]["sales_mode"], "per_seat")
        self.assertEqual(items_by_code["ADM-READ-SMODE-FULL"]["sales_mode"], "full_bus")

        detail_response = self.client.get(f"/admin/tours/{full_bus_tour.id}", headers=headers)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["sales_mode"], "full_bus")

    def test_patch_admin_tour_core_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.patch(
            "/admin/tours/999999",
            headers=headers,
            json={"title_default": "X"},
        )
        self.assertEqual(r.status_code, 404)

    def test_patch_admin_tour_core_no_fields_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-PATCH-EMPTY")
        self.session.commit()
        r = self.client.patch(f"/admin/tours/{tour.id}", headers=headers, json={})
        self.assertEqual(r.status_code, 400)

    def test_patch_admin_tour_core_validation_dates(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(
            code="ADM-PATCH-DATES",
            departure_datetime=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 5, 3, 18, 0, tzinfo=UTC),
        )
        self.session.commit()
        r = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={
                "departure_datetime": "2026-05-10T08:00:00+00:00",
                "return_datetime": "2026-05-10T07:00:00+00:00",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_patch_admin_tour_core_seats_total_conservative(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(
            code="ADM-PATCH-SEATS",
            seats_total=40,
            seats_available=12,
        )
        self.session.commit()
        r_bad = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={"seats_total": 27},
        )
        self.assertEqual(r_bad.status_code, 400)
        self.assertIn("allocated", r_bad.json()["detail"].lower())

        r_ok = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={"seats_total": 50},
        )
        self.assertEqual(r_ok.status_code, 200)
        b = r_ok.json()
        self.assertEqual(b["seats_total"], 50)
        self.assertEqual(b["seats_available"], 22)

    def test_patch_admin_tour_core_rejects_code_and_cover_fields(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-PATCH-FORBID")
        self.session.commit()
        r1 = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={"code": "OTHER"},
        )
        self.assertEqual(r1.status_code, 422)
        r2 = self.client.patch(
            f"/admin/tours/{tour.id}",
            headers=headers,
            json={"cover_media_reference": "https://x/y.jpg"},
        )
        self.assertEqual(r2.status_code, 422)

    def test_post_admin_tour_archive_requires_auth(self) -> None:
        r = self.client.post("/admin/tours/1/archive")
        self.assertEqual(r.status_code, 401)

    def test_post_admin_tour_archive_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-ARCH-1", status=TourStatus.OPEN_FOR_SALE)
        self.session.commit()
        r = self.client.post(f"/admin/tours/{tour.id}/archive", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "sales_closed")

    def test_post_admin_tour_archive_idempotent_when_already_archived(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-ARCH-IDEM", status=TourStatus.SALES_CLOSED)
        self.session.commit()
        r1 = self.client.post(f"/admin/tours/{tour.id}/archive", headers=headers)
        r2 = self.client.post(f"/admin/tours/{tour.id}/archive", headers=headers)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.json()["status"], "sales_closed")
        self.assertEqual(r2.json()["status"], "sales_closed")

    def test_post_admin_tour_archive_rejects_in_progress(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-ARCH-BAD", status=TourStatus.IN_PROGRESS)
        self.session.commit()
        r = self.client.post(f"/admin/tours/{tour.id}/archive", headers=headers)
        self.assertEqual(r.status_code, 400)
        self.assertIn("status", r.json()["detail"].lower())

    def test_post_admin_tour_archive_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/tours/999999/archive", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_post_admin_tour_unarchive_requires_auth(self) -> None:
        r = self.client.post("/admin/tours/1/unarchive")
        self.assertEqual(r.status_code, 401)

    def test_post_admin_tour_unarchive_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-UNARCH-1", status=TourStatus.SALES_CLOSED)
        self.session.commit()
        r = self.client.post(f"/admin/tours/{tour.id}/unarchive", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "open_for_sale")

    def test_post_admin_tour_unarchive_idempotent_when_open_for_sale(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-UNARCH-IDEM", status=TourStatus.OPEN_FOR_SALE)
        self.session.commit()
        r = self.client.post(f"/admin/tours/{tour.id}/unarchive", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "open_for_sale")

    def test_post_admin_tour_unarchive_rejects_when_not_archived(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-UNARCH-DRAFT", status=TourStatus.DRAFT)
        self.session.commit()
        r = self.client.post(f"/admin/tours/{tour.id}/unarchive", headers=headers)
        self.assertEqual(r.status_code, 400)
        self.assertIn("archived", r.json()["detail"].lower())

    def test_post_admin_tour_unarchive_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post("/admin/tours/999999/unarchive", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_post_admin_boarding_point_requires_auth(self) -> None:
        r = self.client.post(
            "/admin/tours/1/boarding-points",
            json={"city": "X", "address": "Y", "time": "06:00:00"},
        )
        self.assertEqual(r.status_code, 401)

    def test_post_admin_boarding_point_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-OK")
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{tour.id}/boarding-points",
            headers=headers,
            json={
                "city": " Arad ",
                "address": " Central Station ",
                "time": "07:30:00",
                "notes": "  Gate 2  ",
            },
        )
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(len(body["boarding_points"]), 1)
        bp = body["boarding_points"][0]
        self.assertEqual(bp["city"], "Arad")
        self.assertEqual(bp["address"], "Central Station")
        self.assertEqual(bp["time"], "07:30:00")
        self.assertEqual(bp["notes"], "Gate 2")

    def test_post_admin_boarding_point_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/tours/999999/boarding-points",
            headers=headers,
            json={"city": "X", "address": "Y", "time": "06:00:00"},
        )
        self.assertEqual(r.status_code, 404)

    def test_post_admin_boarding_point_blank_city_422(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-BLANK-CITY")
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{tour.id}/boarding-points",
            headers=headers,
            json={"city": "   ", "address": "Somewhere", "time": "06:00:00"},
        )
        self.assertEqual(r.status_code, 422)

    def test_post_admin_boarding_point_blank_address_422(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-BLANK-ADDR")
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{tour.id}/boarding-points",
            headers=headers,
            json={"city": "Timisoara", "address": "  ", "time": "06:00:00"},
        )
        self.assertEqual(r.status_code, 422)

    def test_patch_admin_boarding_point_requires_auth(self) -> None:
        r = self.client.patch("/admin/boarding-points/1", json={"city": "X"})
        self.assertEqual(r.status_code, 401)

    def test_patch_admin_boarding_point_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-PATCH-OK")
        bp = self.create_boarding_point(tour, city="OldCity", address="OldAddr", notes="keep")
        self.session.commit()
        r = self.client.patch(
            f"/admin/boarding-points/{bp.id}",
            headers=headers,
            json={"city": " NewCity ", "time": "08:15:00", "notes": None},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], tour.id)
        by_id = {p["id"]: p for p in body["boarding_points"]}
        self.assertEqual(by_id[bp.id]["city"], "NewCity")
        self.assertEqual(by_id[bp.id]["address"], "OldAddr")
        self.assertEqual(by_id[bp.id]["time"], "08:15:00")
        self.assertIsNone(by_id[bp.id]["notes"])

    def test_patch_admin_boarding_point_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.patch(
            "/admin/boarding-points/999999",
            headers=headers,
            json={"city": "X"},
        )
        self.assertEqual(r.status_code, 404)

    def test_patch_admin_boarding_point_blank_city_422(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-PATCH-BLANK")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.patch(
            f"/admin/boarding-points/{bp.id}",
            headers=headers,
            json={"city": "   ", "address": "Y"},
        )
        self.assertEqual(r.status_code, 422)

    def test_patch_admin_boarding_point_no_fields_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-PATCH-EMPTY")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.patch(
            f"/admin/boarding-points/{bp.id}",
            headers=headers,
            json={},
        )
        self.assertEqual(r.status_code, 400)

    def test_patch_admin_boarding_point_rejects_tour_id_in_body(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour_a = self.create_tour(code="ADM-BP-PATCH-A")
        tour_b = self.create_tour(code="ADM-BP-PATCH-B")
        bp = self.create_boarding_point(tour_a)
        self.session.commit()
        r = self.client.patch(
            f"/admin/boarding-points/{bp.id}",
            headers=headers,
            json={"city": "X", "tour_id": tour_b.id},
        )
        self.assertEqual(r.status_code, 422)

    def test_put_admin_boarding_point_translation_requires_auth(self) -> None:
        r = self.client.put(
            "/admin/boarding-points/1/translations/ro",
            json={"city": "C", "address": "A"},
        )
        self.assertEqual(r.status_code, 401)

    def test_put_admin_boarding_point_translation_create_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-CREATE")
        bp = self.create_boarding_point(tour, city="Base", address="BaseAddr")
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={
                "city": " Oradea ",
                "address": " Autogara ",
                "notes": " Peron 3 ",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], tour.id)
        by_id = {p["id"]: p for p in body["boarding_points"]}
        trs = {t["language_code"]: t for t in by_id[bp.id]["translations"]}
        self.assertEqual(trs["ro"]["city"], "Oradea")
        self.assertEqual(trs["ro"]["address"], "Autogara")
        self.assertEqual(trs["ro"]["notes"], "Peron 3")

    def test_put_admin_boarding_point_translation_update_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-UPD")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"city": "A", "address": "B", "notes": "Old"},
        )
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"notes": "New note"},
        )
        self.assertEqual(r.status_code, 200)
        by_id = {p["id"]: p for p in r.json()["boarding_points"]}
        trs = {t["language_code"]: t for t in by_id[bp.id]["translations"]}
        self.assertEqual(trs["ro"]["city"], "A")
        self.assertEqual(trs["ro"]["address"], "B")
        self.assertEqual(trs["ro"]["notes"], "New note")

    def test_put_admin_boarding_point_translation_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.put(
            "/admin/boarding-points/999999/translations/ro",
            headers=headers,
            json={"city": "C", "address": "A"},
        )
        self.assertEqual(r.status_code, 404)

    def test_put_admin_boarding_point_translation_unsupported_language(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-BAD-LANG")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/xx",
            headers=headers,
            json={"city": "C", "address": "A"},
        )
        self.assertEqual(r.status_code, 400)

    def test_put_admin_boarding_point_translation_empty_body_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-EMPTY")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={},
        )
        self.assertEqual(r.status_code, 400)

    def test_put_admin_boarding_point_translation_create_without_city_address_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-PARTIAL")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"notes": "Only notes"},
        )
        self.assertEqual(r.status_code, 400)

    def test_put_admin_boarding_point_translation_blank_city_422(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-BLANK-CITY")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"city": "   ", "address": "Somewhere"},
        )
        self.assertEqual(r.status_code, 422)

    def test_put_admin_boarding_point_translation_path_language_normalized(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-NORM")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/DE",
            headers=headers,
            json={"city": "Berlin", "address": "Hbf"},
        )
        self.assertEqual(r.status_code, 200)
        by_id = {p["id"]: p for p in r.json()["boarding_points"]}
        codes = {t["language_code"] for t in by_id[bp.id]["translations"]}
        self.assertEqual(codes, {"de"})

    def test_put_admin_boarding_point_translation_update_cannot_clear_city_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-NOCLEAR")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"city": "A", "address": "B"},
        )
        self.session.commit()
        r = self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"city": None, "address": "Still"},
        )
        self.assertEqual(r.status_code, 400)

    def test_delete_admin_boarding_point_translation_requires_auth(self) -> None:
        r = self.client.delete("/admin/boarding-points/1/translations/ro")
        self.assertEqual(r.status_code, 401)

    def test_delete_admin_boarding_point_translation_success_removes_only_one(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-DEL-OK")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"city": "Ro", "address": "A1"},
        )
        self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/de",
            headers=headers,
            json={"city": "De", "address": "A2"},
        )
        self.session.commit()
        r = self.client.delete(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
        )
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.content, b"")

        g = self.client.get(f"/admin/tours/{tour.id}", headers=headers)
        self.assertEqual(g.status_code, 200)
        by_id = {p["id"]: p for p in g.json()["boarding_points"]}
        codes = {t["language_code"] for t in by_id[bp.id]["translations"]}
        self.assertEqual(codes, {"de"})

    def test_delete_admin_boarding_point_translation_not_found_boarding_point(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.delete("/admin/boarding-points/999999/translations/ro", headers=headers)
        self.assertEqual(r.status_code, 404)
        self.assertIn("boarding", r.json()["detail"].lower())

    def test_delete_admin_boarding_point_translation_not_found_translation(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-DEL-NO-ROW")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        r = self.client.delete(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
        )
        self.assertEqual(r.status_code, 404)
        self.assertIn("translation", r.json()["detail"].lower())

    def test_delete_admin_boarding_point_translation_unsupported_language_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BPTR-DEL-BAD-LANG")
        bp = self.create_boarding_point(tour)
        self.session.commit()
        self.client.put(
            f"/admin/boarding-points/{bp.id}/translations/ro",
            headers=headers,
            json={"city": "C", "address": "A"},
        )
        self.session.commit()
        r = self.client.delete(
            f"/admin/boarding-points/{bp.id}/translations/xx",
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("language", r.json()["detail"].lower())

    def test_delete_admin_boarding_point_requires_auth(self) -> None:
        r = self.client.delete("/admin/boarding-points/1")
        self.assertEqual(r.status_code, 401)

    def test_delete_admin_boarding_point_success_removes_only_one(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-BP-DEL-OK")
        bp_keep = self.create_boarding_point(tour, city="KeepCity")
        bp_go = self.create_boarding_point(tour, city="GoCity")
        self.session.commit()
        r = self.client.delete(f"/admin/boarding-points/{bp_go.id}", headers=headers)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.content, b"")

        g = self.client.get(f"/admin/tours/{tour.id}", headers=headers)
        self.assertEqual(g.status_code, 200)
        ids = {p["id"] for p in g.json()["boarding_points"]}
        self.assertEqual(ids, {bp_keep.id})
        self.assertNotIn(bp_go.id, ids)

    def test_delete_admin_boarding_point_not_found(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.delete("/admin/boarding-points/999999", headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_delete_admin_boarding_point_conflict_when_order_references(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        user = self.create_user()
        tour = self.create_tour(code="ADM-BP-DEL-BLOCK")
        bp = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            bp,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        self.session.commit()
        r = self.client.delete(f"/admin/boarding-points/{bp.id}", headers=headers)
        self.assertEqual(r.status_code, 409)
        self.assertIn("reference", r.json()["detail"].lower())

    def test_put_admin_tour_translation_requires_auth(self) -> None:
        r = self.client.put(
            "/admin/tours/1/translations/ro",
            json={"title": "T"},
        )
        self.assertEqual(r.status_code, 401)

    def test_put_admin_tour_translation_create_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-CREATE")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/ro",
            headers=headers,
            json={
                "title": " Excursie RO ",
                "short_description": "Scurt",
                "full_description": "Lung",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["id"], tour.id)
        trs = {t["language_code"]: t["title"] for t in body["translations"]}
        self.assertEqual(trs.get("ro"), "Excursie RO")

    def test_put_admin_tour_translation_update_success(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-UPD")
        self.create_translation(tour, language_code="ro", title="Old")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/ro",
            headers=headers,
            json={"title": "New RO Title"},
        )
        self.assertEqual(r.status_code, 200)
        trs = {t["language_code"]: t["title"] for t in r.json()["translations"]}
        self.assertEqual(trs.get("ro"), "New RO Title")

    def test_put_admin_tour_translation_path_language_normalized(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-NORM")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/DE",
            headers=headers,
            json={"title": "DE Titel"},
        )
        self.assertEqual(r.status_code, 200)
        codes = {t["language_code"] for t in r.json()["translations"]}
        self.assertIn("de", codes)

    def test_put_admin_tour_translation_not_found_tour(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.put(
            "/admin/tours/999999/translations/ro",
            headers=headers,
            json={"title": "X"},
        )
        self.assertEqual(r.status_code, 404)

    def test_put_admin_tour_translation_unsupported_language(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-BAD-LANG")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/xx",
            headers=headers,
            json={"title": "Nope"},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("language", r.json()["detail"].lower())

    def test_put_admin_tour_translation_empty_body_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-EMPTY")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/ro",
            headers=headers,
            json={},
        )
        self.assertEqual(r.status_code, 400)

    def test_put_admin_tour_translation_create_without_title_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-NO-TITLE")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/ro",
            headers=headers,
            json={"short_description": "Only short"},
        )
        self.assertEqual(r.status_code, 400)

    def test_put_admin_tour_translation_blank_title_422(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-BLANK-TITLE")
        self.session.commit()
        r = self.client.put(
            f"/admin/tours/{tour.id}/translations/ro",
            headers=headers,
            json={"title": "   "},
        )
        self.assertEqual(r.status_code, 422)

    def test_delete_admin_tour_translation_requires_auth(self) -> None:
        r = self.client.delete("/admin/tours/1/translations/ro")
        self.assertEqual(r.status_code, 401)

    def test_delete_admin_tour_translation_success_removes_only_one(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-DEL-OK")
        self.create_translation(tour, language_code="ro", title="RO")
        self.create_translation(tour, language_code="de", title="DE")
        self.session.commit()
        r = self.client.delete(f"/admin/tours/{tour.id}/translations/ro", headers=headers)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.content, b"")

        g = self.client.get(f"/admin/tours/{tour.id}", headers=headers)
        self.assertEqual(g.status_code, 200)
        codes = {t["language_code"] for t in g.json()["translations"]}
        self.assertEqual(codes, {"de"})

    def test_delete_admin_tour_translation_not_found_tour(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.delete("/admin/tours/999999/translations/ro", headers=headers)
        self.assertEqual(r.status_code, 404)
        self.assertIn("tour", r.json()["detail"].lower())

    def test_delete_admin_tour_translation_not_found_translation(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-DEL-NO-ROW")
        self.session.commit()
        r = self.client.delete(f"/admin/tours/{tour.id}/translations/ro", headers=headers)
        self.assertEqual(r.status_code, 404)
        self.assertIn("translation", r.json()["detail"].lower())

    def test_delete_admin_tour_translation_unsupported_language_400(self) -> None:
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="ADM-TR-DEL-BAD-LANG")
        self.create_translation(tour, language_code="ro", title="X")
        self.session.commit()
        r = self.client.delete(f"/admin/tours/{tour.id}/translations/xx", headers=headers)
        self.assertEqual(r.status_code, 400)
        self.assertIn("language", r.json()["detail"].lower())
