"""Thin composition of group + handoff trigger helpers (Phase 7 / Step 2).

Safe to call from future bot handlers; does not touch repositories or persistence.
"""

from __future__ import annotations

from app.schemas.group_assistant_triggers import AssistantTriggerSnapshot
from app.services.group_trigger_evaluation import evaluate_group_trigger
from app.services.handoff_trigger_evaluation import evaluate_handoff_triggers


def evaluate_assistant_trigger_snapshot(
    message_text: str,
    *,
    bot_username: str,
    low_confidence_signal: bool = False,
    approved_commands: frozenset[str] | None = None,
    approved_trigger_phrases: frozenset[str] | None = None,
) -> AssistantTriggerSnapshot:
    """Return a single structured snapshot for a user message (e.g. group or private)."""
    group = evaluate_group_trigger(
        message_text,
        bot_username=bot_username,
        approved_commands=approved_commands,
        approved_trigger_phrases=approved_trigger_phrases,
    )
    handoff = evaluate_handoff_triggers(message_text, low_confidence_signal=low_confidence_signal)
    return AssistantTriggerSnapshot(
        should_respond_in_group=group.should_respond_in_group,
        group_trigger_reason=group.group_trigger_reason,
        handoff_required=handoff.handoff_required,
        handoff_category=handoff.handoff_category,
    )
