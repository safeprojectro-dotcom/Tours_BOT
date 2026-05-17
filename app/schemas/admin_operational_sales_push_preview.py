"""S1D-1: read-only operational sales-push preview for admin (no channel publish)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminOperationalSalesPushPreviewRead(BaseModel):
    """Eligibility + plain preview from Layer A inventory — predeparture and/or low-availability urgency."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int
    tour_code: str
    tour_title_default: str
    departure_datetime: datetime

    seats_available: int = Field(ge=0)
    seats_inventory_trusted: bool = Field(
        description="False when S1A inventory vs orders mismatch is present — do not claim scarcity.",
    )

    predeparture_sales_push_days_before: int = Field(
        ge=1,
        description="Configured window: urgency when departure is within this many days (strictly future).",
    )
    low_availability_seats_threshold: int = Field(
        ge=1,
        description="Configured threshold N: low-availability trigger when 1..N seats remain.",
    )

    predeparture_urgency_triggered: bool = Field(
        description="True when departure is within predeparture_sales_push_days_before and seats remain.",
    )
    low_availability_urgency_triggered: bool = Field(
        description="True when seats_available is between 1 and low_availability_seats_threshold inclusive.",
    )

    eligible_for_operational_sales_push_preview: bool = Field(
        description="True when base gates pass and at least one urgency trigger is active.",
    )
    eligibility_block_codes: list[str] = Field(
        default_factory=list,
        description="Stable codes when not eligible; empty when eligible.",
    )

    preview_plain: str | None = Field(
        default=None,
        description="Suggested ops copy when eligible; no Telegram send implied.",
    )

    readiness_warnings: list[str] = Field(default_factory=list)
    computed_at_utc: datetime
