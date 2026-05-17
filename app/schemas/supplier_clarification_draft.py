"""A3: read-only clarification drafts — supplier-safe asks vs internal admin tasks (nothing is sent)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SupplierClarificationDraftRead(BaseModel):
    """Split-view drafts derived from intake validation; admin-only display until a future send flow exists."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int = Field(description="Supplier offer these drafts refer to.")
    draft_version: Literal["a3_v1"] = "a3_v1"
    projection_note: str = Field(
        default="Ciorne numai pentru echipa internă; nu s-a trimis nimic către furnizor.",
        description="Plain-language reminder (RO) that these lines are not auto-sent.",
    )
    supplier_facing_asks: list[str] = Field(
        default_factory=list,
        description="Short, polite Romanian lines suitable for eventual supplier messages (no platform jargon).",
    )
    internal_admin_tasks: list[str] = Field(
        default_factory=list,
        description="Technical / operational follow-ups for admins only (may include English diagnostics).",
    )


__all__ = ["SupplierClarificationDraftRead"]
