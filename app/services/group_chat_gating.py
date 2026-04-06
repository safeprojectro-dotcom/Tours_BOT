"""Phase 7 / Step 3 — minimal group chat reply gating (ack only).

Uses Step 2 ``evaluate_group_trigger``. No booking, payment, or handoff persistence.
See ``docs/GROUP_ASSISTANT_RULES.md`` — group replies stay short and CTA-oriented.
"""

from __future__ import annotations

from app.services.group_trigger_evaluation import evaluate_group_trigger

# Single safe placeholder — no prices, dates, or availability (GROUP_ASSISTANT_RULES §2–3).
GROUP_TRIGGER_ACK_REPLY_TEXT = (
    "Thanks — for booking and details, please message me in private or use the Mini App."
)


def resolve_group_trigger_ack_reply(message_text: str, *, bot_username: str | None) -> str | None:
    """
    If triggers match, return one short acknowledgment; otherwise ``None`` (stay silent).

    When ``bot_username`` is unset, mention-based triggers cannot be evaluated safely;
    the bot stays silent in groups (configure ``TELEGRAM_BOT_USERNAME`` for full gating).
    """
    if not bot_username or not bot_username.strip():
        return None
    result = evaluate_group_trigger(message_text, bot_username=bot_username.strip())
    if not result.should_respond_in_group:
        return None
    return GROUP_TRIGGER_ACK_REPLY_TEXT
