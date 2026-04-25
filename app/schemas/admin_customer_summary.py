"""Admin/ops read-side customer label derived from persisted ``User`` fields only (Y35.5)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AdminCustomerSummary(BaseModel):
    """Operator-facing customer summary; does not replace ``customer_telegram_user_id`` on parent DTOs."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(
        default=None,
        description="Trimmed name from first_name/last_name when derivable; else None.",
    )
    username: str | None = Field(
        default=None,
        description="Telegram @handle without @ prefix, when present.",
    )
    summary_line: str = Field(
        ...,
        description="One line: 'customer: <name or tg:id> [@username if available]'.",
    )
