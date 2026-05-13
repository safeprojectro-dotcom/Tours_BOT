"""B16D1: read-only preview of a future ``prepare_conversion_chain`` action (no execution)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PrepareConversionChainPlanStepStatus = Literal["satisfied", "pending", "blocked", "not_applicable"]


class AdminPrepareConversionChainPlanStepRead(BaseModel):
    """Single ordered step in the internal preparation chain (bridge → catalog → execution link)."""

    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    summary: str
    order_index: int = Field(ge=1, le=3)
    status: PrepareConversionChainPlanStepStatus
    already_satisfied: bool
    would_execute: bool
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AdminPrepareConversionChainPlanRead(BaseModel):
    """GET …/prepare-conversion-chain/plan — derived read-only; does not mutate."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int
    prepare_conversion_chain_eligible: bool = Field(
        description="True when packaging/moderation gates would allow starting the chain (preview only).",
    )
    eligibility_blockers: list[str] = Field(default_factory=list)
    steps: list[AdminPrepareConversionChainPlanStepRead]
    plan_blockers: list[str] = Field(
        default_factory=list,
        description="Consolidated blockers for executing the chain now (from steps + gates).",
    )
    warnings: list[str] = Field(default_factory=list)
    will_not_do: list[str] = Field(
        default_factory=list,
        description="Explicit non-goals for the future mutation action (this endpoint performs none of these).",
    )
    recommended_next_action: str | None = None
    review_package_path: str
    conversion_closure_next_missing_step: str | None = Field(
        default=None,
        description="Echo of review-package conversion_closure.next_missing_step (full funnel).",
    )
    generated_at: datetime
    audit_hint: str = Field(
        default=(
            "Read-only prepare-conversion-chain plan preview; no bridge, catalog, execution link, "
            "or Telegram I/O is performed from this endpoint."
        ),
    )


__all__ = [
    "AdminPrepareConversionChainPlanRead",
    "AdminPrepareConversionChainPlanStepRead",
    "PrepareConversionChainPlanStepStatus",
]
