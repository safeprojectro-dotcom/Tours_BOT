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
    updated_at: datetime | None = None,
) -> MiniAppBookingListItemRead:
    lc = LocalizedTourContentRead(title="Tour")
    tour = OrderTourSummaryRead(
        id=1,
        code="T",
        departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        return_datetime=datetime(2026, 6, 2, 20, 0, tzinfo=UTC),
        localized_content=lc,
    )
    now = updated_at or datetime.now(UTC)
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
        c, a, h, omitted = partition_bookings_for_my_bookings_ui(items)
        self.assertEqual(omitted, 0)
        self.assertEqual([x.summary.order.id for x in c], [2, 5])
        self.assertEqual([x.summary.order.id for x in a], [3])
        self.assertEqual([x.summary.order.id for x in h], [1, 4, 6])

    def test_empty_input(self) -> None:
        c, a, h, omitted = partition_bookings_for_my_bookings_ui([])
        self.assertEqual(omitted, 0)
        self.assertEqual(c, [])
        self.assertEqual(a, [])
        self.assertEqual(h, [])

    def test_history_sorted_newest_first_and_capped(self) -> None:
        base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        items = [
            _minimal_item(
                i + 1,
                MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION,
                updated_at=base.replace(day=i + 1),
            )
            for i in range(18)
        ]
        c, a, h, omitted = partition_bookings_for_my_bookings_ui(items)
        self.assertEqual(c, [])
        self.assertEqual(a, [])
        self.assertEqual(omitted, 3)
        self.assertEqual(len(h), 15)
        self.assertEqual([x.summary.order.id for x in h], list(range(18, 3, -1)))

    def test_history_unlimited_when_max_is_none(self) -> None:
        items = [
            _minimal_item(i + 1, MiniAppBookingFacadeState.OTHER, updated_at=datetime(2026, 2, i + 1, tzinfo=UTC))
            for i in range(20)
        ]
        c, a, h, omitted = partition_bookings_for_my_bookings_ui(items, history_max_items=None)
        self.assertEqual(omitted, 0)
        self.assertEqual(len(h), 20)


if __name__ == "__main__":
    unittest.main()
