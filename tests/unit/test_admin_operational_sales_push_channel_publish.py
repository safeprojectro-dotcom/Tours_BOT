"""S1D-2: admin-gated operational sales push channel publish."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import BookingStatus, PaymentStatus, TourStatus
from app.services.admin_operational_sales_push_preview_service import (
    AdminOperationalSalesPushPreviewService,
    channel_plain_text_for_operational_sales_push_read,
)
from tests.unit.base import FoundationDBTestCase


class AdminOperationalSalesPushChannelPublishTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"
        self._original_token = get_settings().telegram_bot_token
        self._original_ch = get_settings().telegram_offer_showcase_channel_id
        get_settings().telegram_bot_token = "test-tg-token-for-s1d2"
        get_settings().telegram_offer_showcase_channel_id = "-1001"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        get_settings().telegram_bot_token = self._original_token
        get_settings().telegram_offer_showcase_channel_id = self._original_ch
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def test_channel_plain_strips_preview_footer(self) -> None:
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
        out = channel_plain_text_for_operational_sales_push_read(read)
        assert out is not None
        self.assertNotIn("not published", out)
        self.assertNotIn("Operational sales push preview:", out)

    @patch("app.services.admin_operational_sales_push_publish_service.send_channel_plain_message", return_value=777001)
    @patch("app.services.admin_operational_sales_push_publish_service.get_settings")
    def test_post_publish_confirm_sends_to_channel(self, mock_settings, _mock_send) -> None:
        mock_s = MagicMock()
        mock_s.telegram_bot_token = "fake-token-for-test"
        mock_s.telegram_offer_showcase_channel_id = "-10042424242"
        mock_settings.return_value = mock_s

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

        r = self.client.post(
            f"/admin/tours/{tour.id}/operational-sales-push/publish",
            headers=self._headers(),
            json={"confirm": True},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["telegram_message_id"], 777001)
        self.assertEqual(body["tour_id"], tour.id)
        self.assertTrue(
            "Predeparture urgency" in body["message_plain_sent"] or "Low availability urgency" in body["message_plain_sent"],
            body["message_plain_sent"],
        )
        self.assertTrue(body["eligibility_recheck"]["eligible_for_operational_sales_push_preview"])

    def test_post_publish_requires_confirm(self) -> None:
        tour = self.create_tour(status=TourStatus.OPEN_FOR_SALE)
        self.session.commit()
        r = self.client.post(
            f"/admin/tours/{tour.id}/operational-sales-push/publish",
            headers=self._headers(),
            json={"confirm": False},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_post_publish_not_eligible_returns_400(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
        dep = now + timedelta(days=30)
        tour = self.create_tour(
            seats_total=40,
            seats_available=20,
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
            seats_count=20,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            total_amount=Decimal("100.00"),
        )
        self.session.commit()

        r = self.client.post(
            f"/admin/tours/{tour.id}/operational-sales-push/publish",
            headers=self._headers(),
            json={"confirm": True},
        )
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()["detail"]["code"], "operational_sales_push_not_eligible")

    @patch("app.services.admin_operational_sales_push_publish_service.get_settings")
    def test_post_publish_503_when_channel_missing(self, mock_settings) -> None:
        mock_s = MagicMock()
        mock_s.telegram_bot_token = None
        mock_s.telegram_offer_showcase_channel_id = None
        mock_settings.return_value = mock_s

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

        r = self.client.post(
            f"/admin/tours/{tour.id}/operational-sales-push/publish",
            headers=self._headers(),
            json={"confirm": True},
        )
        self.assertEqual(r.status_code, 503, r.text)
