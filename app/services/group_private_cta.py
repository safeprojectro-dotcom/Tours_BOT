"""Phase 7 / Steps 5–6 — group CTA deep links + private ``/start`` payload matching.

Uses ``https://t.me/<bot_username>?start=<payload>`` (see ``docs/TELEGRAM_SETUP.md``).
Payloads are ASCII identifiers. Step **6** branches private ``/start`` only for
``START_PAYLOAD_GRP_*``; other args keep existing behavior (e.g. ``tour_*``).

No booking, payment, handoff persistence, or Mini App changes.
"""

from __future__ import annotations

from app.schemas.group_assistant_triggers import HandoffTriggerResult
from app.schemas.group_private_cta import GroupPrivateCtaTarget, GroupPrivateEntryMode

# Telegram ``start`` parameter: [A-Za-z0-9_], length limits per Bot API.
# Must stay aligned with group reply deep links (Phase 7 / Step 5).
START_PAYLOAD_GRP_PRIVATE = "grp_private"
START_PAYLOAD_GRP_FOLLOWUP = "grp_followup"


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

    payload = (
        START_PAYLOAD_GRP_FOLLOWUP
        if entry_mode == GroupPrivateEntryMode.HUMAN_FOLLOWUP
        else START_PAYLOAD_GRP_PRIVATE
    )
    deep_link = f"https://t.me/{uname}?start={payload}"
    return GroupPrivateCtaTarget(
        entry_mode=entry_mode,
        start_payload=payload,
        deep_link=deep_link,
    )


def match_group_cta_start_payload(start_arg: str | None) -> str | None:
    """
    If ``start_arg`` is a Phase 7 group CTA payload, return it; otherwise ``None``.

    Does **not** match ``tour_*`` or other payloads — private ``/start`` uses this
    before tour resolution (Phase 7 / Step 6).
    """
    if start_arg is None:
        return None
    s = start_arg.strip()
    if s == START_PAYLOAD_GRP_PRIVATE:
        return START_PAYLOAD_GRP_PRIVATE
    if s == START_PAYLOAD_GRP_FOLLOWUP:
        return START_PAYLOAD_GRP_FOLLOWUP
    return None
