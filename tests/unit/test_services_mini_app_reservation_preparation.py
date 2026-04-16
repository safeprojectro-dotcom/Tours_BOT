from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import TourSalesMode, TourStatus
from app.services.mini_app_reservation_preparation import MiniAppReservationPreparationService
from tests.unit.base import FoundationDBTestCase


class MiniAppReservationPreparationServiceTests(FoundationDBTestCase):
    def test_get_preparation_returns_seat_options_and_boarding_points(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-PREP",
            title_default="Belgrade Default",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=4,
        )
        self.create_translation(tour, language_code="ro", title="Belgrad Pregatire")
        point = self.create_boarding_point(tour, city="Timisoara", address="Central Station")

        result = MiniAppReservationPreparationService().get_preparation(
            self.session,
            code=tour.code,
            language_code="ro",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.tour.localized_content.title, "Belgrad Pregatire")
        self.assertEqual(result.seat_count_options, [1, 2, 3, 4])
        self.assertEqual(result.boarding_points[0].id, point.id)
        self.assertTrue(result.preparation_only)
        self.assertTrue(result.sales_mode_policy.per_seat_self_service_allowed)

    def test_get_preparation_full_bus_returns_empty_seat_options(self) -> None:
        tour = self.create_tour(
            code="FULL-BUS-PREP-SVC",
            title_default="Charter",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=8,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Charter EN")
        self.create_boarding_point(tour)

        result = MiniAppReservationPreparationService().get_preparation(
            self.session,
            code=tour.code,
            language_code="en",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.seat_count_options, [])
        self.assertFalse(result.sales_mode_policy.per_seat_self_service_allowed)

    def test_build_preparation_summary_returns_preview_only_summary(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-PREP-SUMMARY",
            title_default="Belgrade Summary",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
            base_price="90.00",
        )
        self.create_translation(tour, language_code="ro", title="Belgrad Rezumat")
        point = self.create_boarding_point(tour, city="Arad", address="Main Station")

        summary = MiniAppReservationPreparationService().build_preparation_summary(
            self.session,
            code=tour.code,
            seats_count=2,
            boarding_point_id=point.id,
            language_code="ro",
        )

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.tour.localized_content.title, "Belgrad Rezumat")
        self.assertEqual(summary.seats_count, 2)
        self.assertEqual(summary.boarding_point.city, "Arad")
        self.assertEqual(str(summary.estimated_total_amount), "180.00")
        self.assertTrue(summary.preparation_only)

    def test_build_preparation_summary_none_for_full_bus(self) -> None:
        tour = self.create_tour(
            code="FULL-BUS-SUMMARY-SVC",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour)

        summary = MiniAppReservationPreparationService().build_preparation_summary(
            self.session,
            code=tour.code,
            seats_count=2,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNone(summary)

    def test_preparation_returns_none_for_invalid_or_non_preparable_tour(self) -> None:
        sold_out = self.create_tour(
            code="SOLD-OUT-PREP",
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
        )
        collecting_group = self.create_tour(
            code="GROUP-PREP",
            status=TourStatus.COLLECTING_GROUP,
        )
        self.create_boarding_point(sold_out)
        self.create_boarding_point(collecting_group)

        service = MiniAppReservationPreparationService()
        self.assertIsNone(service.get_preparation(self.session, code=sold_out.code, language_code="en"))
        self.assertIsNone(service.get_preparation(self.session, code=collecting_group.code, language_code="en"))
        self.assertIsNone(service.build_preparation_summary(self.session, code="UNKNOWN", seats_count=1, boarding_point_id=1))
