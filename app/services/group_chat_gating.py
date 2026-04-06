"""Phase 7 / Steps 3–5 — minimal group gating, handoff-aware replies, private CTA deep links.

Uses Step 2 ``evaluate_group_trigger`` and ``evaluate_handoff_triggers``; Step 5 appends a
``t.me`` deep link via ``group_private_cta``. No booking, payment, or handoff **persistence**.
Replies stay short and safe — ``docs/GROUP_ASSISTANT_RULES.md``.
"""

from __future__ import annotations

from app.schemas.group_assistant_triggers import HandoffCategory
from app.services.group_private_cta import build_group_private_cta_target, entry_mode_from_handoff
from app.services.group_trigger_evaluation import evaluate_group_trigger
from app.services.handoff_trigger_evaluation import evaluate_handoff_triggers

# Default when the group trigger fired but no handoff category matched (or generic info intent).
GROUP_TRIGGER_ACK_REPLY_TEXT = (
    "Thanks — for booking and details, please message me in private or use the Mini App."
)

# Category-specific short lines — no prices, dates, promises of assignment, or payment resolution.
_HANDOFF_CATEGORY_REPLY_TEXT: dict[HandoffCategory, str] = {
    HandoffCategory.DISCOUNT_REQUEST: (
        "Discounts and special pricing need a private follow-up — please message me directly."
    ),
    HandoffCategory.GROUP_BOOKING: (
        "For larger groups, please continue in private chat so we can check options safely."
    ),
    HandoffCategory.CUSTOM_PICKUP: (
        "Pickup or boarding changes need to be arranged in private — please message me."
    ),
    HandoffCategory.COMPLAINT: (
        "Sorry you’re having trouble — a human will need to review this. Please continue in private chat."
    ),
    HandoffCategory.UNCLEAR_PAYMENT_ISSUE: (
        "Payment questions are handled in private for security — please message me directly."
    ),
    HandoffCategory.EXPLICIT_HUMAN_REQUEST: (
        "For human support, please message me in private — we’ll continue there."
    ),
    HandoffCategory.LOW_CONFIDENCE_ANSWER: (
        "I can’t confirm details here — please continue in private or use the Mini App."
    ),
}


def resolve_group_trigger_ack_reply(message_text: str, *, bot_username: str | None) -> str | None:
    """
    If the **group** trigger matches, return one reply line: base text + ``t.me`` deep link CTA.

    Handoff-category-specific base text uses ``grp_followup`` payload; generic uses ``grp_private``.
    Otherwise ``None`` (stay silent). No handoff DB rows are created.

    When ``bot_username`` is unset, mention-based triggers cannot be evaluated safely;
    the bot stays silent in groups (configure ``TELEGRAM_BOT_USERNAME`` for full gating).
    """
    if not bot_username or not bot_username.strip():
        return None
    uname = bot_username.strip()
    group_result = evaluate_group_trigger(message_text, bot_username=uname)
    if not group_result.should_respond_in_group:
        return None

    handoff = evaluate_handoff_triggers(message_text, low_confidence_signal=False)
    if handoff.handoff_required and handoff.handoff_category is not None:
        base = _HANDOFF_CATEGORY_REPLY_TEXT.get(
            handoff.handoff_category,
            GROUP_TRIGGER_ACK_REPLY_TEXT,
        )
    else:
        base = GROUP_TRIGGER_ACK_REPLY_TEXT

    mode = entry_mode_from_handoff(handoff)
    cta = build_group_private_cta_target(bot_username=uname, entry_mode=mode)
    return f"{base} — {cta.deep_link}"
