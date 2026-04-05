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
        self.assertEqual(body["orders_count"], 0)
        self.assertEqual(len(body["translations"]), 0)
        self.assertEqual(len(body["boarding_points"]), 0)
        self.assertIsNone(body.get("cover_media_reference"))

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
