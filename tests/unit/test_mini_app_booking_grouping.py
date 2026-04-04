from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal

from app.models.enums import BookingStatus, PaymentStatus
from app.schemas.mini_app import (
    MiniAppBookingFacadeState,
    MiniAppBookingListItemRead,
    MiniAppBookingPrimaryCta,
)
from app.schemas.order import OrderRead
from app.schemas.prepared import LocalizedTourContentRead, OrderSummaryRead, OrderTourSummaryRead
from mini_app.booking_grouping import partition_bookings_for_my_bookings_ui


def _minimal_item(
    order_id: int,
    facade_state: MiniAppBookingFacadeState,
    *,
    cta: MiniAppBookingPrimaryCta = MiniAppBookingPrimaryCta.BACK_TO_BOOKINGS,
) -> MiniAppBookingListItemRead:
    lc = LocalizedTourContentRead(title="Tour")
    tour = OrderTourSummaryRead(
        id=1,
        code="T",
        departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        return_datetime=datetime(2026, 6, 2, 20, 0, tzinfo=UTC),
        localized_content=lc,
    )
    now = datetime.now(UTC)
    order = OrderRead(
        id=order_id,
        user_id=1,
        tour_id=1,
        boarding_point_id=1,
        seats_count=1,
        booking_status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.PAID,
        total_amount=Decimal("10.00"),
        currency="EUR",
        created_at=now,
        updated_at=now,
    )
    summary = OrderSummaryRead(
        order=order,
        booking_status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.PAID,
        tour=tour,
        boarding_point=None,
    )
    return MiniAppBookingListItemRead(
        summary=summary,
        user_visible_booking_label="",
        user_visible_payment_label="",
        facade_state=facade_state,
        primary_cta=cta,
    )


class PartitionBookingsTests(unittest.TestCase):
    def test_partitions_by_facade_state_order(self) -> None:
        items = [
            _minimal_item(1, MiniAppBookingFacadeState.CANCELLED_NO_PAYMENT),
            _minimal_item(2, MiniAppBookingFacadeState.CONFIRMED),
            _minimal_item(3, MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION, cta=MiniAppBookingPrimaryCta.PAY_NOW),
            _minimal_item(4, MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION),
            _minimal_item(5, MiniAppBookingFacadeState.IN_TRIP_PIPELINE),
            _minimal_item(6, MiniAppBookingFacadeState.OTHER),
        ]
        c, a, h = partition_bookings_for_my_bookings_ui(items)
        self.assertEqual([x.summary.order.id for x in c], [2, 5])
        self.assertEqual([x.summary.order.id for x in a], [3])
        self.assertEqual([x.summary.order.id for x in h], [1, 4, 6])

    def test_empty_input(self) -> None:
        c, a, h = partition_bookings_for_my_bookings_ui([])
        self.assertEqual(c, [])
        self.assertEqual(a, [])
        self.assertEqual(h, [])


if __name__ == "__main__":
    unittest.main()
