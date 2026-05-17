"""S1D-1: admin operational sales-push preview (read-only; no publish)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import BookingStatus, PaymentStatus, TourStatus
from app.services.admin_operational_sales_push_preview_service import AdminOperationalSalesPushPreviewService
from tests.unit.base import FoundationDBTestCase


class AdminOperationalSalesPushPreviewTests(FoundationDBTestCase):
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

    def test_low_availability_only_far_departure(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
        dep = now + timedelta(days=14)
        tour = self.create_tour(
            seats_total=10,
            seats_available=2,
            departure_datetime=dep,
            sales_deadline=dep - timedelta(days=1),
            status=TourStatus.OPEN_FOR_SALE,
        )
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        self.create_order(
            u,
            tour,
            bp,
            seats_count=8,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("799.92"),
        )
        self.session.commit()

        read = AdminOperationalSalesPushPreviewService().read_for_tour(
            self.session, tour_id=tour.id, now=now
        )
        self.assertIsNotNone(read)
        assert read is not None
        self.assertFalse(read.predeparture_urgency_triggered)
        self.assertTrue(read.low_availability_urgency_triggered)
        self.assertTrue(read.eligible_for_operational_sales_push_preview)
        self.assertEqual(read.eligibility_block_codes, [])
        assert read.preview_plain is not None
        self.assertIn("Low availability urgency", read.preview_plain)
        self.assertNotIn("Predeparture urgency", read.preview_plain)

        r = self.client.get(
            f"/admin/tours/{tour.id}/operational-sales-push-preview",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["eligible_for_operational_sales_push_preview"])
        self.assertTrue(body["low_availability_urgency_triggered"])
        self.assertFalse(body["predeparture_urgency_triggered"])

    def test_predeparture_only_plenty_of_seats(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
        dep = now + timedelta(days=1)
        tour = self.create_tour(
            seats_total=40,
            seats_available=20,
            departure_datetime=dep,
            sales_deadline=dep - timedelta(hours=1),
            status=TourStatus.OPEN_FOR_SALE,
        )
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        self.create_order(
            u,
            tour,
            bp,
            seats_count=20,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("100.00"),
        )
        self.session.commit()

        read = AdminOperationalSalesPushPreviewService().read_for_tour(
            self.session, tour_id=tour.id, now=now
        )
        self.assertIsNotNone(read)
        assert read is not None
        self.assertTrue(read.predeparture_urgency_triggered)
        self.assertFalse(read.low_availability_urgency_triggered)
        self.assertTrue(read.eligible_for_operational_sales_push_preview)
        assert read.preview_plain is not None
        self.assertIn("Predeparture urgency", read.preview_plain)
        self.assertNotIn("Low availability urgency", read.preview_plain)

    def test_combined_predeparture_and_low_availability(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
        dep = now + timedelta(days=1)
        tour = self.create_tour(
            seats_total=40,
            seats_available=2,
            departure_datetime=dep,
            sales_deadline=dep - timedelta(hours=1),
            status=TourStatus.OPEN_FOR_SALE,
        )
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        self.create_order(
            u,
            tour,
            bp,
            seats_count=38,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("500.00"),
        )
        self.session.commit()

        read = AdminOperationalSalesPushPreviewService().read_for_tour(
            self.session, tour_id=tour.id, now=now
        )
        self.assertIsNotNone(read)
        assert read is not None
        self.assertTrue(read.predeparture_urgency_triggered)
        self.assertTrue(read.low_availability_urgency_triggered)
        self.assertTrue(read.eligible_for_operational_sales_push_preview)
        assert read.preview_plain is not None
        self.assertIn("Predeparture urgency", read.preview_plain)
        self.assertIn("Low availability urgency", read.preview_plain)

    def test_neither_trigger_blocks(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
        dep = now + timedelta(days=14)
        tour = self.create_tour(
            seats_total=40,
            seats_available=15,
            departure_datetime=dep,
            sales_deadline=dep - timedelta(days=1),
            status=TourStatus.OPEN_FOR_SALE,
        )
        bp = self.create_boarding_point(tour)
        u = self.create_user()
        self.create_order(
            u,
            tour,
            bp,
            seats_count=25,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("100.00"),
        )
        self.session.commit()

        read = AdminOperationalSalesPushPreviewService().read_for_tour(
            self.session, tour_id=tour.id, now=now
        )
        self.assertIsNotNone(read)
        assert read is not None
        self.assertFalse(read.eligible_for_operational_sales_push_preview)
        self.assertIn("s1d1_no_operational_sales_push_trigger", read.eligibility_block_codes)
        self.assertIsNone(read.preview_plain)

    def test_inventory_unverified_not_eligible(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
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
        self.session.commit()

        read = AdminOperationalSalesPushPreviewService().read_for_tour(
            self.session, tour_id=tour.id, now=now
        )
        self.assertIsNotNone(read)
        assert read is not None
        self.assertFalse(read.seats_inventory_trusted)
        self.assertFalse(read.eligible_for_operational_sales_push_preview)
        self.assertIn("s1d1_inventory_unverified", read.eligibility_block_codes)
