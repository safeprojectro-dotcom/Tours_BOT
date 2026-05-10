from __future__ import annotations

from datetime import UTC, date, datetime

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.models.order import Order
from app.schemas.mini_app import MiniAppCatalogFiltersRead
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind, describe_order_admin_lifecycle
from app.services.mini_app_catalog import MiniAppCatalogService
from tests.unit.base import FoundationDBTestCase


class MiniAppCatalogServiceTests(FoundationDBTestCase):
    def test_list_catalog_returns_filtered_open_for_sale_cards_only(self) -> None:
        matching = self.create_tour(
            code="BELGRADE-MINI",
            title_default="Belgrade Mini Break",
            departure_datetime=datetime(2027, 6, 15, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 20, 0, tzinfo=UTC),
            base_price="140.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        collecting_group = self.create_tour(
            code="BELGRADE-GROUP",
            title_default="Belgrade Collecting Group",
            departure_datetime=datetime(2027, 6, 15, 9, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 21, 0, tzinfo=UTC),
            base_price="120.00",
            status=TourStatus.COLLECTING_GROUP,
        )
        different_destination = self.create_tour(
            code="BUDAPEST-MINI",
            title_default="Budapest Weekend",
            departure_datetime=datetime(2027, 6, 15, 10, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 22, 0, tzinfo=UTC),
            base_price="130.00",
            status=TourStatus.OPEN_FOR_SALE,
        )
        over_budget = self.create_tour(
            code="BELGRADE-PREMIUM",
            title_default="Belgrade Premium",
            departure_datetime=datetime(2027, 6, 15, 11, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 6, 16, 23, 0, tzinfo=UTC),
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
                departure_date_from=date(2027, 6, 15),
                departure_date_to=date(2027, 6, 15),
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

    def test_list_catalog_persists_lazy_expiry_and_restores_seats(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="CAT-EXP-LAZY",
            title_default="Catalog Expiry Lazy",
            departure_datetime=datetime(2027, 8, 10, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 8, 12, 20, 0, tzinfo=UTC),
            base_price="99.00",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=10,
            seats_available=7,
        )
        self.create_translation(tour, language_code="ro", title="Cat Exp")
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=3,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        self.session.commit()

        MiniAppCatalogService().list_catalog(
            self.session,
            language_code="ro",
            filters=MiniAppCatalogFiltersRead(),
        )

        self.session.expire_all()
        refreshed_tour = self.session.get(type(tour), tour.id)
        refreshed_order = self.session.get(Order, order.id)
        assert refreshed_tour is not None and refreshed_order is not None
        self.assertEqual(refreshed_tour.seats_available, 10)
        kind, _ = describe_order_admin_lifecycle(refreshed_order)
        self.assertEqual(kind, AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD)

    def test_list_catalog_does_not_change_future_hold(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="CAT-FUTURE-HOLD",
            title_default="Future hold",
            departure_datetime=datetime(2027, 9, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 9, 3, 20, 0, tzinfo=UTC),
            base_price="80.00",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=10,
            seats_available=7,
        )
        self.create_translation(tour, language_code="ro", title="Fut")
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            seats_count=3,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2030, 1, 1, 12, 0, tzinfo=UTC),
        )
        self.session.commit()

        MiniAppCatalogService().list_catalog(self.session, language_code="ro", filters=MiniAppCatalogFiltersRead())

        self.session.expire_all()
        refreshed_tour = self.session.get(type(tour), tour.id)
        refreshed_order = self.session.get(Order, order.id)
        assert refreshed_tour is not None and refreshed_order is not None
        self.assertEqual(refreshed_tour.seats_available, 7)
        kind, _ = describe_order_admin_lifecycle(refreshed_order)
        self.assertEqual(kind, AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD)
