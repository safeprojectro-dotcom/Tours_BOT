"""B16D1: read-only preview of a future ``prepare_conversion_chain`` action (no execution)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PrepareConversionChainPlanStepStatus = Literal["satisfied", "pending", "blocked", "not_applicable"]

PrepareConversionChainPlanSummaryStatus = Literal["ineligible", "blocked", "partial", "already_prepared"]

PrepareConversionChainExecutionOverallStatus = Literal[
    "succeeded",
    "partial_success",
    "failed",
    "blocked",
    "dry_run_preview",
]

PrepareConversionChainExecutionStepOutcomeStatus = Literal["succeeded", "failed", "skipped"]

_CONSTANT_PREPARE_CONVERSION_CHAIN_PATH_PATTERN: str = (
    "/admin/supplier-offers/{offer_id}/prepare-conversion-chain"
)


class PrepareConversionChainActionAffordanceRead(BaseModel):
    """B16D2D: read-only HTTP affordance for guarded prepare_conversion_chain (no execution from read paths)."""

    model_config = ConfigDict(extra="forbid")

    code: Literal["prepare_conversion_chain"] = "prepare_conversion_chain"
    method: Literal["POST"] = "POST"
    path: str = Field(description="Resolved POST path for this supplier_offer_id.")
    path_pattern: str = Field(
        default=_CONSTANT_PREPARE_CONVERSION_CHAIN_PATH_PATTERN,
        description="Stable template; substitute {offer_id}.",
    )
    requires_admin: Literal[True] = True
    requires_idempotency_key: Literal[True] = True
    requires_confirm_for_live: Literal[True] = True
    supports_dry_run: Literal[True] = True
    enabled: bool
    disabled_reason: str | None = None
    plan_path: str = Field(description="GET plan preview path for this offer (B16D1).")
    plan_status: PrepareConversionChainPlanSummaryStatus
    recommended_action: str | None = None
    blockers_count: int = Field(ge=0)


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
    prepare_conversion_chain_plan_path: str = Field(
        description="Admin HTTP path for this plan response (same route; stable navigation key for clients).",
    )
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
    prepare_conversion_chain_plan_status: PrepareConversionChainPlanSummaryStatus = Field(
        description="Lightweight chain readiness: ineligible, blocked, partial, or already_prepared (B16D1.2).",
    )
    prepare_conversion_chain_recommended_action: str | None = Field(
        default=None,
        description="Same derivation as recommended_next_action; stable key for list rows (B16D1.2).",
    )
    prepare_conversion_chain_blockers_count: int = Field(
        ge=0,
        description="Count of distinct eligibility + plan blocker strings (B16D1.2).",
    )
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


class AdminPrepareConversionChainExecutionStepResultRead(BaseModel):
    """Outcome of one chain step during guarded execution (live or replay summary)."""

    model_config = ConfigDict(extra="forbid")

    step_code: str
    step_order: int
    status: PrepareConversionChainExecutionStepOutcomeStatus
    error_code: str | None = None
    error_message: str | None = None
    detail: dict | None = None


class AdminPrepareConversionChainExecuteBody(BaseModel):
    """B16D2C: POST …/prepare-conversion-chain — thin HTTP binding for guarded execution."""

    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(..., description="Required non-blank idempotency key for this offer + action.")
    confirm: bool = Field(default=False, description="Must be true for live execution unless dry_run is true.")
    dry_run: bool = Field(default=False, description="Preview only: no audit rows or chain mutations.")

    @field_validator("idempotency_key")
    @classmethod
    def idempotency_key_strip_non_empty(cls, v: str) -> str:
        key = (v or "").strip()
        if not key:
            raise ValueError("idempotency_key must be non-blank")
        return key


class AdminPrepareConversionChainExecutionResultRead(BaseModel):
    """B16D2B/C: result of ``prepare_conversion_chain`` execution (service + HTTP)."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int
    dry_run: bool
    confirm: bool
    actor_surface: str
    idempotency_key: str
    requested_by: str | None = None
    attempt_id: int | None = None
    attempt_status: str | None = None
    overall_status: PrepareConversionChainExecutionOverallStatus
    blockers: list[str] = Field(default_factory=list)
    message: str | None = None
    tour_id: int | None = None
    execution_link_id: int | None = None
    prepare_conversion_chain_plan_status: PrepareConversionChainPlanSummaryStatus | None = None
    steps: list[AdminPrepareConversionChainExecutionStepResultRead] = Field(default_factory=list)
    generated_at: datetime


__all__ = [
    "AdminPrepareConversionChainExecuteBody",
    "AdminPrepareConversionChainExecutionResultRead",
    "AdminPrepareConversionChainExecutionStepResultRead",
    "AdminPrepareConversionChainPlanRead",
    "AdminPrepareConversionChainPlanStepRead",
    "PrepareConversionChainActionAffordanceRead",
    "PrepareConversionChainExecutionOverallStatus",
    "PrepareConversionChainExecutionStepOutcomeStatus",
    "PrepareConversionChainPlanStepStatus",
    "PrepareConversionChainPlanSummaryStatus",
]
