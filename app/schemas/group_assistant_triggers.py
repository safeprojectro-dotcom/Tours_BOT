"""Narrow typing for Phase 7 group + handoff trigger evaluation (helpers only).

Grounded in docs/GROUP_ASSISTANT_RULES.md — not an API surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GroupTriggerReason(StrEnum):
    """Why the bot may respond in a group (anti-spam: default is no reply)."""

    NONE = "none"
    MENTION = "mention"
    APPROVED_COMMAND = "approved_command"
    APPROVED_TRIGGER_PHRASE = "approved_trigger_phrase"


class HandoffCategory(StrEnum):
    """Documented handoff categories (GROUP_ASSISTANT_RULES.md §5)."""

    DISCOUNT_REQUEST = "discount_request"
    GROUP_BOOKING = "group_booking"
    CUSTOM_PICKUP = "custom_pickup"
    COMPLAINT = "complaint"
    UNCLEAR_PAYMENT_ISSUE = "unclear_payment_issue"
    EXPLICIT_HUMAN_REQUEST = "explicit_human_request"
    LOW_CONFIDENCE_ANSWER = "low_confidence_answer"


@dataclass(frozen=True, slots=True)
class GroupTriggerResult:
    should_respond_in_group: bool
    group_trigger_reason: GroupTriggerReason


@dataclass(frozen=True, slots=True)
class HandoffTriggerResult:
    handoff_required: bool
    handoff_category: HandoffCategory | None


@dataclass(frozen=True, slots=True)
class AssistantTriggerSnapshot:
    """Single message snapshot for future bot wiring (Phase 7+)."""

    should_respond_in_group: bool
    group_trigger_reason: GroupTriggerReason
    handoff_required: bool
    handoff_category: HandoffCategory | None
