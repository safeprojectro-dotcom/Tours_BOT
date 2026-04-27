"""Read model for tour commercial sales-mode policy (Phase 7.1 / Step 2).

Consumers should treat this as backend-owned interpretation of `Tour.sales_mode`.
Not wired into customer surfaces in Step 2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TourSalesMode


class CatalogActionabilityState(StrEnum):
    BOOKABLE = "bookable"
    ASSISTED_ONLY = "assisted_only"
    VIEW_ONLY = "view_only"
    BLOCKED = "blocked"


class CatalogConversionProfile(StrEnum):
    """B10.3: how catalog/detail/preparation should describe booking (per-seat vs whole-bus package vs assisted)."""

    PER_SEAT_STANDARD = "per_seat_standard"
    FULL_BUS_WHOLE_VEHICLE_BOOKABLE = "full_bus_whole_vehicle_bookable"
    FULL_BUS_ASSISTED_CATALOG = "full_bus_assisted_catalog"
    FULL_BUS_VIEW_ONLY = "full_bus_view_only"
    FULL_BUS_BLOCKED = "full_bus_blocked"


SeatSelectionUx = Literal["free_numeric", "fixed_charter", "none"]


class TourSalesModePolicyRead(BaseModel):
    """Policy view from `TourSalesMode`; optional tour-aware fields via `policy_for_catalog_tour`."""

    model_config = ConfigDict(frozen=True)

    effective_sales_mode: TourSalesMode = Field(
        description="Same as persisted `tours.sales_mode` for now; reserved if defaults normalize later.",
    )
    per_seat_self_service_allowed: bool = Field(
        description="Whether standard per-seat self-serve reservation/checkout is allowed.",
    )
    direct_customer_booking_blocked_or_deferred: bool = Field(
        description="True when direct customer booking must be deferred (e.g. full bus — operator path later).",
    )
    operator_path_required: bool = Field(
        description="True when an operator-assisted path is required for booking (full bus in current design).",
    )
    mini_app_catalog_reservation_allowed: bool = Field(
        description="Track 5g.4a: Mini App catalog may create a temporary reservation (per-seat, or full-bus virgin capacity).",
    )
    catalog_charter_fixed_seats_count: int | None = Field(
        default=None,
        description="When full-bus catalog self-serve is allowed, reservation must use exactly this seats_count (typically seats_total).",
    )
    catalog_actionability_state: CatalogActionabilityState = Field(
        description=(
            "Customer-facing actionability for current catalog context. "
            "`blocked` is fail-safe for invalid/inconsistent inventory snapshots."
        ),
    )
    # --- B10.3 Mini App copy/UX (stable i18n keys; Flet maps via `mini_app/ui_strings.shell`) ---
    catalog_conversion_profile: CatalogConversionProfile = Field(
        description="Distinguishes per-seat vs fixed whole-vehicle package vs assisted/view-only for full_bus.",
    )
    reservation_cta_semantic_key: str = Field(
        description="e.g. mini_app_cta_reserve_seats vs mini_app_cta_reserve_full_bus — must exist in `ui_strings`.",
    )
    price_display_semantic_key: str = Field(
        description="Whether catalog price is per person or total bus/package (label key, not a second price).",
    )
    capacity_display_semantic_key: str = Field(
        description="Whether capacity shows free pool vs whole-vehicle fixed capacity (key into `ui_strings`).",
    )
    seat_selection_ux: SeatSelectionUx = Field(
        description="free_numeric = per-seat count UI; fixed_charter = one fixed seats_count, no free picker; none = n/a.",
    )
    bookable_as_full_bus_package: bool = Field(
        default=False,
        description="True when the catalog self-serve path books the full vehicle/package at a fixed seat count.",
    )
    show_custom_trip_routing_hint: bool = Field(
        default=False,
        description="When True, show copy routing alternate routes/sizes to the custom-request flow.",
    )
