"""Read-only queue indicators for admin handoff list/detail (Phase 6 / Step 18).

Secondary labels only; does not encode workflow permissions.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.handoff_entry import HandoffEntryService


def compute_group_followup_visibility(*, reason: str) -> tuple[bool, str | None]:
    """
    Phase 7 / Step 9 — derived read-only labels for the group → private follow-up chain.

    Returns (is_group_followup, source_label). Does not imply assignment or workflow state.
    """
    if reason == HandoffEntryService.REASON_GROUP_FOLLOWUP_START:
        return (
            True,
            "Group chat → private follow-up (/start grp_followup)",
        )
    return (False, None)


def compute_handoff_queue_fields(
    *,
    status: str,
    created_at: datetime,
    now: datetime | None = None,
) -> tuple[bool, bool, str]:
    """
    Returns (is_open, needs_attention, age_bucket).

    age_bucket: within_1h | within_24h | older — relative to `now` (UTC).
    needs_attention: true when status is open or in_review (operational follow-up may apply).
    """
    clock = now if now is not None else datetime.now(UTC)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    else:
        created_at = created_at.astimezone(UTC)
    clock = clock.astimezone(UTC) if clock.tzinfo else clock.replace(tzinfo=UTC)

    is_open = status == "open"
    needs_attention = status in ("open", "in_review")

    delta = clock - created_at
    secs = delta.total_seconds()
    if secs < 3600:
        age_bucket = "within_1h"
    elif secs < 86400:
        age_bucket = "within_24h"
    else:
        age_bucket = "older"

    return is_open, needs_attention, age_bucket
