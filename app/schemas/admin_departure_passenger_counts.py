"""S1A: read-only Layer A passenger / order aggregates per departure (tour)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminDepartureSupplierAssociationRead(BaseModel):
    """Supplier / offer context linked to this tour via bridge or execution link (read-only)."""

    model_config = ConfigDict(extra="forbid")

    supplier_id: int
    supplier_code: str
    supplier_display_name: str
    supplier_offer_id: int
    supplier_offer_title: str
    association_kind: Literal["execution_link", "tour_bridge"]


class AdminDeparturePassengerCountsRead(BaseModel):
    """Aggregated operational counts for one Layer A tour departure (no manifest, no PII)."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int
    tour_code: str
    tour_title_default: str
    departure_datetime: datetime

    total_orders_count: int = Field(ge=0)
    active_orders_count: int = Field(ge=0)
    reserved_unpaid_orders_count: int = Field(ge=0)
    paid_confirmed_orders_count: int = Field(ge=0)
    cancelled_orders_count: int = Field(ge=0)
    other_active_orders_count: int = Field(ge=0)

    active_passenger_count: int = Field(ge=0)
    reserved_unpaid_passenger_count: int = Field(ge=0)
    paid_confirmed_passenger_count: int = Field(ge=0)
    cancelled_passenger_count: int = Field(ge=0)
    other_active_passenger_count: int = Field(ge=0)

    capacity: int = Field(ge=0)
    seats_available: int = Field(ge=0)
    remaining_capacity: int = Field(ge=0)
    load_percentage: float | None = Field(
        default=None,
        description="Share of seats not available for sale (inventory-based), 0–100 when capacity > 0.",
    )

    supplier_associations: list[AdminDepartureSupplierAssociationRead] = Field(default_factory=list)
    readiness_warnings: list[str] = Field(default_factory=list)

    computed_at_utc: datetime
    resolution_source: Literal["tour_scoped", "supplier_offer_execution_link", "supplier_offer_tour_bridge"] | None = (
        None
    )


class AdminDeparturePassengerCountsListRead(BaseModel):
    """Multiple departures for a supplier (distinct tours with any active link)."""

    model_config = ConfigDict(extra="forbid")

    supplier_id: int
    items: list[AdminDeparturePassengerCountsRead]
    readiness_warnings: list[str] = Field(default_factory=list)
    computed_at_utc: datetime
