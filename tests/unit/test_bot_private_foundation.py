from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.bot.constants import (
    DATE_OPTION_NEXT_30_DAYS,
    DATE_OPTION_WEEKEND,
    REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX,
)
from app.bot.keyboards import build_tour_detail_keyboard
from app.bot.messages import (
    format_catalog_message,
    format_filtered_catalog_message,
    format_payment_entry_message,
    format_reservation_preparation_summary,
    format_temporary_reservation_confirmation,
    format_tour_detail_message,
    translate,
)
from app.bot.services import (
    PrivateReservationPreparationService,
    PrivateTourBrowseService,
    TelegramUserContextService,
)
from app.services.catalog_preparation import CatalogPreparationService
from app.services.language_aware_tour import LanguageAwareTourReadService
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourSalesMode, TourStatus
from tests.unit.base import FoundationDBTestCase


class TelegramUserContextServiceTests(FoundationDBTestCase):
    def test_sync_private_user_uses_supported_telegram_language(self) -> None:
        service = TelegramUserContextService(supported_language_codes=("en", "ro", "ru"))

        user = service.sync_private_user(
            self.session,
            telegram_user_id=12345,
            username="traveler",
            first_name="Ana",
            last_name="Pop",
            telegram_language_code="ro-RO",
        )

        self.session.commit()
        self.assertEqual(user.preferred_language, "ro")
        self.assertEqual(user.source_channel, "private")

    def test_resolve_language_prefers_stored_user_language(self) -> None:
        user = self.create_user(telegram_user_id=555, preferred_language="ru")
        self.session.commit()
        service = TelegramUserContextService(supported_language_codes=("en", "ro", "ru"))

        resolved = service.resolve_language(
            self.session,
            telegram_user_id=user.telegram_user_id,
            telegram_language_code="en-US",
        )

        self.assertEqual(resolved, "ru")


