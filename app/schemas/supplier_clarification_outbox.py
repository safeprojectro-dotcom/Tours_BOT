"""A4: admin API DTOs for supplier clarification outbox."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead


class SupplierClarificationOutboxItemRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    supplier_offer_id: int
    workflow_status: str
    draft_snapshot: dict
    created_by_telegram_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


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


__all__ = [
    "SupplierClarificationOutboxCreateRequest",
    "SupplierClarificationOutboxItemRead",
    "SupplierClarificationOutboxUpsertRead",
]
