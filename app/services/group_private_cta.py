"""Phase 7 / Step 5 — build safe private-chat deep links for group CTAs.

Uses ``https://t.me/<bot_username>?start=<payload>`` (see ``docs/TELEGRAM_SETUP.md``).
Payloads are ASCII identifiers; private ``/start`` handling ignores unknown args and
falls through to the normal catalog flow (same as any non-``tour_`` deep link).

No booking, payment, handoff persistence, or Mini App changes.
"""

from __future__ import annotations

from app.schemas.group_assistant_triggers import HandoffTriggerResult
from app.schemas.group_private_cta import GroupPrivateCtaTarget, GroupPrivateEntryMode

# Telegram ``start`` parameter: [A-Za-z0-9_], length limits per Bot API.
_START_PAYLOAD_GENERIC = "grp_private"
_START_PAYLOAD_HUMAN = "grp_followup"


def entry_mode_from_handoff(handoff: HandoffTriggerResult) -> GroupPrivateEntryMode:
    """When a handoff category produced a category-specific group line, use human-followup mode."""
    if handoff.handoff_required and handoff.handoff_category is not None:
        return GroupPrivateEntryMode.HUMAN_FOLLOWUP
    return GroupPrivateEntryMode.GENERIC_PRIVATE


def build_group_private_cta_target(
    *,
    bot_username: str,
    entry_mode: GroupPrivateEntryMode,
) -> GroupPrivateCtaTarget:
    """
    Build a single consistent private deep link for group reply text.

    ``entry_mode`` selects payload only; private chat behavior is not branched in this step
    (unknown ``start`` args still resolve to the existing private entry flow).
    """
    uname = bot_username.strip().lstrip("@")
    if not uname:
        raise ValueError("bot_username is required for deep link construction")

    payload = _START_PAYLOAD_HUMAN if entry_mode == GroupPrivateEntryMode.HUMAN_FOLLOWUP else _START_PAYLOAD_GENERIC
    deep_link = f"https://t.me/{uname}?start={payload}"
    return GroupPrivateCtaTarget(
        entry_mode=entry_mode,
        start_payload=payload,
        deep_link=deep_link,
    )
