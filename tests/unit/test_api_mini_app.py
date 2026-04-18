from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourSalesMode, TourStatus
from app.models.handoff import Handoff
from app.models.waitlist import WaitlistEntry
from app.services.handoff_entry import HandoffEntryService
from app.repositories.user import UserRepository
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
            departure_datetime=datetime(2027, 6, 15, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 20, 0, tzinfo=UTC),
            base_price="140.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        other = self.create_tour(
            code="BUDAPEST-API",
            title_default="Budapest Weekend",
            departure_datetime=datetime(2027, 6, 15, 9, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 21, 0, tzinfo=UTC),
            base_price="110.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        collecting_group = self.create_tour(
            code="BELGRADE-GROUP-API",
            title_default="Belgrade Group Build",
            departure_datetime=datetime(2027, 6, 15, 10, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 22, 0, tzinfo=UTC),
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
                "departure_date_from": "2027-06-15",
                "departure_date_to": "2027-06-15",
                "max_price": "150.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["code"] for item in payload["items"]], ["BELGRADE-API"])
        self.assertEqual(payload["status_scope"], ["open_for_sale"])
        self.assertEqual(payload["applied_filters"]["destination_query"], "Belgrade")
        self.assertEqual(payload["items"][0]["sales_mode_policy"]["effective_sales_mode"], "per_seat")
        self.assertTrue(payload["items"][0]["sales_mode_policy"]["per_seat_self_service_allowed"])

    def test_customer_catalog_hides_past_departure_but_shows_future_open_tour(self) -> None:
        future = self.create_tour(
            code="MINI-CAT-FUTURE-VIS",
            title_default="Future Catalog Tour",
            departure_datetime=datetime(2028, 3, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2028, 3, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        past = self.create_tour(
            code="MINI-CAT-PAST-VIS",
            title_default="Past Catalog Tour",
            departure_datetime=datetime(2018, 3, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2018, 3, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        smoke_style = self.create_tour(
            code="MINI-SMOKE-STYLE-VISIBLE",
            title_default="Smoke style future",
            departure_datetime=datetime(2028, 4, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2028, 4, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        for tour in (future, past, smoke_style):
            self.create_translation(tour, language_code="en", title=tour.title_default)
            self.create_boarding_point(tour)
        self.session.commit()

        response = self.client.get("/mini-app/catalog", params={"language_code": "en"})
        self.assertEqual(response.status_code, 200)
        codes = {item["code"] for item in response.json()["items"]}
        self.assertIn("MINI-CAT-FUTURE-VIS", codes)
        self.assertIn("MINI-SMOKE-STYLE-VISIBLE", codes)
        self.assertNotIn("MINI-CAT-PAST-VIS", codes)

        past_detail = self.client.get("/mini-app/tours/MINI-CAT-PAST-VIS", params={"language_code": "en"})
        self.assertEqual(past_detail.status_code, 404)

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
            departure_datetime=datetime(2027, 6, 15, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 20, 0, tzinfo=UTC),
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
        self.assertEqual(payload["sales_mode_policy"]["effective_sales_mode"], "per_seat")
        self.assertTrue(payload["sales_mode_policy"]["per_seat_self_service_allowed"])
        self.assertEqual(payload["commercial_mode"], "supplier_route_per_seat")

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
            departure_datetime=datetime(2027, 6, 15, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 20, 0, tzinfo=UTC),
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
        self.assertTrue(payload["sales_mode_policy"]["per_seat_self_service_allowed"])

    def test_preparation_summary_route_returns_preparation_only_summary(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-PREP-SUMMARY-API",
            title_default="Belgrade Prep Summary",
            departure_datetime=datetime(2027, 6, 15, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 20, 0, tzinfo=UTC),
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

    def test_full_bus_preparation_read_side_no_self_service_seats(self) -> None:
        tour = self.create_tour(
            code="FULL-BUS-PREP-API",
            title_default="Charter Tour",
            departure_datetime=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 7, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=40,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Charter EN")
        self.create_boarding_point(tour)
        self.session.commit()

        prep = self.client.get(f"/mini-app/tours/{tour.code}/preparation", params={"language_code": "en"})
        self.assertEqual(prep.status_code, 200)
        body = prep.json()
        self.assertEqual(body["seat_count_options"], [])
        self.assertFalse(body["sales_mode_policy"]["per_seat_self_service_allowed"])
        self.assertTrue(body["sales_mode_policy"]["operator_path_required"])

        point_id = body["boarding_points"][0]["id"]
        summary = self.client.get(
            f"/mini-app/tours/{tour.code}/preparation-summary",
            params={"language_code": "en", "seats_count": 1, "boarding_point_id": point_id},
        )
        self.assertEqual(summary.status_code, 400)
        self.assertEqual(summary.json()["detail"], "invalid reservation preparation selection")

    def test_full_bus_reservation_post_rejected_with_policy_code(self) -> None:
        tour = self.create_tour(
            code="FULL-BUS-RES-API",
            title_default="Charter Reserve",
            departure_datetime=datetime(2026, 7, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 7, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=20,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        response = self.client.post(
            f"/mini-app/tours/{tour.code}/reservations",
            json={"telegram_user_id": 90_001, "seats_count": 2, "boarding_point_id": point.id},
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIsInstance(detail, dict)
        self.assertEqual(detail["code"], "mini_app_self_service_booking_not_available")

    def test_tour_detail_full_bus_shows_policy_without_prepare_path_in_api(self) -> None:
        tour = self.create_tour(
            code="FULL-BUS-DETAIL-API",
            title_default="Charter Detail",
            departure_datetime=datetime(2026, 7, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 7, 11, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=10,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Charter Detail EN")
        self.create_boarding_point(tour)
        self.session.commit()

        response = self.client.get(f"/mini-app/tours/{tour.code}", params={"language_code": "en"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["sales_mode_policy"]["per_seat_self_service_allowed"])
        self.assertEqual(payload["tour"]["sales_mode"], "full_bus")
        self.assertEqual(payload["commercial_mode"], "supplier_route_full_bus")

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

    def test_mini_app_help_route_returns_structure(self) -> None:
        response = self.client.get("/mini-app/help")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["title"], "Help")
        self.assertTrue(len(body["categories"]) >= 1)
        self.assertIn("operator_notice", body)
        self.assertIn("not implemented", body["operator_notice"].lower())

    def test_support_request_with_full_bus_tour_code_uses_structured_reason(self) -> None:
        self.create_user(telegram_user_id=888_101)
        tour = self.create_tour(
            code="MINI-FB-SUPPORT",
            title_default="Charter API",
            departure_datetime=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_boarding_point(tour)
        self.session.commit()

        response = self.client.post(
            "/mini-app/support-request",
            json={
                "telegram_user_id": 888_101,
                "order_id": None,
                "tour_code": tour.code,
                "screen_hint": "tour_detail",
            },
        )
        self.assertEqual(response.status_code, 200)
        hid = response.json()["handoff_id"]
        self.assertIsNotNone(hid)
        row = self.session.get(Handoff, hid)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertTrue(HandoffEntryService.is_full_bus_sales_assistance_reason(row.reason))
        self.assertIn("MINI-FB-SUPPORT", row.reason)
        self.assertIn("mini_app", row.reason)

    def test_support_request_per_seat_tour_code_stays_generic_mini_app(self) -> None:
        self.create_user(telegram_user_id=888_102)
        tour = self.create_tour(
            code="MINI-PS-SUPPORT",
            title_default="Per seat API",
            departure_datetime=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.create_boarding_point(tour)
        self.session.commit()

        response = self.client.post(
            "/mini-app/support-request",
            json={
                "telegram_user_id": 888_102,
                "order_id": None,
                "tour_code": tour.code,
                "screen_hint": "help",
            },
        )
        self.assertEqual(response.status_code, 200)
        hid = response.json()["handoff_id"]
        row = self.session.get(Handoff, hid)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertFalse(HandoffEntryService.is_full_bus_sales_assistance_reason(row.reason))
        self.assertTrue(row.reason.startswith(f"{HandoffEntryService.REASON_MINI_APP_PREFIX}|"))

    def test_mini_app_settings_route_returns_supported_languages(self) -> None:
        response = self.client.get("/mini-app/settings")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("en", body["supported_languages"])
        self.assertIn(body["resolved_language"], body["supported_languages"])
        self.assertIn("mock_payment_completion_enabled", body)
        self.assertFalse(body["mock_payment_completion_enabled"])

    def test_mini_app_settings_with_telegram_user_reflects_preferred_language(self) -> None:
        self.create_user(telegram_user_id=777_010, preferred_language="ro")
        self.session.commit()
        response = self.client.get("/mini-app/settings", params={"telegram_user_id": 777_010})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["active_language"], "ro")
        self.assertEqual(body["resolved_language"], "ro")

    def test_mini_app_language_preference_updates_profile(self) -> None:
        self.create_user(telegram_user_id=777_011, preferred_language="en")
        self.session.commit()
        response = self.client.post(
            "/mini-app/language-preference",
            json={"telegram_user_id": 777_011, "language_code": "de"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["language_code"], "de")
        self.session.expire_all()
        user = UserRepository().get_by_telegram_user_id(self.session, telegram_user_id=777_011)
        self.assertIsNotNone(user)
        assert user is not None
        self.assertEqual(user.preferred_language, "de")

    def test_mini_app_language_preference_rejects_unknown_code(self) -> None:
        self.create_user(telegram_user_id=777_012, preferred_language="en")
        self.session.commit()
        response = self.client.post(
            "/mini-app/language-preference",
            json={"telegram_user_id": 777_012, "language_code": "xx"},
        )
        self.assertEqual(response.status_code, 400)

    def test_mock_payment_complete_confirms_booking_when_enabled(self) -> None:
        prev = os.environ.get("ENABLE_MOCK_PAYMENT_COMPLETION")
        os.environ["ENABLE_MOCK_PAYMENT_COMPLETION"] = "true"
        get_settings.cache_clear()
        try:
            tour = self.create_tour(
                code="MINI-MOCK-PAY",
                title_default="Mock Pay Tour",
                departure_datetime=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
                return_datetime=datetime(2026, 8, 11, 20, 0, tzinfo=UTC),
                status=TourStatus.OPEN_FOR_SALE,
                seats_available=4,
                base_price="80.00",
            )
            self.create_translation(tour, language_code="en", title="Mock Pay Tour EN")
            point = self.create_boarding_point(tour)
            self.session.commit()

            telegram_user_id = 88_500
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
            order_id = reserve_response.json()["order"]["id"]

            pay_response = self.client.post(
                f"/mini-app/orders/{order_id}/payment-entry",
                json={"telegram_user_id": telegram_user_id},
            )
            self.assertEqual(pay_response.status_code, 200)

            done = self.client.post(
                f"/mini-app/orders/{order_id}/mock-payment-complete",
                json={"telegram_user_id": telegram_user_id},
            )
            self.assertEqual(done.status_code, 200)
            payload = done.json()
            self.assertTrue(payload["payment_confirmed"])
            self.assertEqual(payload["order"]["booking_status"], "confirmed")
            self.assertEqual(payload["order"]["payment_status"], "paid")
            self.assertIsNone(payload["order"]["reservation_expires_at"])
        finally:
            if prev is None:
                os.environ.pop("ENABLE_MOCK_PAYMENT_COMPLETION", None)
            else:
                os.environ["ENABLE_MOCK_PAYMENT_COMPLETION"] = prev
            get_settings.cache_clear()

    def test_mock_payment_complete_returns_403_when_disabled(self) -> None:
        response = self.client.post(
            "/mini-app/orders/1/mock-payment-complete",
            json={"telegram_user_id": 1},
        )
        self.assertEqual(response.status_code, 403)

    def test_waitlist_status_eligible_when_sold_out_open_tour(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-STATUS-SO",
            title_default="Waitlist Status",
            departure_datetime=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        self.session.commit()
        response = self.client.get(
            f"/mini-app/tours/{tour.code}/waitlist-status",
            params={"telegram_user_id": 77_101},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "eligible": True,
                "on_waitlist": False,
                "waitlist_status": None,
                "waitlist_entry_id": None,
            },
        )

    def test_waitlist_status_not_eligible_when_seats_available(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-STATUS-SEATS",
            title_default="Waitlist Seats",
            departure_datetime=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=4,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        self.session.commit()
        response = self.client.get(
            f"/mini-app/tours/{tour.code}/waitlist-status",
            params={"telegram_user_id": 77_102},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "eligible": False,
                "on_waitlist": False,
                "waitlist_status": None,
                "waitlist_entry_id": None,
            },
        )

    def test_waitlist_status_active_row(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-STATUS-ACT",
            title_default="Waitlist Active",
            departure_datetime=datetime(2026, 9, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 11, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        user = self.create_user(telegram_user_id=77_110)
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=2, status="active")
        self.session.add(w)
        self.session.commit()
        response = self.client.get(
            f"/mini-app/tours/{tour.code}/waitlist-status",
            params={"telegram_user_id": 77_110},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["eligible"])
        self.assertTrue(body["on_waitlist"])
        self.assertEqual(body["waitlist_status"], "active")
        self.assertEqual(body["waitlist_entry_id"], w.id)

    def test_waitlist_status_in_review(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-STATUS-REV",
            title_default="Waitlist In Review",
            departure_datetime=datetime(2026, 9, 11, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 12, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        user = self.create_user(telegram_user_id=77_111)
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=1, status="in_review")
        self.session.add(w)
        self.session.commit()
        response = self.client.get(
            f"/mini-app/tours/{tour.code}/waitlist-status",
            params={"telegram_user_id": 77_111},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["eligible"])
        self.assertTrue(body["on_waitlist"])
        self.assertEqual(body["waitlist_status"], "in_review")
        self.assertEqual(body["waitlist_entry_id"], w.id)

    def test_waitlist_status_closed(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-STATUS-CL",
            title_default="Waitlist Closed",
            departure_datetime=datetime(2026, 9, 12, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 13, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        user = self.create_user(telegram_user_id=77_112)
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=1, status="closed")
        self.session.add(w)
        self.session.commit()
        response = self.client.get(
            f"/mini-app/tours/{tour.code}/waitlist-status",
            params={"telegram_user_id": 77_112},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["eligible"])
        self.assertFalse(body["on_waitlist"])
        self.assertEqual(body["waitlist_status"], "closed")
        self.assertEqual(body["waitlist_entry_id"], w.id)

    def test_waitlist_join_created_then_already_exists(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-JOIN",
            title_default="Waitlist Join",
            departure_datetime=datetime(2026, 9, 3, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 4, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        self.session.commit()
        telegram_user_id = 77_103
        first = self.client.post(
            f"/mini-app/tours/{tour.code}/waitlist",
            json={"telegram_user_id": telegram_user_id, "seats_count": 2},
        )
        self.assertEqual(first.status_code, 200)
        body1 = first.json()
        self.assertEqual(body1["outcome"], "created")
        self.assertIsNotNone(body1["waitlist_entry_id"])

        second = self.client.post(
            f"/mini-app/tours/{tour.code}/waitlist",
            json={"telegram_user_id": telegram_user_id, "seats_count": 1},
        )
        self.assertEqual(second.status_code, 200)
        body2 = second.json()
        self.assertEqual(body2["outcome"], "already_exists")
        self.assertEqual(body2["waitlist_entry_id"], body1["waitlist_entry_id"])

    def test_waitlist_join_already_exists_when_in_review(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-JOIN-REV",
            title_default="Waitlist Join Rev",
            departure_datetime=datetime(2026, 9, 13, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 14, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        user = self.create_user(telegram_user_id=77_113)
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=1, status="in_review")
        self.session.add(w)
        self.session.commit()
        response = self.client.post(
            f"/mini-app/tours/{tour.code}/waitlist",
            json={"telegram_user_id": 77_113, "seats_count": 1},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "already_exists")
        self.assertEqual(body["waitlist_entry_id"], w.id)

    def test_waitlist_join_not_eligible_when_seats_available(self) -> None:
        tour = self.create_tour(
            code="WAITLIST-NOT-ELIG",
            title_default="Not Elig",
            departure_datetime=datetime(2026, 9, 4, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 9, 5, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
            base_price="50.00",
        )
        self.create_boarding_point(tour)
        self.session.commit()
        response = self.client.post(
            f"/mini-app/tours/{tour.code}/waitlist",
            json={"telegram_user_id": 77_104, "seats_count": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["outcome"], "not_eligible")

    def test_waitlist_join_invalid_tour(self) -> None:
        response = self.client.post(
            "/mini-app/tours/UNKNOWN-WAITLIST-XYZ/waitlist",
            json={"telegram_user_id": 77_105, "seats_count": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["outcome"], "invalid_tour")
