"""Backend policy for `Tour.sales_mode` (Phase 7.1 / Step 2).

`policy_for_sales_mode` is enum-only. Track 5g.4a adds `policy_for_catalog_tour` for Mini App
catalog holds (full-bus virgin capacity) and explicit actionability classification, without
changing RFQ bridge callers of `policy_for_tour`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from app.models.enums import TourSalesMode
from app.schemas.tour import TourRead
from app.schemas.tour_sales_mode_policy import (
    CatalogActionabilityState,
    CatalogConversionProfile,
    TourSalesModePolicyRead,
)

if TYPE_CHECKING:
    from app.models.tour import Tour

CatalogTourPolicySource = Union["Tour", TourRead]


class TourSalesModePolicyService:
    """Compute read-only policy views for tours."""

    @staticmethod
    def _full_bus_catalog_actionability(*, seats_total: int, seats_available: int) -> CatalogActionabilityState:
        """Fail-safe classification for full-bus catalog actionability."""
        if seats_total <= 0:
            return CatalogActionabilityState.BLOCKED
        if seats_available < 0 or seats_available > seats_total:
            return CatalogActionabilityState.BLOCKED
        if seats_available <= 0:
            return CatalogActionabilityState.VIEW_ONLY
        if seats_available == seats_total:
            return CatalogActionabilityState.BOOKABLE
        return CatalogActionabilityState.ASSISTED_ONLY

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
                catalog_actionability_state=CatalogActionabilityState.BOOKABLE,
                catalog_conversion_profile=CatalogConversionProfile.PER_SEAT_STANDARD,
                reservation_cta_semantic_key="mini_app_cta_reserve_seats",
                price_display_semantic_key="price_display_per_person",
                capacity_display_semantic_key="capacity_display_live_seats_remaining",
                seat_selection_ux="free_numeric",
                bookable_as_full_bus_package=False,
                show_custom_trip_routing_hint=False,
            )
        if sales_mode is TourSalesMode.FULL_BUS:
            return TourSalesModePolicyRead(
                effective_sales_mode=TourSalesMode.FULL_BUS,
                per_seat_self_service_allowed=False,
                direct_customer_booking_blocked_or_deferred=True,
                operator_path_required=True,
                mini_app_catalog_reservation_allowed=False,
                catalog_charter_fixed_seats_count=None,
                catalog_actionability_state=CatalogActionabilityState.ASSISTED_ONLY,
                catalog_conversion_profile=CatalogConversionProfile.FULL_BUS_ASSISTED_CATALOG,
                reservation_cta_semantic_key="mini_app_cta_contact_operator",
                price_display_semantic_key="price_display_total_bus_package",
                capacity_display_semantic_key="capacity_display_fixed_vehicle_capacity",
                seat_selection_ux="none",
                bookable_as_full_bus_package=False,
                show_custom_trip_routing_hint=True,
            )
        raise ValueError(f"Unsupported tour sales mode: {sales_mode!r}")

    @classmethod
    def _apply_b10_3_catalog_semantics(
        cls,
        tour: CatalogTourPolicySource,
        policy: TourSalesModePolicyRead,
    ) -> TourSalesModePolicyRead:
        """B10.3: explicit catalog conversion labels so full_bus fixed offers do not read as per-seat pickers."""
        if tour.sales_mode is not TourSalesMode.FULL_BUS:
            return policy.model_copy(
                update={
                    "catalog_conversion_profile": CatalogConversionProfile.PER_SEAT_STANDARD,
                    "reservation_cta_semantic_key": "mini_app_cta_reserve_seats",
                    "price_display_semantic_key": "price_display_per_person",
                    "capacity_display_semantic_key": "capacity_display_live_seats_remaining",
                    "seat_selection_ux": "free_numeric",
                    "bookable_as_full_bus_package": False,
                    "show_custom_trip_routing_hint": False,
                }
            )
        st = policy.catalog_actionability_state
        if (
            st is CatalogActionabilityState.BOOKABLE
            and policy.mini_app_catalog_reservation_allowed
            and policy.catalog_charter_fixed_seats_count is not None
        ):
            return policy.model_copy(
                update={
                    "catalog_conversion_profile": CatalogConversionProfile.FULL_BUS_WHOLE_VEHICLE_BOOKABLE,
                    "reservation_cta_semantic_key": "mini_app_cta_reserve_full_bus",
                    "price_display_semantic_key": "price_display_total_bus_package",
                    "capacity_display_semantic_key": "capacity_display_whole_vehicle_capacity",
                    "seat_selection_ux": "fixed_charter",
                    "bookable_as_full_bus_package": True,
                    "show_custom_trip_routing_hint": True,
                }
            )
        if st is CatalogActionabilityState.ASSISTED_ONLY:
            return policy.model_copy(
                update={
                    "catalog_conversion_profile": CatalogConversionProfile.FULL_BUS_ASSISTED_CATALOG,
                    "reservation_cta_semantic_key": "mini_app_cta_contact_operator",
                    "price_display_semantic_key": "price_display_total_bus_package",
                    "capacity_display_semantic_key": "capacity_display_fixed_vehicle_capacity",
                    "seat_selection_ux": "none",
                    "bookable_as_full_bus_package": False,
                    "show_custom_trip_routing_hint": True,
                }
            )
        if st is CatalogActionabilityState.VIEW_ONLY:
            return policy.model_copy(
                update={
                    "catalog_conversion_profile": CatalogConversionProfile.FULL_BUS_VIEW_ONLY,
                    "reservation_cta_semantic_key": "mini_app_cta_view_only",
                    "price_display_semantic_key": "price_display_total_bus_package",
                    "capacity_display_semantic_key": "capacity_display_whole_vehicle_capacity",
                    "seat_selection_ux": "none",
                    "bookable_as_full_bus_package": False,
                    "show_custom_trip_routing_hint": True,
                }
            )
        if st is CatalogActionabilityState.BLOCKED:
            return policy.model_copy(
                update={
                    "catalog_conversion_profile": CatalogConversionProfile.FULL_BUS_BLOCKED,
                    "reservation_cta_semantic_key": "mini_app_cta_unavailable",
                    "price_display_semantic_key": "price_display_total_bus_package",
                    "capacity_display_semantic_key": "capacity_display_unavailable",
                    "seat_selection_ux": "none",
                    "bookable_as_full_bus_package": False,
                    "show_custom_trip_routing_hint": False,
                }
            )
        return policy

    @classmethod
    def policy_for_catalog_tour(cls, tour: CatalogTourPolicySource) -> TourSalesModePolicyRead:
        """Mini App catalog path: full-bus self-serve only when virgin capacity (5g.4a).

        Accepts ORM `Tour` or `TourRead` (private bot preparation uses the latter).
        """
        base = cls.policy_for_sales_mode(tour.sales_mode)
        if tour.sales_mode is not TourSalesMode.FULL_BUS:
            return cls._apply_b10_3_catalog_semantics(tour, base)
        actionability = cls._full_bus_catalog_actionability(
            seats_total=tour.seats_total,
            seats_available=tour.seats_available,
        )
        if actionability is not CatalogActionabilityState.BOOKABLE:
            merged = base.model_copy(update={"catalog_actionability_state": actionability})
            return cls._apply_b10_3_catalog_semantics(tour, merged)
        if tour.seats_total <= 0:
            merged = base.model_copy(
                update={"catalog_actionability_state": CatalogActionabilityState.BLOCKED}
            )
            return cls._apply_b10_3_catalog_semantics(tour, merged)
        merged = base.model_copy(
            update={
                "mini_app_catalog_reservation_allowed": True,
                "catalog_charter_fixed_seats_count": tour.seats_total,
                "catalog_actionability_state": actionability,
            }
        )
        return cls._apply_b10_3_catalog_semantics(tour, merged)

    @classmethod
    def policy_for_tour(cls, tour: Tour) -> TourSalesModePolicyRead:
        """Enum-only policy (RFQ bridge, legacy); does not apply virgin-capacity catalog rules."""
        return cls.policy_for_sales_mode(tour.sales_mode)
