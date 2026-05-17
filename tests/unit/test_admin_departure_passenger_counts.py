"""S1A: read-only admin departure passenger count aggregates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    BookingStatus,
    CancellationStatus,
    PaymentStatus,
    SupplierOfferTourBridgeKind,
    SupplierOfferTourBridgeStatus,
)
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from tests.unit.base import FoundationDBTestCase


class AdminDeparturePassengerCountsTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def test_tour_counts_shape_and_buckets(self) -> None:
        tour = self.create_tour(seats_total=40, seats_available=35)
        bp = self.create_boarding_point(tour)
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        exp = datetime.now(UTC) + timedelta(hours=1)
        self.create_order(
            u1,
            tour,
            bp,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("199.98"),
        )
        self.create_order(
            u2,
            tour,
            bp,
            seats_count=3,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            reservation_expires_at=exp,
            total_amount=Decimal("299.97"),
        )
        self.create_order(
            u3,
            tour,
            bp,
            seats_count=1,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.CANCELLED_BY_CLIENT,
            total_amount=Decimal("99.99"),
        )

        r = self.client.get(f"/admin/tours/{tour.id}/departure-passenger-counts", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["tour_id"], tour.id)
        self.assertEqual(body["total_orders_count"], 3)
        self.assertEqual(body["active_orders_count"], 2)
        self.assertEqual(body["paid_confirmed_orders_count"], 1)
        self.assertEqual(body["paid_confirmed_passenger_count"], 2)
        self.assertEqual(body["reserved_unpaid_orders_count"], 1)
        self.assertEqual(body["reserved_unpaid_passenger_count"], 3)
        self.assertEqual(body["cancelled_orders_count"], 1)
        self.assertEqual(body["cancelled_passenger_count"], 1)
        self.assertEqual(body["active_passenger_count"], 5)
        self.assertEqual(body["capacity"], 40)
        self.assertEqual(body["seats_available"], 35)
        self.assertEqual(body["remaining_capacity"], 35)
        self.assertEqual(body["other_active_orders_count"], 0)
        self.assertNotIn("s1a_inventory_vs_active_order_seats_mismatch", body["readiness_warnings"])

    def test_inventory_mismatch_warning(self) -> None:
        tour = self.create_tour(seats_total=40, seats_available=35)
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        self.create_order(
            u,
            tour,
            bp,
            seats_count=2,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("99.99"),
        )

        r = self.client.get(f"/admin/tours/{tour.id}/departure-passenger-counts", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("s1a_inventory_vs_active_order_seats_mismatch", r.json()["readiness_warnings"])

    def test_other_active_order_warning(self) -> None:
        tour = self.create_tour(seats_total=40, seats_available=38)
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        self.create_order(
            u,
            tour,
            bp,
            seats_count=2,
            booking_status=BookingStatus.NEW,
            payment_status=PaymentStatus.UNPAID,
            total_amount=Decimal("99.99"),
        )

        r = self.client.get(f"/admin/tours/{tour.id}/departure-passenger-counts", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["other_active_orders_count"], 1)
        self.assertIn("s1a_unexpected_active_order_state_mix", body["readiness_warnings"])

    def test_expired_hold_warning(self) -> None:
        tour = self.create_tour(seats_total=40, seats_available=38)
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        past = datetime.now(UTC) - timedelta(minutes=5)
        self.create_order(
            u,
            tour,
            bp,
            seats_count=2,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            reservation_expires_at=past,
            total_amount=Decimal("99.99"),
        )

        r = self.client.get(f"/admin/tours/{tour.id}/departure-passenger-counts", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("s1a_expired_temporary_hold_not_released", r.json()["readiness_warnings"])

    def test_offer_resolves_via_execution_link_before_bridge(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        tour_a = self.create_tour(code="TA-S1A", seats_total=30, seats_available=28)
        tour_b = self.create_tour(code="TB-S1A", seats_total=30, seats_available=25)
        self.session.add(
            SupplierOfferTourBridge(
                supplier_offer_id=offer.id,
                tour_id=tour_a.id,
                status=SupplierOfferTourBridgeStatus.ACTIVE.value,
                bridge_kind=SupplierOfferTourBridgeKind.LINKED_EXISTING_TOUR.value,
                created_by="test",
                source_packaging_status=offer.packaging_status.value,
                source_lifecycle_status=offer.lifecycle_status.value,
                packaging_snapshot_json={},
            ),
        )
        self.session.add(
            SupplierOfferExecutionLink(supplier_offer_id=offer.id, tour_id=tour_b.id, link_status="active"),
        )
        self.session.flush()

        r = self.client.get(
            f"/admin/supplier-offers/{offer.id}/departure-passenger-counts",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["tour_id"], tour_b.id)
        self.assertEqual(r.json()["resolution_source"], "supplier_offer_execution_link")

    def test_offer_falls_back_to_bridge(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        tour = self.create_tour(code="TC-S1A", seats_total=20, seats_available=20)
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
        self.session.flush()

        r = self.client.get(
            f"/admin/supplier-offers/{offer.id}/departure-passenger-counts",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["tour_id"], tour.id)
        self.assertEqual(r.json()["resolution_source"], "supplier_offer_tour_bridge")

    def test_offer_without_link_404(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        r = self.client.get(
            f"/admin/supplier-offers/{offer.id}/departure-passenger-counts",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 404, r.text)

    def test_supplier_list_two_tours(self) -> None:
        supplier = self.create_supplier()
        o1 = self.create_supplier_offer(supplier)
        o2 = self.create_supplier_offer(supplier)
        t1 = self.create_tour(code="S1-LIST-1", departure_datetime=datetime.now(UTC) + timedelta(days=3))
        t2 = self.create_tour(code="S1-LIST-2", departure_datetime=datetime.now(UTC) + timedelta(days=10))
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=o1.id, tour_id=t1.id, link_status="active"))
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=o2.id, tour_id=t2.id, link_status="active"))
        self.session.flush()

        r = self.client.get(
            f"/admin/suppliers/{supplier.id}/departure-passenger-counts",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["supplier_id"], supplier.id)
        self.assertEqual(len(body["items"]), 2)
        codes = [item["tour_code"] for item in body["items"]]
        self.assertEqual(codes, ["S1-LIST-1", "S1-LIST-2"])

    def test_supplier_no_links_returns_warning(self) -> None:
        supplier = self.create_supplier()
        self.create_supplier_offer(supplier)
        r = self.client.get(
            f"/admin/suppliers/{supplier.id}/departure-passenger-counts",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("s1a_supplier_no_active_tour_links", r.json()["readiness_warnings"])
        self.assertEqual(r.json()["items"], [])