class PrivateTourBrowseServiceTests(FoundationDBTestCase):
    def test_list_entry_tours_limits_to_three_open_tours(self) -> None:
        service = PrivateTourBrowseService()
        open_tours: list = []
        for index in range(4):
            tour = self.create_tour(
                code=f"OPEN-{index}",
                title_default=f"Open Tour {index}",
                status=TourStatus.OPEN_FOR_SALE,
            )
            open_tours.append(tour)
            self.create_translation(tour, language_code="ro", title=f"Tur {index}")
            self.create_boarding_point(tour)
        cancelled = self.create_tour(code="CANCELLED-1", status=TourStatus.CANCELLED)
        self.create_boarding_point(cancelled)
        self.session.commit()

        cards = service.list_entry_tours(self.session, language_code="ro", limit=50)
        open_ids = {t.id for t in open_tours}
        ours = sorted((c for c in cards if c.id in open_ids), key=lambda c: c.code)
        self.assertEqual(len(ours), 4)
        self.assertTrue(all(card.status == TourStatus.OPEN_FOR_SALE for card in ours))
        self.assertEqual(ours[0].title, "Tur 0")

        capped = service.list_entry_tours(self.session, language_code="ro", limit=3)
        self.assertEqual(len(capped), 3)

    def test_get_tour_detail_from_start_arg(self) -> None:
        service = PrivateTourBrowseService()
        tour = self.create_tour(code="BELGRADE-1", title_default="Belgrade")
        self.create_translation(tour, language_code="ro", title="Belgrad")
        self.create_boarding_point(tour, city="Timisoara")
        self.session.commit()

        detail = service.get_tour_detail_from_start_arg(
            self.session,
            start_arg="tour_BELGRADE-1",
            language_code="ro",
        )

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail.localized_content.title, "Belgrad")
        self.assertEqual(detail.boarding_points[0].city, "Timisoara")

    def test_get_tour_detail_from_start_arg_returns_none_when_departed(self) -> None:
        service = PrivateTourBrowseService()
        tour = self.create_tour(
            code="DEPARTED-START-ARG",
            title_default="Departed tour",
            departure_datetime=datetime(2014, 6, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2014, 6, 3, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.create_translation(tour, language_code="ro", title="Tur plecat")
        self.create_boarding_point(tour)
        self.session.commit()

        self.assertIsNone(
            service.get_tour_detail_from_start_arg(
                self.session,
                start_arg="tour_DEPARTED-START-ARG",
                language_code="ro",
            )
        )

    def test_list_entry_tours_filtered_by_destination_query(self) -> None:
        service = PrivateTourBrowseService()
        matching = self.create_tour(code="BELGRADE-1", title_default="Belgrade Escape")
        other = self.create_tour(code="BUDAPEST-1", title_default="Budapest Weekend")
        self.create_translation(matching, language_code="ro", title="Belgrad Escape")
        self.create_translation(other, language_code="ro", title="Budapesta Weekend")
        self.create_boarding_point(matching)
        self.create_boarding_point(other)
        self.session.commit()

        cards = service.list_entry_tours_filtered(
            self.session,
            language_code="ro",
            filters=service.build_destination_filters("Belgrad"),
        )

        belgrade = [card for card in cards if card.code == "BELGRADE-1"]
        self.assertEqual([c.code for c in belgrade], ["BELGRADE-1"])

    def test_build_date_filters_for_weekend_and_next_30_days(self) -> None:
        service = PrivateTourBrowseService()
        current = datetime(2026, 3, 27, 12, 0, tzinfo=UTC)

        weekend_filters = service.build_date_filters(DATE_OPTION_WEEKEND, now=current)
        next_30_days_filters = service.build_date_filters(DATE_OPTION_NEXT_30_DAYS, now=current)

        assert weekend_filters is not None
        assert next_30_days_filters is not None
        self.assertEqual(weekend_filters.departure_from, datetime(2026, 3, 28, 0, 0, tzinfo=UTC))
        self.assertEqual(weekend_filters.departure_to, datetime(2026, 3, 29, 23, 59, 59, 999999, tzinfo=UTC))
        self.assertEqual(next_30_days_filters.departure_from, current)
        self.assertEqual(next_30_days_filters.departure_to, datetime(2026, 4, 26, 12, 0, tzinfo=UTC))

    def test_budget_filter_currency_requires_single_currency_catalog(self) -> None:
        service = PrivateTourBrowseService()
        eur_tour = self.create_tour(code="EUR-1", currency="EUR")
        usd_tour = self.create_tour(code="USD-1", currency="USD")
        self.create_boarding_point(eur_tour)
        self.create_boarding_point(usd_tour)
        self.session.commit()

        currency = service.get_budget_filter_currency(
            self.session,
            language_code="en",
        )

        self.assertIsNone(currency)


class PrivateReservationPreparationServiceTests(FoundationDBTestCase):
    def test_get_preparable_tour_requires_open_tour_with_seats_and_boarding_point(self) -> None:
        service = PrivateReservationPreparationService()
        valid = self.create_tour(code="VALID-1", seats_available=3, status=TourStatus.OPEN_FOR_SALE)
        sold_out = self.create_tour(code="SOLDOUT-1", seats_available=0, status=TourStatus.OPEN_FOR_SALE)
        no_point = self.create_tour(code="NOPOINT-1", seats_available=2, status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(valid, language_code="ro", title="Valid RO")
        self.create_boarding_point(valid, city="Arad")
        self.create_boarding_point(sold_out, city="Timisoara")
        self.session.commit()

        valid_detail = service.get_preparable_tour(self.session, tour_id=valid.id, language_code="ro")
        sold_out_detail = service.get_preparable_tour(self.session, tour_id=sold_out.id, language_code="ro")
        no_point_detail = service.get_preparable_tour(self.session, tour_id=no_point.id, language_code="ro")

        self.assertIsNotNone(valid_detail)
        self.assertIsNone(sold_out_detail)
        self.assertIsNone(no_point_detail)

    def test_build_preparation_summary_uses_selected_seats_and_boarding_point(self) -> None:
        service = PrivateReservationPreparationService()
        tour = self.create_tour(code="BELGRADE-2", title_default="Belgrade", base_price="89.50", seats_available=4)
        self.create_translation(tour, language_code="ro", title="Belgrad")
        point = self.create_boarding_point(tour, city="Timisoara", address="Central Station")
        self.session.commit()

        summary = service.build_preparation_summary(
            self.session,
            tour_id=tour.id,
            seats_count=2,
            boarding_point_id=point.id,
            language_code="ro",
        )

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.tour.localized_content.title, "Belgrad")
        self.assertEqual(summary.seats_count, 2)
        self.assertEqual(summary.boarding_point.city, "Timisoara")
        self.assertEqual(str(summary.estimated_total_amount), "179.00")

    def test_build_preparation_summary_rejects_invalid_seat_count(self) -> None:
        service = PrivateReservationPreparationService()
        tour = self.create_tour(code="SMALL-1", seats_available=2)
        point = self.create_boarding_point(tour)
        self.session.commit()

        summary = service.build_preparation_summary(
            self.session,
            tour_id=tour.id,
            seats_count=3,
            boarding_point_id=point.id,
            language_code="en",
        )

        self.assertIsNone(summary)

    def test_list_seat_count_options_empty_for_full_bus(self) -> None:
        service = PrivateReservationPreparationService()
        tour = self.create_tour(
            code="FULLBUS-OPTS",
            seats_available=4,
            status=TourStatus.OPEN_FOR_SALE,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Charter")
        self.create_boarding_point(tour)
        self.session.commit()

        detail = LanguageAwareTourReadService().get_localized_tour_detail(
            self.session, tour_id=tour.id, language_code="en"
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertFalse(detail.sales_mode_policy.per_seat_self_service_allowed)
        self.assertEqual(service.list_seat_count_options(detail), ())

    def test_build_preparation_summary_none_for_full_bus_tour(self) -> None:
        service = PrivateReservationPreparationService()
        tour = self.create_tour(
            code="FULLBUS-SUM",
            seats_available=4,
            status=TourStatus.OPEN_FOR_SALE,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour)
        self.create_translation(tour, language_code="en", title="Charter")
        self.session.commit()

        summary = service.build_preparation_summary(
            self.session,
            tour_id=tour.id,
            seats_count=2,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNone(summary)


class BotMessageTemplateTests(unittest.TestCase):
    def test_router_home_body_translate_contains_mini_app_and_support(self) -> None:
        body = translate("en", "router_home_body")
        self.assertIn("Mini App", body)
        self.assertIn("/help", body)

    def test_translate_falls_back_to_english(self) -> None:
        self.assertEqual(
            translate("unknown", "catalog_empty"),
            "There are no open tours to show right now. Please try again later.",
        )

    def test_format_catalog_message_handles_empty_list(self) -> None:
        self.assertEqual(
            format_catalog_message("ro", []),
            "Momentan nu exista tururi deschise pentru vanzare. Te rog incearca mai tarziu.",
        )

    def test_format_filtered_catalog_message_handles_empty_list(self) -> None:
        self.assertEqual(
            format_filtered_catalog_message(
                "en",
                [],
                filter_summary="this weekend",
            ),
            "I could not find open tours matching: this weekend\n\nYou can try another filter or open the full tour list.",
        )

    def test_format_reservation_preparation_summary(self) -> None:
        from app.schemas.prepared import LocalizedTourContentRead, ReservationPreparationSummaryRead, ReservationPreparationTourRead
        from app.schemas.tour import BoardingPointRead

        summary = ReservationPreparationSummaryRead(
            tour=ReservationPreparationTourRead(
                id=1,
                code="BELGRADE-2",
                departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
                return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
                base_price="89.50",
                currency="EUR",
                seats_available_snapshot=4,
                localized_content=LocalizedTourContentRead(title="Belgrad"),
            ),
            seats_count=2,
            boarding_point=BoardingPointRead(
                id=10,
                tour_id=1,
                city="Timisoara",
                address="Central Station",
                time=datetime(2026, 4, 5, 6, 0, tzinfo=UTC).time(),
                notes=None,
            ),
            estimated_total_amount="179.00",
        )

        message = format_reservation_preparation_summary("en", summary)

        self.assertIn("Reservation preparation summary: Belgrad", message)
        self.assertIn("Seats: 2", message)
        self.assertIn("Estimated total: 179.00 EUR", message)

    def test_format_temporary_reservation_confirmation(self) -> None:
        from app.schemas.order import OrderRead
        from app.schemas.prepared import (
            LocalizedTourContentRead,
            OrderBoardingPointSummaryRead,
            OrderSummaryRead,
            OrderTourSummaryRead,
            PaymentEntryRead,
        )
        from app.schemas.payment import PaymentRead

        summary = OrderSummaryRead(
            order=OrderRead(
                id=7,
                user_id=1,
                tour_id=2,
                boarding_point_id=3,
                seats_count=2,
                booking_status=BookingStatus.RESERVED,
                payment_status=PaymentStatus.AWAITING_PAYMENT,
                cancellation_status=CancellationStatus.ACTIVE,
                reservation_expires_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
                total_amount="179.00",
                currency="EUR",
                source_channel="private",
                assigned_operator_id=None,
                created_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
                updated_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
            ),
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            tour=OrderTourSummaryRead(
                id=2,
                code="BELGRADE-2",
                departure_datetime=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
                return_datetime=datetime(2026, 4, 6, 20, 0, tzinfo=UTC),
                sales_mode=TourSalesMode.PER_SEAT,
                localized_content=LocalizedTourContentRead(title="Belgrad"),
            ),
            boarding_point=OrderBoardingPointSummaryRead(
                id=3,
                city="Timisoara",
                address="Central Station",
                time=datetime(2026, 4, 5, 6, 0, tzinfo=UTC).time(),
            ),
        )

        message = format_temporary_reservation_confirmation("en", summary)

        self.assertIn("Temporary reservation created: Belgrad", message)
        self.assertIn("Reservation reference: #7", message)
        self.assertIn("Reservation expires: 2026-04-05 12:00", message)

        payment_entry = PaymentEntryRead(
            order=summary.order,
            payment=PaymentRead(
                id=11,
                order_id=7,
                provider="mockpay",
                external_payment_id="mockpay-order-7-abc123",
                amount="179.00",
                currency="EUR",
                status=PaymentStatus.AWAITING_PAYMENT,
                raw_payload={"kind": "payment_entry"},
                created_at=datetime(2026, 4, 1, 8, 5, tzinfo=UTC),
                updated_at=datetime(2026, 4, 1, 8, 5, tzinfo=UTC),
            ),
            payment_session_reference="mockpay-order-7-abc123",
        )

        payment_message = format_payment_entry_message("en", payment_entry, tour_title="Belgrad")
        self.assertIn("Payment step ready: Belgrad", payment_message)
        self.assertIn("Payment session: mockpay-order-7-abc123", payment_message)
        self.assertIn("Amount due: 179.00 EUR", payment_message)


class PrivateBotSalesModeReadTests(FoundationDBTestCase):
    def test_format_tour_detail_message_includes_assisted_note_for_full_bus(self) -> None:
        tour = self.create_tour(
            code="CHARTER-DETAIL",
            title_default="Charter default",
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Charter trip")
        self.create_boarding_point(tour, city="Timisoara")
        self.session.commit()

        detail = LanguageAwareTourReadService().get_localized_tour_detail(
            self.session, tour_id=tour.id, language_code="en"
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        body = format_tour_detail_message("en", detail)
        self.assertIn("Automated self-serve booking", body)
        self.assertIn("charter or whole-vehicle package", body)
        self.assertFalse(detail.sales_mode_policy.per_seat_self_service_allowed)

    def test_format_catalog_message_marks_full_bus_card(self) -> None:
        tour = self.create_tour(
            code="CHARTER-CAT",
            status=TourStatus.OPEN_FOR_SALE,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Charter list")
        self.create_boarding_point(tour)
        self.session.commit()

        cards = CatalogPreparationService().list_catalog_cards(
            self.session,
            language_code="en",
            status=TourStatus.OPEN_FOR_SALE,
            limit=10,
        )
        ours = [c for c in cards if c.code == "CHARTER-CAT"]
        self.assertEqual(len(ours), 1)
        self.assertFalse(ours[0].sales_mode_policy.per_seat_self_service_allowed)
        text = format_catalog_message("en", ours)
        self.assertIn("team assistance", text.lower())

    def test_tour_detail_keyboard_prepare_vs_assistance(self) -> None:
        prep = build_tour_detail_keyboard(
            language_code="en",
            tour_id=42,
            mini_app_url=None,
            per_seat_self_service_allowed=True,
        )
        prep_data = [b.callback_data for row in prep.inline_keyboard for b in row]
        self.assertIn("prepare:tour:42", prep_data)
        self.assertFalse(any(x.startswith(f"{REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX}:") for x in prep_data))

        assisted = build_tour_detail_keyboard(
            language_code="en",
            tour_id=42,
            mini_app_url=None,
            per_seat_self_service_allowed=False,
        )
        asst_data = [b.callback_data for row in assisted.inline_keyboard for b in row]
        self.assertIn(f"{REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX}:42", asst_data)
        self.assertFalse(any(x and x.startswith("prepare:tour:") for x in asst_data))

    def test_tour_detail_keyboard_primary_webapp_exact_tour_url_b10_6(self) -> None:
        from app.services.supplier_offer_deep_link import mini_app_tour_detail_url

        m = build_tour_detail_keyboard(
            language_code="en",
            tour_id=99,
            mini_app_url="https://web.example/app/",
            tour_code="BELGRADE-1",
            per_seat_self_service_allowed=True,
        )
        urls = [
            b.web_app.url
            for row in m.inline_keyboard
            for b in row
            if b.web_app is not None
        ]
        self.assertIn(mini_app_tour_detail_url(mini_app_url="https://web.example/app/", tour_code="BELGRADE-1"), urls)
