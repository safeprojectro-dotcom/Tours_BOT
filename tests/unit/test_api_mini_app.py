from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourStatus
from tests.unit.base import FoundationDBTestCase


class MiniAppCatalogRouteTests(FoundationDBTestCase):
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

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_catalog_route_returns_filtered_cards(self) -> None:
        matching = self.create_tour(
            code="BELGRADE-API",
            title_default="Belgrade City Break",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            base_price="140.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        other = self.create_tour(
            code="BUDAPEST-API",
            title_default="Budapest Weekend",
            departure_datetime=datetime(2026, 4, 5, 9, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 21, 0, tzinfo=UTC),
            base_price="110.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        collecting_group = self.create_tour(
            code="BELGRADE-GROUP-API",
            title_default="Belgrade Group Build",
            departure_datetime=datetime(2026, 4, 5, 10, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 22, 0, tzinfo=UTC),
            base_price="115.00",
            status=TourStatus.COLLECTING_GROUP,
        )
        for tour in (matching, other, collecting_group):
            self.create_translation(tour, language_code="ro", title=tour.title_default)
            self.create_boarding_point(tour)
        self.session.commit()

        response = self.client.get(
            "/mini-app/catalog",
            params={
                "language_code": "ro",
                "destination_query": "Belgrade",
                "departure_date_from": "2026-04-05",
                "departure_date_to": "2026-04-05",
                "max_price": "150.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["code"] for item in payload["items"]], ["BELGRADE-API"])
        self.assertEqual(payload["status_scope"], ["open_for_sale"])
        self.assertEqual(payload["applied_filters"]["destination_query"], "Belgrade")

    def test_catalog_route_rejects_invalid_date_range(self) -> None:
        response = self.client.get(
            "/mini-app/catalog",
            params={
                "departure_date_from": "2026-04-07",
                "departure_date_to": "2026-04-05",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "departure date range is invalid")

    def test_tour_detail_route_returns_localized_read_only_detail(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-DETAIL-API",
            title_default="Belgrade Default",
            short_description_default="Default short",
            full_description_default="Default full",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=6,
        )
        self.create_translation(
            tour,
            language_code="ro",
            title="Belgrad API",
            short_description="Scurt API",
            full_description="Detalii API",
            program_text="Program API",
        )
        self.create_boarding_point(tour, city="Arad", address="Central Station")
        self.session.commit()

        response = self.client.get(
            f"/mini-app/tours/{tour.code}",
            params={"language_code": "ro"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tour"]["code"], tour.code)
        self.assertEqual(payload["localized_content"]["title"], "Belgrad API")
        self.assertEqual(payload["localized_content"]["full_description"], "Detalii API")
        self.assertEqual(payload["boarding_points"][0]["city"], "Arad")
        self.assertTrue(payload["is_available"])

    def test_tour_detail_route_returns_not_found_for_unknown_or_non_open_tour(self) -> None:
        collecting_group = self.create_tour(
            code="BELGRADE-GROUP-DETAIL-API",
            title_default="Belgrade Group",
            status=TourStatus.COLLECTING_GROUP,
        )
        self.create_translation(collecting_group, language_code="ro", title="Belgrad Grup")
        self.create_boarding_point(collecting_group)
        self.session.commit()

        unknown_response = self.client.get("/mini-app/tours/UNKNOWN-CODE")
        collecting_group_response = self.client.get(f"/mini-app/tours/{collecting_group.code}")

        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(unknown_response.json()["detail"], "tour not found")
        self.assertEqual(collecting_group_response.status_code, 404)
        self.assertEqual(collecting_group_response.json()["detail"], "tour not found")

    def test_preparation_route_returns_preparation_options_for_open_tour(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-PREP-API",
            title_default="Belgrade Prep",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=3,
        )
        self.create_translation(tour, language_code="ro", title="Belgrad Pregatire API")
        point = self.create_boarding_point(tour, city="Timisoara", address="Central Station")
        self.session.commit()

        response = self.client.get(
            f"/mini-app/tours/{tour.code}/preparation",
            params={"language_code": "ro"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tour"]["code"], tour.code)
        self.assertEqual(payload["tour"]["localized_content"]["title"], "Belgrad Pregatire API")
        self.assertEqual(payload["seat_count_options"], [1, 2, 3])
        self.assertEqual(payload["boarding_points"][0]["id"], point.id)
        self.assertTrue(payload["preparation_only"])

    def test_preparation_summary_route_returns_preparation_only_summary(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-PREP-SUMMARY-API",
            title_default="Belgrade Prep Summary",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=4,
            base_price="95.00",
        )
        self.create_translation(tour, language_code="ro", title="Belgrad Rezumat API")
        point = self.create_boarding_point(tour, city="Arad", address="Main Station")
        self.session.commit()

        response = self.client.get(
            f"/mini-app/tours/{tour.code}/preparation-summary",
            params={
                "language_code": "ro",
                "seats_count": 2,
                "boarding_point_id": point.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tour"]["localized_content"]["title"], "Belgrad Rezumat API")
        self.assertEqual(payload["seats_count"], 2)
        self.assertEqual(payload["boarding_point"]["city"], "Arad")
        self.assertEqual(payload["estimated_total_amount"], "190.00")
        self.assertTrue(payload["preparation_only"])

    def test_preparation_routes_reject_invalid_or_unavailable_inputs(self) -> None:
        sold_out = self.create_tour(
            code="SOLDOUT-PREP-API",
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
        )
        point = self.create_boarding_point(sold_out)
        self.session.commit()

        unavailable_response = self.client.get(f"/mini-app/tours/{sold_out.code}/preparation")
        invalid_summary_response = self.client.get(
            f"/mini-app/tours/{sold_out.code}/preparation-summary",
            params={"seats_count": 1, "boarding_point_id": point.id},
        )

        self.assertEqual(unavailable_response.status_code, 404)
        self.assertEqual(
            unavailable_response.json()["detail"],
            "tour is not available for reservation preparation",
        )
        self.assertEqual(invalid_summary_response.status_code, 400)
        self.assertEqual(
            invalid_summary_response.json()["detail"],
            "invalid reservation preparation selection",
        )

    def test_create_reservation_and_payment_entry_routes(self) -> None:
        tour = self.create_tour(
            code="MINI-API-RESERVE",
            title_default="Mini API Reserve",
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 5, 11, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=4,
            base_price="80.00",
        )
        self.create_translation(tour, language_code="en", title="Mini API Reserve EN")
        point = self.create_boarding_point(tour)
        self.session.commit()

        telegram_user_id = 88_001
        reserve_response = self.client.post(
            f"/mini-app/tours/{tour.code}/reservations",
            params={"language_code": "en"},
            json={
                "telegram_user_id": telegram_user_id,
                "seats_count": 2,
                "boarding_point_id": point.id,
            },
        )
        self.assertEqual(reserve_response.status_code, 200)
        order_payload = reserve_response.json()["order"]
        self.assertEqual(order_payload["source_channel"], "mini_app")
        order_id = order_payload["id"]

        pay_response = self.client.post(
            f"/mini-app/orders/{order_id}/payment-entry",
            json={"telegram_user_id": telegram_user_id},
        )
        self.assertEqual(pay_response.status_code, 200)
        pay_json = pay_response.json()
        self.assertEqual(pay_json["order"]["id"], order_id)
        self.assertTrue(pay_json["payment_session_reference"])

    def test_create_reservation_returns_404_for_unknown_tour(self) -> None:
        response = self.client.post(
            "/mini-app/tours/UNKNOWN-CODE-NOPE/reservations",
            json={
                "telegram_user_id": 88_002,
                "seats_count": 1,
                "boarding_point_id": 1,
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "tour not found")

    def test_reservation_overview_returns_order_summary_for_owner(self) -> None:
        tour = self.create_tour(
            code="MINI-OVERVIEW-API",
            title_default="Overview API",
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 6, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=3,
            base_price="55.00",
        )
        self.create_translation(tour, language_code="en", title="Overview API EN")
        point = self.create_boarding_point(tour)
        self.session.commit()

        telegram_user_id = 88_010
        reserve = self.client.post(
            f"/mini-app/tours/{tour.code}/reservations",
            params={"language_code": "en"},
            json={
                "telegram_user_id": telegram_user_id,
                "seats_count": 1,
                "boarding_point_id": point.id,
            },
        )
        self.assertEqual(reserve.status_code, 200)
        order_id = reserve.json()["order"]["id"]

        overview = self.client.get(
            f"/mini-app/orders/{order_id}/reservation-overview",
            params={"telegram_user_id": telegram_user_id, "language_code": "en"},
        )
        self.assertEqual(overview.status_code, 200)
        body = overview.json()
        self.assertEqual(body["order"]["id"], order_id)
        self.assertIsNotNone(body["order"]["reservation_expires_at"])

    def test_bookings_list_empty_for_new_telegram_user(self) -> None:
        response = self.client.get("/mini-app/bookings", params={"telegram_user_id": 999_991})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])

    def test_bookings_list_and_booking_status_after_reservation(self) -> None:
        tour = self.create_tour(
            code="MINI-BOOKINGS-LIST",
            title_default="Bookings List Tour",
            departure_datetime=datetime(2026, 7, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 7, 11, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
            base_price="60.00",
        )
        self.create_translation(tour, language_code="en", title="Bookings List EN")
        point = self.create_boarding_point(tour)
        self.session.commit()

        telegram_user_id = 999_992
        reserve = self.client.post(
            f"/mini-app/tours/{tour.code}/reservations",
            params={"language_code": "en"},
            json={
                "telegram_user_id": telegram_user_id,
                "seats_count": 1,
                "boarding_point_id": point.id,
            },
        )
        self.assertEqual(reserve.status_code, 200)
        order_id = reserve.json()["order"]["id"]

        list_response = self.client.get(
            "/mini-app/bookings",
            params={"telegram_user_id": telegram_user_id, "language_code": "en"},
        )
        self.assertEqual(list_response.status_code, 200)
        items = list_response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["summary"]["order"]["id"], order_id)
        self.assertEqual(items[0]["facade_state"], "active_temporary_reservation")
        self.assertEqual(items[0]["primary_cta"], "pay_now")
        self.assertIn("user_visible_booking_label", items[0])

        detail_ok = self.client.get(
            f"/mini-app/orders/{order_id}/booking-status",
            params={"telegram_user_id": telegram_user_id, "language_code": "en"},
        )
        self.assertEqual(detail_ok.status_code, 200)
        detail_body = detail_ok.json()
        self.assertEqual(detail_body["summary"]["order"]["id"], order_id)
        self.assertEqual(detail_body["primary_cta"], "pay_now")

        detail_other = self.client.get(
            f"/mini-app/orders/{order_id}/booking-status",
            params={"telegram_user_id": 999_993, "language_code": "en"},
        )
        self.assertEqual(detail_other.status_code, 404)
