"""Read-only admin API response models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import TourStatus
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind


class AdminTourListItem(BaseModel):
    id: int
    code: str
    title_default: str
    departure_datetime: datetime
    status: TourStatus
    seats_total: int
    seats_available: int
    currency: str
    base_price: Decimal


class AdminTourListRead(BaseModel):
    items: list[AdminTourListItem]
    total_returned: int


class AdminOrderListItem(BaseModel):
    id: int
    user_id: int
    tour_id: int
    tour_code: str
    seats_count: int
    total_amount: Decimal
    currency: str
    created_at: datetime
    lifecycle_kind: AdminOrderLifecycleKind
    lifecycle_summary: str


class AdminOrderListRead(BaseModel):
    items: list[AdminOrderListItem]
    total_returned: int


class AdminOverviewRead(BaseModel):
    app_env: str = Field(description="Configured APP_ENV for orientation (not a secret).")
    tours_total_approx: int
    orders_total_approx: int
    open_handoffs_count: int
    active_waitlist_entries_count: int
