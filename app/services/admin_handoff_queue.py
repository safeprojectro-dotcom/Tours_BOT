"""Read-only queue indicators for admin handoff list/detail (Phase 6 / Step 18).

Secondary labels only; does not encode workflow permissions.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.handoff_entry import HandoffEntryService


def compute_full_bus_sales_assistance_visibility(
    *, reason: str
) -> tuple[bool, str | None, dict[str, str] | None]:
    """
    Phase 7.1 / Step 5 — distinguish full-bus commercial assistance from generic support handoffs.

    Returns (is_full_bus_sales_assistance, operator_label, parsed_key_values).
    """
    parsed = HandoffEntryService.parse_full_bus_sales_assistance(reason)
    if parsed is None:
        return False, None, None
    tour = parsed.get("tour") or "—"
    channel = parsed.get("channel") or "—"
    sm = parsed.get("sales_mode", "")
    label = f"Full-bus commercial assistance — tour {tour}, channel {channel}"
    if sm:
        label = f"{label}, sales_mode={sm}"
    return True, label, parsed


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


def compute_group_followup_assignment_visibility(
    *,
    reason: str,
    assigned_operator_id: int | None,
    status: str,
) -> tuple[bool, str | None]:
    """
    Phase 7 / Step 11 — read-only triage signal for assigned ``group_followup_start`` handoffs.

    Returns (is_assigned_group_followup, group_followup_work_label).

    ``is_assigned_group_followup`` is True only when reason is ``group_followup_start`` and an
    operator is assigned. ``group_followup_work_label`` is set only for that reason (including
    unassigned awaiting-assignment copy); for any other reason both are falsy / None.
    """
    is_gf, _ = compute_group_followup_visibility(reason=reason)
    if not is_gf:
        return False, None
    if assigned_operator_id is None:
        return False, "Queued with team — Awaiting assignment"
    if status == "closed":
        return True, "Assigned — follow-up closed"
    if status == "in_review":
        return True, "Assigned — in progress"
    return True, "Assigned — follow-up open"


def compute_group_followup_queue_state(
    *,
    reason: str,
    status: str,
    assigned_operator_id: int | None,
) -> str | None:
    """
    Phase 7 / Step 15 — single derived queue bucket for ``group_followup_start`` only.

    Returns ``awaiting_assignment`` | ``assigned_open`` | ``in_work`` | ``resolved``, or ``None``
    for other reasons or unexpected statuses. Read-only; does not encode permissions.
    """
    is_gf, _ = compute_group_followup_visibility(reason=reason)
    if not is_gf:
        return None
    if status == "closed":
        return "resolved"
    if status == "in_review":
        return "in_work"
    if status == "open":
        if assigned_operator_id is None:
            return "awaiting_assignment"
        return "assigned_open"
    return None


def compute_group_followup_resolution_label(*, reason: str, status: str) -> str | None:
    """
    Phase 7 / Steps 13–14 — read-only label when a ``group_followup_start`` handoff is **closed**.

    ``None`` for other reasons or non-terminal statuses. Does not record *how* the row was closed.
    """
    is_gf, _ = compute_group_followup_visibility(reason=reason)
    if not is_gf:
        return None
    if status == "closed":
        return "Group follow-up closed (resolved)"
    return None


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
