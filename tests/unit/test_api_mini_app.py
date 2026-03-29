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
