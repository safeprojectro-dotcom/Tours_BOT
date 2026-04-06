"""Phase 7 / Step 5 — structured private CTA targets for group replies (no API surface)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GroupPrivateEntryMode(StrEnum):
    """How the user is invited into private chat from a group CTA."""

    GENERIC_PRIVATE = "generic_private"
    HUMAN_FOLLOWUP = "human_followup"


@dataclass(frozen=True, slots=True)
class GroupPrivateCtaTarget:
    """Machine-friendly private entry descriptor (Telegram deep link)."""

    entry_mode: GroupPrivateEntryMode
    start_payload: str
    deep_link: str
