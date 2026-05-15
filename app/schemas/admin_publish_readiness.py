"""B15H: read-only publish readiness / suggest-only metadata (no Telegram I/O, no publish execution)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PublishReadinessSummaryStatus = Literal[
    "ready_to_suggest",
    "blocked",
    "not_applicable",
    "already_published",
    "needs_review",
]

PublishReadinessBadge = Literal[
    "ready_to_suggest",
    "blocked",
    "not_applicable",
    "already_published",
    "needs_review",
]

PublishReadinessGateResultStatus = Literal["passed", "failed", "warning", "not_applicable"]

PublishReadinessGateSeverity = Literal["blocker", "warning", "info"]


class AdminPublishReadinessGateRead(BaseModel):
    """Single evaluated gate for manual-publish suggestion (read-only)."""

    model_config = ConfigDict(extra="forbid")

    code: str
    label: str
    status: PublishReadinessGateResultStatus
    reason: str | None = None
    severity: PublishReadinessGateSeverity


class AdminPublishReadinessRead(BaseModel):
    """Suggest-only projection: whether to propose manual showcase publish, and why."""

    model_config = ConfigDict(extra="forbid")

    status: PublishReadinessSummaryStatus
    recommended_action: str
    gates_passed_count: int = Field(ge=0)
    gates_failed_count: int = Field(ge=0)
    gates_warning_count: int = Field(ge=0)
    gates: list[AdminPublishReadinessGateRead]
    can_suggest_manual_publish: bool
    can_auto_publish: Literal[False] = False
    auto_publish_mode: Literal["disabled"] = "disabled"
    publish_action_path: str | None = None
    prepare_conversion_chain_plan_path: str | None = None
    generated_at: datetime
    # B15I — compact UX layer (same read model; no extra I/O).
    summary: str = Field(description="One-line status for admin/OPS UI.")
    badge: PublishReadinessBadge = Field(description="Display badge key; mirrors status.")
    next_action_code: str | None = Field(
        default=None,
        description="Suggested next admin intent code (not an HTTP action execution).",
    )
    next_action_label: str | None = Field(
        default=None,
        description="Human-readable label for next_action_code.",
    )
    primary_blocker: str | None = Field(
        default=None,
        description="First failed blocker gate reason, if any.",
    )
    warning_summary: str | None = Field(
        default=None,
        description="Compact summary of warning gates (non-blocking).",
    )
    gate_summary: str = Field(description="Compact gate outcome counts for UI chrome.")


__all__ = [
    "AdminPublishReadinessGateRead",
    "AdminPublishReadinessRead",
    "PublishReadinessBadge",
    "PublishReadinessGateResultStatus",
    "PublishReadinessGateSeverity",
    "PublishReadinessSummaryStatus",
]
