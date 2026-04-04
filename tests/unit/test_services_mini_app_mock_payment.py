from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.core.config import get_settings
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from app.services.mini_app_mock_payment import MiniAppMockPaymentCompletionService
from tests.unit.base import FoundationDBTestCase


class MiniAppMockPaymentCompletionTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self._prev_mock = os.environ.get("ENABLE_MOCK_PAYMENT_COMPLETION")
        os.environ["ENABLE_MOCK_PAYMENT_COMPLETION"] = "true"
        get_settings.cache_clear()

    def tearDown(self) -> None:
        if self._prev_mock is None:
            os.environ.pop("ENABLE_MOCK_PAYMENT_COMPLETION", None)
        else:
            os.environ["ENABLE_MOCK_PAYMENT_COMPLETION"] = self._prev_mock
        get_settings.cache_clear()
        super().tearDown()

    def test_complete_mock_payment_confirms_order(self) -> None:
        user = self.create_user(telegram_user_id=77_001)
        tour = self.create_tour(
            code="MOCK-PAY-OK",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 7, 10, 8, 0, tzinfo=UTC),
            seats_available=10,
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime.now(UTC) + timedelta(hours=6),
        )
        self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-order-mock-1",
            status=PaymentStatus.AWAITING_PAYMENT,
        )
        self.session.commit()

        result = MiniAppMockPaymentCompletionService().complete_mock_payment_for_order(
            self.session,
            order_id=order.id,
            telegram_user_id=user.telegram_user_id,
        )
        self.session.commit()

        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.payment_confirmed)
        self.assertEqual(result.order.booking_status, BookingStatus.CONFIRMED)
        self.assertEqual(result.order.payment_status, PaymentStatus.PAID)
        self.assertIsNone(result.order.reservation_expires_at)

    @patch("app.services.mini_app_mock_payment.get_settings")
    def test_returns_none_when_feature_disabled(self, mock_gs: object) -> None:
        mock_gs.return_value.enable_mock_payment_completion = False
        result = MiniAppMockPaymentCompletionService().complete_mock_payment_for_order(
            self.session,
            order_id=999,
            telegram_user_id=1,
        )
        self.assertIsNone(result)
