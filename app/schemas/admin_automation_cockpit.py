"""A1-Block 1/2: read-only Admin Automation Cockpit response DTOs (no mutations / publish / Telegram I/O)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

AutomationCockpitQueueCode = Literal[
    "supplier_intake",
    "missing_info",
    "offer_readiness",
    "risk_conflict",
    "marketing_review",
    "publishing_queue",
    "catalog_conversion",
]

AUTOMATION_COCKPIT_QUEUE_CODES: Final[tuple[str, ...]] = (
    "supplier_intake",
    "missing_info",
    "offer_readiness",
    "risk_conflict",
    "marketing_review",
    "publishing_queue",
    "catalog_conversion",
)
AUTOMATION_COCKPIT_QUEUE_CODES_SET: Final[frozenset[str]] = frozenset(AUTOMATION_COCKPIT_QUEUE_CODES)

CockpitNextBestActionKind = Literal[
    "safe_read",
    "safe_generate_draft",
    "supplier_clarification",
    "guarded_internal_action",
    "guarded_dry_run",
    "guarded_live_action",
    "public_side_effect",
    "future_disabled",
    "forbidden",
]


def parse_include_queues_query(raw: str | None) -> frozenset[str] | None:
    """Comma-separated queue_code filter; None/empty => all queues. Raises ValueError on unknown tokens."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None
    invalid = sorted({p for p in parts if p not in AUTOMATION_COCKPIT_QUEUE_CODES_SET})
    if invalid:
        raise ValueError(
            f"Unknown include_queues {invalid!r}; allowed: {list(AUTOMATION_COCKPIT_QUEUE_CODES)}",
        )
    return frozenset(parts)


COCKPIT_FACT_LOCK_NOTE: Final[str] = (
    "Supplier/catalog commercial facts are read-only in this cockpit view. "
    "Use marketing review flows for packaging and copy only; do not change price, route, inclusions, discounts, "
    "or capacity from this surface. Factual corrections require supplier clarification or governed source updates."
)


