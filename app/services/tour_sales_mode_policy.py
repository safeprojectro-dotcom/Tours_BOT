"""Backend policy for `Tour.sales_mode` (Phase 7.1 / Step 2).

Single boundary for commercial interpretation of sales mode. Policy is driven **only**
by `TourSalesMode` — never by `seats_total`, `seats_available`, or order size.

Not used by reservation, payment, Mini App, or private bot handlers in this step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.enums import TourSalesMode
from app.schemas.tour_sales_mode_policy import TourSalesModePolicyRead

if TYPE_CHECKING:
    from app.models.tour import Tour


class TourSalesModePolicyService:
    """Compute read-only policy views for tours."""

    @staticmethod
    def policy_for_sales_mode(sales_mode: TourSalesMode) -> TourSalesModePolicyRead:
        """Derive policy from enum value only (no tour row, no seat math)."""
        if sales_mode is TourSalesMode.PER_SEAT:
            return TourSalesModePolicyRead(
                effective_sales_mode=TourSalesMode.PER_SEAT,
                per_seat_self_service_allowed=True,
                direct_customer_booking_blocked_or_deferred=False,
                operator_path_required=False,
            )
        if sales_mode is TourSalesMode.FULL_BUS:
            return TourSalesModePolicyRead(
                effective_sales_mode=TourSalesMode.FULL_BUS,
                per_seat_self_service_allowed=False,
                direct_customer_booking_blocked_or_deferred=True,
                operator_path_required=True,
            )
        raise ValueError(f"Unsupported tour sales mode: {sales_mode!r}")

    @classmethod
    def policy_for_tour(cls, tour: Tour) -> TourSalesModePolicyRead:
        """Convenience: policy from `tour.sales_mode` only."""
        return cls.policy_for_sales_mode(tour.sales_mode)
