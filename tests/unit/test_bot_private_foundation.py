from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.bot.constants import DATE_OPTION_NEXT_30_DAYS, DATE_OPTION_WEEKEND
from app.bot.messages import (
    format_catalog_message,
    format_filtered_catalog_message,
    format_payment_entry_message,
    format_reservation_preparation_summary,
    format_temporary_reservation_confirmation,
    translate,
)
from app.bot.services import (
    PrivateReservationPreparationService,
    PrivateTourBrowseService,
    TelegramUserContextService,
)
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
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
        for index in range(4):
            tour = self.create_tour(
                code=f"OPEN-{index}",
                title_default=f"Open Tour {index}",
                status=TourStatus.OPEN_FOR_SALE,
            )
            self.create_translation(tour, language_code="ro", title=f"Tur {index}")
            self.create_boarding_point(tour)
        cancelled = self.create_tour(code="CANCELLED-1", status=TourStatus.CANCELLED)
        self.create_boarding_point(cancelled)
        self.session.commit()

        cards = service.list_entry_tours(self.session, language_code="ro", limit=3)

        self.assertEqual(len(cards), 3)
        self.assertTrue(all(card.status == TourStatus.OPEN_FOR_SALE for card in cards))
        self.assertEqual(cards[0].title, "Tur 0")

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

        self.assertEqual([card.code for card in cards], ["BELGRADE-1"])

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


class BotMessageTemplateTests(unittest.TestCase):
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