class AdminAutomationCockpitCommercialContextRead(BaseModel):
    """Safe read-only commercial/marketing signals (no PII/secrets). A1-Block 2."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int | None = None
    tour_id: int | None = None
    tour_code: str | None = None
    already_published: bool | None = None
    has_tour_bridge: bool | None = None
    has_catalog_visible_tour: bool | None = None
    has_active_execution_link: bool | None = None
    preview_status: str | None = None
    payload_status: str | None = None
    template_family: str | None = None
    selected_template_id: str | None = None
    publish_status: str | None = None
    prepare_chain_status: str | None = None
    fact_lock_note: str = Field(
        default=COCKPIT_FACT_LOCK_NOTE,
        description="Fact-lock copy: marketing vs supplier truth boundaries.",
    )


class AdminAutomationCockpitCardSafetyFlagsRead(BaseModel):
    """Explicit read-only / no side-effect boundaries for a cockpit card (documentation flags)."""

    model_config = ConfigDict(extra="forbid")

    read_only: Literal[True] = True
    no_telegram_io: Literal[True] = True
    no_publish_attempt: Literal[True] = True
    no_scheduler: Literal[True] = True
    no_auto_publish: Literal[True] = True
    no_supplier_notification_send: Literal[True] = True
    no_qr_token: Literal[True] = True
    no_layer_a_mutation: Literal[True] = True
    no_b11_change: Literal[True] = True


class AdminAutomationCockpitSafetySummaryRead(BaseModel):
    """Response-level safety envelope for the cockpit snapshot."""

    model_config = ConfigDict(extra="forbid")

    read_only: Literal[True] = True
    no_telegram_io: Literal[True] = True
    no_publish_attempt: Literal[True] = True
    no_scheduler: Literal[True] = True
    no_auto_publish: Literal[True] = True
    no_supplier_notification_send: Literal[True] = True
    no_qr_token: Literal[True] = True
    no_layer_a_mutation: Literal[True] = True
    no_b11_change: Literal[True] = True
    note: str = Field(
        description="Confirms this GET assembles read-only projections only (no sends, no jobs, no mutations).",
    )


class AdminAutomationCockpitCardRead(BaseModel):
    """Generic cockpit queue card aligned with A1 (read-only foundation)."""

    model_config = ConfigDict(extra="forbid")

    card_id: str
    source_type: str
    source_id: int
    title: str
    subtitle: str | None = None
    status: str
    status_label: str
    status_tone: str
    priority: int = Field(ge=0, le=9, description="Lower is more urgent within snapshot ordering heuristics.")
    next_best_action_code: str
    next_best_action_label: str
    next_best_action_kind: CockpitNextBestActionKind
    next_best_action_enabled: bool
    blocker_summary: str | None = None
    warning_summary: str | None = None
    risk_summary: str | None = None
    owner_role: str | None = None
    last_updated_at: datetime | None = None
    due_at: datetime | None = None
    departure_at: datetime | None = None
    safety_flags: AdminAutomationCockpitCardSafetyFlagsRead = Field(
        default_factory=AdminAutomationCockpitCardSafetyFlagsRead,
    )
    source_paths: dict[str, str] = Field(default_factory=dict)
    commercial_context: AdminAutomationCockpitCommercialContextRead | None = Field(
        default=None,
        description="A1-Block 2: commercial/marketing/conversion context; optional on operational-queue cards.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


AutomationCockpitQueueStatus = Literal["active", "idle", "degraded"]
AutomationCockpitQueueTone = Literal["neutral", "info", "success", "warning", "danger"]


class AdminAutomationCockpitQueueRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queue_code: AutomationCockpitQueueCode
    queue_label: str
    queue_status: AutomationCockpitQueueStatus
    queue_tone: AutomationCockpitQueueTone
    total_count: int = Field(ge=0)
    cards: list[AdminAutomationCockpitCardRead] = Field(default_factory=list)
    description: str
    next_refresh_hint: str


class AdminAutomationCockpitSummaryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cards: int = Field(ge=0)
    queue_counts: dict[str, int]
    urgent_count: int = Field(ge=0)
    needs_attention_count: int = Field(ge=0)
    ready_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    future_disabled_count: int = Field(ge=0)


class AdminAutomationCockpitQueryRead(BaseModel):
    """Echo of cockpit query knobs (support / debugging)."""

    model_config = ConfigDict(extra="forbid")

    limit_per_queue: int
    include_queues: list[str] | None = None
    publishing_console_limit: int
    publishing_console_kind: str | None = None


class AdminAutomationCockpitRead(BaseModel):
    """GET /admin/automation-cockpit — read-only cockpit snapshot."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: AdminAutomationCockpitSummaryRead
    queues: list[AdminAutomationCockpitQueueRead]
    safety_summary: AdminAutomationCockpitSafetySummaryRead
    source_note: str = Field(
        description="How this snapshot was assembled; counts may be bounded by publishing-console fetch limits.",
    )
    query: AdminAutomationCockpitQueryRead | None = None


__all__ = [
    "AUTOMATION_COCKPIT_QUEUE_CODES",
    "AUTOMATION_COCKPIT_QUEUE_CODES_SET",
    "AdminAutomationCockpitCommercialContextRead",
    "AutomationCockpitQueueTone",
    "COCKPIT_FACT_LOCK_NOTE",
    "AdminAutomationCockpitCardRead",
    "AdminAutomationCockpitCardSafetyFlagsRead",
    "AdminAutomationCockpitQueueRead",
    "AdminAutomationCockpitRead",
    "AdminAutomationCockpitQueryRead",
    "AdminAutomationCockpitSafetySummaryRead",
    "AdminAutomationCockpitSummaryRead",
    "AutomationCockpitQueueCode",
    "CockpitNextBestActionKind",
    "parse_include_queues_query",
]
