from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.enums import PaymentStatus, TourSalesMode, TourStatus
from app.services.mini_app_booking import (
    MINI_APP_SOURCE_CHANNEL,
    MiniAppBookingService,
    MiniAppSelfServiceBookingNotAllowedError,
)
from tests.unit.base import FoundationDBTestCase


class MiniAppBookingServiceTests(FoundationDBTestCase):
    def test_create_temporary_reservation_returns_summary_with_mini_app_source(self) -> None:
        tour = self.create_tour(
            code="MINI-BOOK-1",
            title_default="Mini Book",
            departure_datetime=datetime.now(UTC) + timedelta(days=10),
            return_datetime=datetime.now(UTC) + timedelta(days=12),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=5,
            base_price="50.00",
        )
        self.create_translation(tour, language_code="en", title="Mini Book EN")
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        summary = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=77_001,
            seats_count=2,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.order.source_channel, MINI_APP_SOURCE_CHANNEL)
        self.assertEqual(summary.order.seats_count, 2)
        self.assertEqual(summary.order.payment_status, PaymentStatus.AWAITING_PAYMENT)

    def test_create_temporary_reservation_returns_none_when_invalid(self) -> None:
        tour = self.create_tour(
            code="MINI-BOOK-BAD",
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=1,
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        too_many = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=77_002,
            seats_count=5,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNone(too_many)

    def test_create_temporary_reservation_raises_when_sales_mode_disallows_self_service(self) -> None:
        tour = self.create_tour(
            code="MINI-BOOK-FULL-BUS",
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=10,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        with self.assertRaises(MiniAppSelfServiceBookingNotAllowedError):
            svc.create_temporary_reservation(
                self.session,
                tour_code=tour.code,
                telegram_user_id=77_099,
                seats_count=1,
                boarding_point_id=point.id,
                language_code="en",
            )

    def test_start_payment_entry_returns_entry_for_same_user(self) -> None:
        user = self.create_user(telegram_user_id=77_003)
        tour = self.create_tour(
            code="MINI-PAY-1",
            departure_datetime=datetime.now(UTC) + timedelta(days=10),
            return_datetime=datetime.now(UTC) + timedelta(days=12),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=4,
            base_price="40.00",
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        summary = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=user.telegram_user_id,
            seats_count=1,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.session.commit()

        entry = svc.start_payment_entry(
            self.session,
            order_id=summary.order.id,
            telegram_user_id=user.telegram_user_id,
        )
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry.order.id, summary.order.id)
        self.assertTrue(entry.payment_session_reference)

    def test_get_reservation_overview_for_owner(self) -> None:
        user = self.create_user(telegram_user_id=77_004)
        tour = self.create_tour(
            code="MINI-OVERVIEW-1",
            departure_datetime=datetime.now(UTC) + timedelta(days=10),
            return_datetime=datetime.now(UTC) + timedelta(days=12),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=3,
            base_price="30.00",
        )
        self.create_translation(tour, language_code="en", title="Overview Tour")
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        summary = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=user.telegram_user_id,
            seats_count=1,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.session.commit()

        overview = svc.get_reservation_overview_for_user(
            self.session,
            order_id=summary.order.id,
            telegram_user_id=user.telegram_user_id,
            language_code="en",
        )
        self.assertIsNotNone(overview)
        assert overview is not None
        self.assertEqual(overview.order.id, summary.order.id)

    def test_get_reservation_overview_denies_other_telegram_user(self) -> None:
        owner = self.create_user(telegram_user_id=77_005)
        other = self.create_user(telegram_user_id=77_006)
        tour = self.create_tour(
            code="MINI-OVERVIEW-2",
            departure_datetime=datetime.now(UTC) + timedelta(days=10),
            return_datetime=datetime.now(UTC) + timedelta(days=12),
            status=TourStatus.OPEN_FOR_SALE,
            seats_available=2,
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        summary = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=owner.telegram_user_id,
            seats_count=1,
            boarding_point_id=point.id,
            language_code="en",
        )
        assert summary is not None
        self.session.commit()

        overview = svc.get_reservation_overview_for_user(
            self.session,
            order_id=summary.order.id,
            telegram_user_id=other.telegram_user_id,
            language_code="en",
        )
        self.assertIsNone(overview)

    def test_mode2_virgin_charter_payment_entry_reuses_pending_session(self) -> None:
        user = self.create_user(telegram_user_id=77_310)
        tour = self.create_tour(
            code="MINI-BOOK-MODE2-PAY",
            departure_datetime=datetime.now(UTC) + timedelta(days=14),
            return_datetime=datetime.now(UTC) + timedelta(days=16),
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=10,
            seats_available=10,
            base_price="60.00",
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.create_translation(tour, language_code="en", title="Mode2 Pay")
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        summary = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=user.telegram_user_id,
            seats_count=10,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(str(summary.order.total_amount), "60.00")
        self.assertEqual(summary.order.seats_count, 10)
        self.session.commit()

        entry1 = svc.start_payment_entry(
            self.session,
            order_id=summary.order.id,
            telegram_user_id=user.telegram_user_id,
        )
        self.assertIsNotNone(entry1)
        assert entry1 is not None
        self.assertFalse(entry1.reused_existing_payment)
        ref1 = entry1.payment_session_reference

        entry2 = svc.start_payment_entry(
            self.session,
            order_id=summary.order.id,
            telegram_user_id=user.telegram_user_id,
        )
        self.assertIsNotNone(entry2)
        assert entry2 is not None
        self.assertTrue(entry2.reused_existing_payment)
        self.assertEqual(entry2.payment_session_reference, ref1)

    def test_mode2_partial_charter_raises_not_allowed_not_seats_mismatch(self) -> None:
        tour = self.create_tour(
            code="MINI-BOOK-MODE2-PARTIAL",
            departure_datetime=datetime.now(UTC) + timedelta(days=15),
            return_datetime=datetime.now(UTC) + timedelta(days=17),
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=20,
            seats_available=7,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        with self.assertRaises(MiniAppSelfServiceBookingNotAllowedError):
            svc.create_temporary_reservation(
                self.session,
                tour_code=tour.code,
                telegram_user_id=77_311,
                seats_count=20,
                boarding_point_id=point.id,
                language_code="en",
            )

    def test_mode2_virgin_coerces_client_seats_count_to_fixed_charter(self) -> None:
        tour = self.create_tour(
            code="MINI-BOOK-MODE2-MISMATCH",
            departure_datetime=datetime.now(UTC) + timedelta(days=16),
            return_datetime=datetime.now(UTC) + timedelta(days=18),
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=8,
            seats_available=8,
            base_price="400.00",
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour)
        self.session.commit()

        svc = MiniAppBookingService()
        summary = svc.create_temporary_reservation(
            self.session,
            tour_code=tour.code,
            telegram_user_id=77_312,
            seats_count=3,
            boarding_point_id=point.id,
            language_code="en",
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.order.seats_count, 8)
        self.assertEqual(str(summary.order.total_amount), "400.00")
