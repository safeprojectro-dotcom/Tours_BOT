"""A4/A5: admin API DTOs for supplier clarification outbox."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead

CLARIFICATION_OUTBOX_WORKFLOW_STATUSES: frozenset[str] = frozenset(
    {"draft", "ready_for_review", "cancelled", "sent_externally_later"},
)


class SupplierClarificationOutboxItemRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    supplier_offer_id: int
    workflow_status: str
    draft_snapshot: dict
    created_by_telegram_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    last_reviewed_at: datetime | None = None
    last_reviewed_by_telegram_user_id: int | None = None
    review_note: str | None = None


class SupplierClarificationOutboxUpsertRead(BaseModel):
    """Result of POST outbox: either a new row or an existing active draft (replay)."""

    model_config = ConfigDict(extra="forbid")

    item: SupplierClarificationOutboxItemRead
    replayed_existing: bool


class SupplierClarificationOutboxCreateRequest(BaseModel):
    """Create a persisted outbox row from a draft snapshot (internal only; no send)."""

    model_config = ConfigDict(extra="forbid")

    draft: SupplierClarificationDraftRead = Field(
        description="Full clarification draft to store; supplier_offer_id must match an existing offer.",
    )
    created_by_telegram_user_id: int | None = Field(
        default=None,
        description="Optional Telegram user id of the admin who saved this row.",
    )


class SupplierClarificationOutboxStatusPatchRequest(BaseModel):
    """A5: transition workflow_status with optional review note (internal admin only)."""

    model_config = ConfigDict(extra="forbid")

    workflow_status: str = Field(
        description="Target status; must be a valid transition from the item's current status.",
    )
    review_note: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional note for this review action. Omit to leave review_note unchanged; send null to clear.",
    )
    reviewed_by_telegram_user_id: int | None = Field(
        default=None,
        description="Optional Telegram user id recorded as reviewer (last_reviewed_by_telegram_user_id).",
    )


__all__ = [
    "CLARIFICATION_OUTBOX_WORKFLOW_STATUSES",
    "SupplierClarificationOutboxCreateRequest",
    "SupplierClarificationOutboxItemRead",
    "SupplierClarificationOutboxStatusPatchRequest",
    "SupplierClarificationOutboxUpsertRead",
]
