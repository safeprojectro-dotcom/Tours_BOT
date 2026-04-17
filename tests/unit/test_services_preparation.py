from __future__ import annotations

from datetime import UTC, datetime, time
from unittest.mock import patch

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourSalesMode, TourStatus
from app.schemas.prepared import CatalogBrowseFiltersRead
from app.schemas.prepared import PaymentSummaryRead
from app.services.catalog_preparation import CatalogPreparationService
from app.services.language_aware_tour import LanguageAwareTourReadService
from app.services.order_summary import OrderSummaryService
from app.services.payment_summary import PaymentSummaryService
from tests.unit.base import FoundationDBTestCase


class PreparationServiceTests(FoundationDBTestCase):
    def test_language_aware_tour_uses_translation_when_present(self) -> None:
        tour = self.create_tour(title_default="Default title")
        self.create_translation(
            tour,
            language_code="ro",
            title="Titlu RO",
            short_description="Scurt",
            full_description="Detaliat",
        )
        self.create_boarding_point(tour)

        result = LanguageAwareTourReadService().get_localized_tour_detail(
            self.session,
            tour_id=tour.id,
            language_code="ro",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.localized_content.title, "Titlu RO")
        self.assertFalse(result.localized_content.used_fallback)
        self.assertEqual(len(result.boarding_points), 1)
        self.assertTrue(result.sales_mode_policy.per_seat_self_service_allowed)
        self.assertEqual(result.sales_mode_policy.effective_sales_mode, TourSalesMode.PER_SEAT)

    def test_language_aware_tour_falls_back_to_default_fields(self) -> None:
        tour = self.create_tour(
            title_default="Default title",
            short_description_default="Default short",
            full_description_default="Default full",
        )
        self.create_boarding_point(tour)

        result = LanguageAwareTourReadService().get_localized_tour_detail(
            self.session,
            tour_id=tour.id,
            language_code="de",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.localized_content.title, "Default title")
        self.assertTrue(result.localized_content.used_fallback)
        self.assertIsNone(result.localized_content.resolved_language)

    def test_catalog_preparation_shapes_card_output(self) -> None:
        available_tour = self.create_tour(
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=3,
            title_default="Belgrade",
        )
        sold_out_tour = self.create_tour(
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=0,
            title_default="Budapest",
        )
        self.create_translation(available_tour, language_code="ro", title="Belgrad")
        self.create_translation(sold_out_tour, language_code="ro", title="Budapesta")
        self.create_boarding_point(available_tour, time=time(6, 0))
        self.create_boarding_point(sold_out_tour, time=time(7, 0))

        cards = CatalogPreparationService().list_catalog_cards(
            self.session,
            language_code="ro",
            status=TourStatus.OPEN_FOR_SALE,
        )

        by_code = {card.code: card for card in cards}
        self.assertIn(available_tour.code, by_code)
        self.assertIn(sold_out_tour.code, by_code)
        self.assertEqual(by_code[available_tour.code].title, "Belgrad")
        self.assertTrue(by_code[available_tour.code].is_available)
        self.assertFalse(by_code[sold_out_tour.code].is_available)

    @patch("app.services.reservation_expiry.datetime")
    def test_list_catalog_cards_lazy_expires_expired_holds(self, mock_datetime) -> None:
        """Opening catalog runs lazy expiry so seats_available reflect released holds."""
        mock_datetime.now.return_value = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
        mock_datetime.UTC = UTC

        user = self.create_user()
        tour = self.create_tour(
            code="CAT-LAZY",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=20,
            seats_available=5,
            title_default="Lazy catalog",
        )
        point = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            point,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        self.create_translation(tour, language_code="en", title="Lazy catalog EN")
        self.session.commit()

        cards = CatalogPreparationService().list_catalog_cards(
            self.session,
            language_code="en",
            status=TourStatus.OPEN_FOR_SALE,
        )
        by_code = {c.code: c for c in cards}
        self.assertIn(tour.code, by_code)
        self.assertEqual(by_code[tour.code].seats_available, 7)

    def test_catalog_preparation_filters_by_destination_date_and_budget(self) -> None:
        matching_departure = datetime(2027, 6, 15, 8, 0, tzinfo=UTC)
        matching = self.create_tour(
            code="BELGRADE-APR",
            title_default="Belgrade Escape",
            departure_datetime=matching_departure,
            return_datetime=datetime(2027, 6, 16, 22, 0, tzinfo=UTC),
            base_price="120.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        other_destination = self.create_tour(
            code="BUDAPEST-APR",
            title_default="Budapest Weekend",
            departure_datetime=datetime(2027, 6, 15, 9, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 21, 0, tzinfo=UTC),
            base_price="110.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        over_budget = self.create_tour(
            code="BELGRADE-PREMIUM",
            title_default="Belgrade Premium",
            departure_datetime=datetime(2027, 6, 15, 10, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 20, 0, tzinfo=UTC),
            base_price="220.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.create_translation(matching, language_code="ro", title="Belgrad Special")
        self.create_translation(other_destination, language_code="ro", title="Budapesta City Break")
        self.create_translation(over_budget, language_code="ro", title="Belgrad Premium")
        self.create_boarding_point(matching)
        self.create_boarding_point(other_destination)
        self.create_boarding_point(over_budget)

        cards = CatalogPreparationService().list_catalog_cards_filtered(
            self.session,
            language_code="ro",
            status=TourStatus.OPEN_FOR_SALE,
            filters=CatalogBrowseFiltersRead(
                departure_from=datetime(2027, 6, 15, 0, 0, tzinfo=UTC),
                departure_to=datetime(2027, 6, 15, 23, 59, tzinfo=UTC),
                destination_query="belgrad",
                max_price="150.00",
            ),
        )

        self.assertEqual([card.code for card in cards], ["BELGRADE-APR"])

    def test_list_catalog_cards_excludes_past_departure_open_tour(self) -> None:
        future = self.create_tour(
            code="PREP-CAT-FUTURE",
            title_default="Future trip",
            departure_datetime=datetime(2029, 1, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2029, 1, 12, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        past = self.create_tour(
            code="PREP-CAT-PAST",
            title_default="Past trip",
            departure_datetime=datetime(2017, 1, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2017, 1, 12, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        for tour in (future, past):
            self.create_translation(tour, language_code="ro", title=tour.title_default)
            self.create_boarding_point(tour)

        cards = CatalogPreparationService().list_catalog_cards(
            self.session,
            language_code="ro",
            status=TourStatus.OPEN_FOR_SALE,
        )
        codes = {c.code for c in cards}
        self.assertIn("PREP-CAT-FUTURE", codes)
        self.assertNotIn("PREP-CAT-PAST", codes)

    def test_list_catalog_cards_excludes_when_sales_deadline_in_past(self) -> None:
        tour = self.create_tour(
            code="PREP-SD-PAST",
            title_default="Sales window closed",
            departure_datetime=datetime(2031, 1, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2031, 1, 12, 20, 0, tzinfo=UTC),
            sales_deadline=datetime(2020, 6, 1, 12, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.create_translation(tour, language_code="en", title="Closed sales")
        self.create_boarding_point(tour)

        cards = CatalogPreparationService().list_catalog_cards(
            self.session,
            language_code="en",
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.assertNotIn("PREP-SD-PAST", {c.code for c in cards})

    def test_order_summary_prepares_localized_tour_and_boarding_point(self) -> None:
        user = self.create_user()
        tour = self.create_tour(code="SERBIA-1")
        self.create_translation(tour, language_code="ro", title="Serbia RO")
        point = self.create_boarding_point(tour, city="Arad", address="Central Station")
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
        )

        summary = OrderSummaryService().get_order_summary(
            self.session,
            order_id=order.id,
            language_code="ro",
        )

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.order.id, order.id)
        self.assertEqual(summary.tour.localized_content.title, "Serbia RO")
        self.assertIsNotNone(summary.boarding_point)
        assert summary.boarding_point is not None
        self.assertEqual(summary.boarding_point.city, "Arad")

    def test_payment_summary_prepares_latest_payment(self) -> None:
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        older = self.create_payment(order, external_payment_id="p1", status=PaymentStatus.UNPAID)
        newer = self.create_payment(order, external_payment_id="p2", status=PaymentStatus.PAID)

        summary = PaymentSummaryService().get_order_payment_summary(
            self.session,
            order_id=order.id,
        )

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(len(summary.payments), 2)
        self.assertIsNotNone(summary.latest_payment)
        assert summary.latest_payment is not None
        self.assertEqual(summary.latest_payment.id, newer.id)
        self.assertEqual(summary.payments[1].id, older.id)

    def test_empty_result_behavior_for_preparation_services(self) -> None:
        # DB may contain seeded tours outside this test transaction; assert empty via impossible filter.
        empty_cards = CatalogPreparationService().list_catalog_cards_filtered(
            self.session,
            filters=CatalogBrowseFiltersRead(destination_query="___no_such_destination_z9f2___"),
        )
        self.assertEqual(empty_cards, [])
        self.assertIsNone(
            LanguageAwareTourReadService().get_localized_tour_detail(
                self.session,
                tour_id=999999,
            )
        )
        self.assertIsNone(OrderSummaryService().get_order_summary(self.session, order_id=999999))
        self.assertIsNone(PaymentSummaryService().get_order_payment_summary(self.session, order_id=999999))
