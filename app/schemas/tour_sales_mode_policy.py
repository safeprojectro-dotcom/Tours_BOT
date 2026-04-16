"""Read model for tour commercial sales-mode policy (Phase 7.1 / Step 2).

Consumers should treat this as backend-owned interpretation of `Tour.sales_mode`.
Not wired into customer surfaces in Step 2.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TourSalesMode


class TourSalesModePolicyRead(BaseModel):
    """Normalized policy view derived only from `TourSalesMode` — never from seat counts."""

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
