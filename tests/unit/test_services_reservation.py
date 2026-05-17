from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from sqlalchemy import select

from app.models.enums import (
    BookingStatus,
    PaymentStatus,
    SupplierOfferTourBridgeKind,
    SupplierOfferTourBridgeStatus,
    TourSalesMode,
    TourStatus,
)
from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.services.reservation_creation import TemporaryReservationService
from tests.unit.base import FoundationDBTestCase


class TemporaryReservationServiceTests(FoundationDBTestCase):
    @patch("app.services.reservation_creation.get_settings")
    def test_create_temporary_reservation_updates_seats_and_creates_reserved_order(
        self, mock_get_settings
    ) -> None:
        mock_get_settings.return_value.temp_reservation_ttl_minutes = None
        user = self.create_user()
        tour = self.create_tour(
            code="BELGRADE-RES-1",
            seats_available=5,
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        point = self.create_boarding_point(tour, city="Arad")
        self.session.commit()

        order = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=point.id,
            seats_count=2,
            source_channel="private",
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNotNone(order)
        assert order is not None
        self.assertEqual(order.booking_status, BookingStatus.RESERVED)
        self.assertEqual(order.payment_status, PaymentStatus.AWAITING_PAYMENT)
        self.assertEqual(order.seats_count, 2)
        self.assertEqual(str(order.total_amount), "199.98")
        self.assertEqual(order.reservation_expires_at, datetime(2026, 4, 2, 8, 0, tzinfo=UTC))

        refreshed_tour = self.session.get(type(tour), tour.id)
        assert refreshed_tour is not None
        self.assertEqual(refreshed_tour.seats_available, 3)

    @patch("app.services.reservation_creation.get_settings")
    def test_create_temporary_reservation_full_bus_uses_package_total(self, mock_get_settings) -> None:
        mock_get_settings.return_value.temp_reservation_ttl_minutes = None
        user = self.create_user()
        tour = self.create_tour(
            code="FULL-BUS-RES-TOTAL",
            seats_total=10,
            seats_available=10,
            base_price="500.00",
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 5, 9, 8, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        point = self.create_boarding_point(tour, city="Arad")
        self.session.commit()

        order = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=point.id,
            seats_count=10,
            source_channel="mini_app",
            now=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNotNone(order)
        assert order is not None
        self.assertEqual(str(order.total_amount), "500.00")

    def test_create_temporary_reservation_rejects_invalid_boarding_point_or_seats(self) -> None:
        user = self.create_user()
        tour = self.create_tour(seats_available=2, status=TourStatus.OPEN_FOR_SALE)
        other_tour = self.create_tour(seats_available=4, status=TourStatus.OPEN_FOR_SALE)
        invalid_point = self.create_boarding_point(other_tour)
        self.create_boarding_point(tour)
        self.session.commit()

        too_many = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=invalid_point.id,
            seats_count=3,
            source_channel="private",
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNone(too_many)

        wrong_point = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=invalid_point.id,
            seats_count=1,
            source_channel="private",
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNone(wrong_point)

    def test_create_temporary_reservation_rejects_closed_or_expired_tour(self) -> None:
        user = self.create_user()
        closed_tour = self.create_tour(
            status=TourStatus.SALES_CLOSED,
            departure_datetime=datetime(2026, 4, 3, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 2, 8, 0, tzinfo=UTC),
        )
        expired_deadline_tour = self.create_tour(
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 4, 3, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 1, 7, 0, tzinfo=UTC),
        )
        closed_point = self.create_boarding_point(closed_tour)
        expired_point = self.create_boarding_point(expired_deadline_tour)
        self.session.commit()

        closed_order = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=closed_tour.id,
            boarding_point_id=closed_point.id,
            seats_count=1,
            source_channel="private",
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        expired_order = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=expired_deadline_tour.id,
            boarding_point_id=expired_point.id,
            seats_count=1,
            source_channel="private",
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNone(closed_order)
        self.assertIsNone(expired_order)

    @patch("app.services.reservation_creation.get_settings")
    def test_calculate_reservation_expiration_caps_to_sales_deadline(self, mock_get_settings) -> None:
        mock_get_settings.return_value.temp_reservation_ttl_minutes = None
        tour = self.create_tour(
            departure_datetime=datetime(2026, 4, 3, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )

        expires_at = TemporaryReservationService().calculate_reservation_expiration(
            tour,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertEqual(expires_at, datetime(2026, 4, 1, 12, 0, tzinfo=UTC))

    @patch("app.services.reservation_creation.get_settings")
    def test_calculate_reservation_expiration_uses_ttl_minutes_from_settings(self, mock_get_settings) -> None:
        mock_get_settings.return_value.temp_reservation_ttl_minutes = 15
        tour = self.create_tour(
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )

        expires_at = TemporaryReservationService().calculate_reservation_expiration(
            tour,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertEqual(expires_at, datetime(2026, 4, 1, 8, 15, tzinfo=UTC))

    @patch("app.services.reservation_creation.get_settings")
    def test_calculate_reservation_expiration_ttl_minutes_still_caps_to_sales_deadline(
        self, mock_get_settings
    ) -> None:
        mock_get_settings.return_value.temp_reservation_ttl_minutes = 60
        tour = self.create_tour(
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 1, 8, 20, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )

        expires_at = TemporaryReservationService().calculate_reservation_expiration(
            tour,
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertEqual(expires_at, datetime(2026, 4, 1, 8, 20, tzinfo=UTC))

    @patch("app.services.reservation_creation.get_settings")
    def test_create_temporary_reservation_enqueues_supplier_order_created_outbox_s1c4(self, mock_get_settings) -> None:
        mock_get_settings.return_value.temp_reservation_ttl_minutes = None
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 888001
        offer = self.create_supplier_offer(supplier)
        user = self.create_user()
        tour = self.create_tour(
            code="S1C4-RES-BRIDGE",
            seats_available=5,
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        point = self.create_boarding_point(tour, city="TestCity")
        self.session.add(
            SupplierOfferTourBridge(
                supplier_offer_id=offer.id,
                tour_id=tour.id,
                status=SupplierOfferTourBridgeStatus.ACTIVE.value,
                bridge_kind=SupplierOfferTourBridgeKind.LINKED_EXISTING_TOUR.value,
                created_by="test",
                source_packaging_status=offer.packaging_status.value,
                source_lifecycle_status=offer.lifecycle_status.value,
                packaging_snapshot_json={},
            ),
        )
        self.session.commit()

        order_read = TemporaryReservationService().create_temporary_reservation(
            self.session,
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=point.id,
            seats_count=2,
            source_channel="mini_app",
            now=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIsNotNone(order_read)
        assert order_read is not None
        oid = order_read.id
        row = self.session.scalar(
            select(SupplierNotificationOutbox).where(
                SupplierNotificationOutbox.idempotency_key == f"s1c1:supplier_order_created:order:{oid}",
            ),
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.event_type, "supplier_order_created")
        self.assertEqual(row.order_id, oid)
        self.assertEqual(row.actor_surface, "s1c4_after_layer_a_temporary_reservation")
        self.assertEqual(row.dispatch_status, "pending_dispatch")
