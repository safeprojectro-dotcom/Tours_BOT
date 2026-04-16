from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import TourStatus
from app.services.mini_app_tour_detail import MiniAppTourDetailService
from tests.unit.base import FoundationDBTestCase


class MiniAppTourDetailServiceTests(FoundationDBTestCase):
    def test_get_tour_detail_returns_localized_read_only_detail_for_open_tour(self) -> None:
        tour = self.create_tour(
            code="BELGRADE-DETAIL",
            title_default="Belgrade Default",
            short_description_default="Default short",
            full_description_default="Default full",
            departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
        )
        self.create_translation(
            tour,
            language_code="ro",
            title="Belgrad",
            short_description="Scurt RO",
            full_description="Detalii RO",
            program_text="Program RO",
            included_text="Inclus RO",
            excluded_text="Exclus RO",
        )
        self.create_boarding_point(tour, city="Timisoara")

        result = MiniAppTourDetailService().get_tour_detail(
            self.session,
            code=tour.code,
            language_code="ro",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.localized_content.title, "Belgrad")
        self.assertEqual(result.localized_content.full_description, "Detalii RO")
        self.assertEqual(result.tour.code, tour.code)
        self.assertTrue(result.is_available)
        self.assertEqual(len(result.boarding_points), 1)
        self.assertTrue(result.sales_mode_policy.per_seat_self_service_allowed)

    def test_get_tour_detail_returns_none_for_non_open_tour_or_unknown_code(self) -> None:
        collecting_group = self.create_tour(
            code="BELGRADE-GROUP-DETAIL",
            title_default="Belgrade Group",
            status=TourStatus.COLLECTING_GROUP,
        )
        self.create_translation(collecting_group, language_code="ro", title="Belgrad Grup")
        self.create_boarding_point(collecting_group)

        self.assertIsNone(
            MiniAppTourDetailService().get_tour_detail(
                self.session,
                code=collecting_group.code,
                language_code="ro",
            )
        )
        self.assertIsNone(
            MiniAppTourDetailService().get_tour_detail(
                self.session,
                code="UNKNOWN-CODE",
                language_code="ro",
            )
        )
