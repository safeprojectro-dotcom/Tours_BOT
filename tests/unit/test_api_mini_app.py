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
