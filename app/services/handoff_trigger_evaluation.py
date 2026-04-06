"""Handoff trigger categorization from free text — no persistence (Phase 7 / Step 2).

Keyword-style checks only (docs/GROUP_ASSISTANT_RULES.md §5). First matching category wins.
"""

from __future__ import annotations

import re

from app.schemas.group_assistant_triggers import HandoffCategory, HandoffTriggerResult

# (category, lowercase substring patterns). Order is priority (first match wins).
_HANDOFF_PATTERN_ROWS: tuple[tuple[HandoffCategory, frozenset[str]], ...] = (
    (
        HandoffCategory.EXPLICIT_HUMAN_REQUEST,
        frozenset(
            {
                "talk to a human",
                "speak to an operator",
                "speak to a human",
                "human operator",
                "real person",
                "live agent",
                "оператор",
                "живой человек",
                "соедини с оператором",
                "хочу поговорить с человеком",
            }
        ),
    ),
    (
        HandoffCategory.COMPLAINT,
        frozenset(
            {
                "complaint",
                "unacceptable",
                "terrible experience",
                "want a refund",
                "this is a scam",
                "жалоба",
                "верните деньги",
                "ужасный сервис",
            }
        ),
    ),
    (
        HandoffCategory.UNCLEAR_PAYMENT_ISSUE,
        frozenset(
            {
                "paid but",
                "payment failed",
                "i was charged but",
                "money was taken but",
                "shows unpaid",
                "still shows unpaid",
                "оплатил но",
                "не прошла оплата",
                "списали деньги но",
            }
        ),
    ),
    (
        HandoffCategory.DISCOUNT_REQUEST,
        frozenset(
            {
                "discount",
                "any promo",
                "promo code",
                "cheaper price",
                "скидк",
                "промокод",
                "дешевле",
            }
        ),
    ),
    (
        HandoffCategory.GROUP_BOOKING,
        frozenset(
            {
                "we are 10",
                "we are ten",
                "group of 12",
                "12 people",
                "large group",
                "нас 10",
                "нас десятеро",
                "группа на",
                "компания из",
            }
        ),
    ),
    (
        HandoffCategory.CUSTOM_PICKUP,
        frozenset(
            {
                "pick up from",
                "pickup from",
                "custom pickup",
                "different boarding",
                "another city pickup",
                "заберите из",
                "другой посадк",
                "можно ли забрать",
            }
        ),
    ),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def evaluate_handoff_triggers(
    message_text: str,
    *,
    low_confidence_signal: bool = False,
) -> HandoffTriggerResult:
    """
    Classify whether a handoff is suggested and with which category.

    ``low_confidence_signal`` must be supplied by upstream logic (e.g. assistant/tool
    layer) — this helper does not guess confidence from text alone.
    """
    if low_confidence_signal:
        return HandoffTriggerResult(True, HandoffCategory.LOW_CONFIDENCE_ANSWER)

    if not message_text or not message_text.strip():
        return HandoffTriggerResult(False, None)

    haystack = _normalize(message_text)

    for category, patterns in _HANDOFF_PATTERN_ROWS:
        for p in patterns:
            if p in haystack:
                return HandoffTriggerResult(True, category)

    return HandoffTriggerResult(False, None)
