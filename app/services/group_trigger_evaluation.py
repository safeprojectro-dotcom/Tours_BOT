"""Narrow group trigger evaluation — no Telegram runtime (Phase 7 / Step 2).

Rules: docs/GROUP_ASSISTANT_RULES.md §1; commands aligned with docs/TELEGRAM_SETUP.md §3.
This is substring / token checks only — not a general NLP router.
"""

from __future__ import annotations

import re

from app.schemas.group_assistant_triggers import GroupTriggerReason, GroupTriggerResult

# Default commands (lowercase, /cmd without @bot) — TELEGRAM_SETUP recommended MVP set.
DEFAULT_APPROVED_GROUP_COMMANDS: frozenset[str] = frozenset(
    {
        "/start",
        "/tours",
        "/bookings",
        "/language",
        "/help",
        "/contact",
    }
)

# Narrow curated substrings (lowercase) — sales/info intent per GROUP_ASSISTANT_RULES §1.3.
DEFAULT_APPROVED_TRIGGER_PHRASES: frozenset[str] = frozenset(
    {
        "how much",
        "how many seats",
        "any seats",
        "still available",
        "book",
        "booking",
        "price",
        "when do you leave",
        "сколько стоит",
        "есть места",
        "забронировать",
        "цена",
        "во сколько выезд",
    }
)


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _first_command_token(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None
    first = stripped.split()[0]
    if not first.startswith("/"):
        return None
    if "@" in first:
        first = first.split("@", 1)[0]
    return first.lower()


def evaluate_group_trigger(
    message_text: str,
    *,
    bot_username: str,
    approved_commands: frozenset[str] | None = None,
    approved_trigger_phrases: frozenset[str] | None = None,
) -> GroupTriggerResult:
    """
    Decide whether the bot should consider responding in a group (trigger-gated).

    - Mention: ``@bot_username`` substring (case-insensitive).
    - Approved command: first token matches configured slash commands.
    - Approved trigger phrase: message contains one of the configured substrings.
    """
    commands = approved_commands if approved_commands is not None else DEFAULT_APPROVED_GROUP_COMMANDS
    phrases = approved_trigger_phrases if approved_trigger_phrases is not None else DEFAULT_APPROVED_TRIGGER_PHRASES

    if not message_text or not message_text.strip():
        return GroupTriggerResult(False, GroupTriggerReason.NONE)

    # Commands first so `/tours@BotName` counts as an approved command, not a mention substring.
    token = _first_command_token(message_text)
    if token is not None and token in commands:
        return GroupTriggerResult(True, GroupTriggerReason.APPROVED_COMMAND)

    uname = bot_username.strip().lstrip("@").lower()
    lowered = message_text.lower()
    if uname and f"@{uname}" in lowered:
        return GroupTriggerResult(True, GroupTriggerReason.MENTION)

    compact = _normalize_ws(message_text)
    for phrase in phrases:
        if phrase in compact:
            return GroupTriggerResult(True, GroupTriggerReason.APPROVED_TRIGGER_PHRASE)

    return GroupTriggerResult(False, GroupTriggerReason.NONE)
