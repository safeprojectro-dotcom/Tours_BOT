"""Read-only DTOs for internal ops queue visibility (handoffs vs waitlist)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OpsHandoffQueueItem(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    status: str
    priority: str
    reason: str
    user_id: int
    order_id: int | None = None
    assigned_operator_id: int | None = Field(
        default=None,
        description="Null when no operator assignment workflow has run yet.",
    )
    order_tour_id: int | None = None
    order_tour_code: str | None = None
    order_tour_title_default: str | None = None


class OpsHandoffQueueRead(BaseModel):
    items: list[OpsHandoffQueueItem]
    ordering: str = Field(
        default="created_at_asc",
        description="Oldest open handoffs first (FIFO-style triage).",
    )


class OpsWaitlistQueueItem(BaseModel):
    id: int
    created_at: datetime
    status: str
    user_id: int
    tour_id: int
    seats_count: int
    tour_code: str | None = None
    tour_title_default: str | None = None


class OpsWaitlistQueueRead(BaseModel):
    items: list[OpsWaitlistQueueItem]
    ordering: str = Field(
        default="created_at_asc",
        description="Oldest active waitlist entries first.",
    )


class OpsHandoffClaimRequest(BaseModel):
    """Optional operator user id (must exist in `users`)."""

    operator_id: int | None = Field(default=None, description="Assign this internal user as operator when set.")


class OpsHandoffCloseRequest(BaseModel):
    """Optional operator id recorded when closing (e.g. who resolved the case)."""

    operator_id: int | None = Field(default=None, description="Set `assigned_operator_id` when closing if provided.")


class OpsHandoffActionRead(BaseModel):
    id: int
    status: str
    assigned_operator_id: int | None = None
    updated_at: datetime


class OpsWaitlistActionRead(BaseModel):
    """Waitlist row has no `updated_at`; `waitlist` is interest only, not a booking."""

    id: int
    status: str
    user_id: int
    tour_id: int
    seats_count: int
    created_at: datetime
