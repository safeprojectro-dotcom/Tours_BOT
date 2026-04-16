from __future__ import annotations

from datetime import UTC, date, datetime

from app.models.enums import TourStatus
from app.schemas.mini_app import MiniAppCatalogFiltersRead
from app.services.mini_app_catalog import MiniAppCatalogService
from tests.unit.base import FoundationDBTestCase


class MiniAppCatalogServiceTests(FoundationDBTestCase):
    def test_list_catalog_returns_filtered_open_for_sale_cards_only(self) -> None:
        matching = self.create_tour(
            code="BELGRADE-MINI",
            title_default="Belgrade Mini Break",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            base_price="140.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        collecting_group = self.create_tour(
            code="BELGRADE-GROUP",
            title_default="Belgrade Collecting Group",
            departure_datetime=datetime(2026, 4, 5, 9, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 21, 0, tzinfo=UTC),
            base_price="120.00",
            status=TourStatus.COLLECTING_GROUP,
        )
        different_destination = self.create_tour(
            code="BUDAPEST-MINI",
            title_default="Budapest Weekend",
            departure_datetime=datetime(2026, 4, 5, 10, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 22, 0, tzinfo=UTC),
            base_price="130.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        over_budget = self.create_tour(
            code="BELGRADE-PREMIUM",
            title_default="Belgrade Premium",
            departure_datetime=datetime(2026, 4, 5, 11, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 23, 0, tzinfo=UTC),
            base_price="240.00",
            status=TourStatus.OPEN_FOR_SALE,
        )

        for tour in (matching, collecting_group, different_destination, over_budget):
            self.create_translation(tour, language_code="ro", title=tour.title_default.replace("e", "e"))
            self.create_boarding_point(tour)

        result = MiniAppCatalogService().list_catalog(
            self.session,
            language_code="ro",
            filters=MiniAppCatalogFiltersRead(
                departure_date_from=date(2026, 4, 5),
                departure_date_to=date(2026, 4, 5),
                destination_query="Belgrade",
                max_price="150.00",
            ),
        )

        self.assertEqual([item.code for item in result.items], ["BELGRADE-MINI"])
        self.assertEqual(result.status_scope, [TourStatus.OPEN_FOR_SALE])
        self.assertEqual(result.limit, MiniAppCatalogService.DEFAULT_LIMIT)
        self.assertEqual(result.offset, 0)
        self.assertTrue(result.items[0].sales_mode_policy.per_seat_self_service_allowed)

    def test_list_catalog_rejects_invalid_date_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "departure date range is invalid"):
            MiniAppCatalogService().list_catalog(
                self.session,
                filters=MiniAppCatalogFiltersRead(
                    departure_date_from=date(2026, 4, 7),
                    departure_date_to=date(2026, 4, 5),
                ),
            )
