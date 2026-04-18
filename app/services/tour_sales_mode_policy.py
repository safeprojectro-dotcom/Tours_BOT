"""Backend policy for `Tour.sales_mode` (Phase 7.1 / Step 2).

`policy_for_sales_mode` is enum-only. Track 5g.4a adds `policy_for_catalog_tour` for Mini App
catalog holds (full-bus virgin capacity) without changing RFQ bridge callers of `policy_for_tour`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from app.models.enums import TourSalesMode
from app.schemas.tour import TourRead
from app.schemas.tour_sales_mode_policy import TourSalesModePolicyRead

if TYPE_CHECKING:
    from app.models.tour import Tour

CatalogTourPolicySource = Union["Tour", TourRead]


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
                mini_app_catalog_reservation_allowed=True,
                catalog_charter_fixed_seats_count=None,
            )
        if sales_mode is TourSalesMode.FULL_BUS:
            return TourSalesModePolicyRead(
                effective_sales_mode=TourSalesMode.FULL_BUS,
                per_seat_self_service_allowed=False,
                direct_customer_booking_blocked_or_deferred=True,
                operator_path_required=True,
                mini_app_catalog_reservation_allowed=False,
                catalog_charter_fixed_seats_count=None,
            )
        raise ValueError(f"Unsupported tour sales mode: {sales_mode!r}")

    @classmethod
    def policy_for_catalog_tour(cls, tour: CatalogTourPolicySource) -> TourSalesModePolicyRead:
        """Mini App catalog path: full-bus self-serve only when virgin capacity (5g.4a).

        Accepts ORM `Tour` or `TourRead` (private bot preparation uses the latter).
        """
        base = cls.policy_for_sales_mode(tour.sales_mode)
        if tour.sales_mode is not TourSalesMode.FULL_BUS:
            return base
        virgin = tour.seats_total > 0 and tour.seats_available == tour.seats_total
        if not virgin:
            return base
        return base.model_copy(
            update={
                "mini_app_catalog_reservation_allowed": True,
                "catalog_charter_fixed_seats_count": tour.seats_total,
            }
        )

    @classmethod
    def policy_for_tour(cls, tour: Tour) -> TourSalesModePolicyRead:
        """Enum-only policy (RFQ bridge, legacy); does not apply virgin-capacity catalog rules."""
        return cls.policy_for_sales_mode(tour.sales_mode)
