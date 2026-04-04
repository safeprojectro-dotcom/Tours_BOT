"""My bookings list UI grouping by existing MiniAppBookingFacadeState (no domain changes)."""

from __future__ import annotations

from app.schemas.mini_app import MiniAppBookingFacadeState, MiniAppBookingListItemRead

# Presentation-only: limit how many released/expired holds appear in History (archive policy Step 19).
HISTORY_SECTION_MAX_ITEMS = 15


def _sort_and_cap_history(
    history: list[MiniAppBookingListItemRead],
    *,
    max_items: int | None,
) -> tuple[list[MiniAppBookingListItemRead], int]:
    """Most recent `updated_at` first; cap list length. Returns (visible, omitted_count)."""
    if not history:
        return [], 0
    sorted_h = sorted(
        history,
        key=lambda it: it.summary.order.updated_at,
        reverse=True,
    )
    if max_items is None or len(sorted_h) <= max_items:
        return sorted_h, 0
    return sorted_h[:max_items], len(sorted_h) - max_items


def partition_bookings_for_my_bookings_ui(
    items: list[MiniAppBookingListItemRead],
    *,
    history_max_items: int | None = HISTORY_SECTION_MAX_ITEMS,
) -> tuple[
    list[MiniAppBookingListItemRead],
    list[MiniAppBookingListItemRead],
    list[MiniAppBookingListItemRead],
    int,
]:
    """
    Split API list into three buckets for display order: confirmed → active holds → history.

    Uses the same facade_state values as the backend/Mini App booking facade.

    History bucket is sorted by order ``updated_at`` (newest first) and truncated to
    ``history_max_items`` (default ``HISTORY_SECTION_MAX_ITEMS``). Omitted rows are not deleted;
    they remain available via booking detail if the user navigates by id. The fourth return
    value is how many history rows were hidden from this list.
    """
    confirmed: list[MiniAppBookingListItemRead] = []
    active: list[MiniAppBookingListItemRead] = []
    history: list[MiniAppBookingListItemRead] = []
    for item in items:
        fs = item.facade_state
        if fs in (MiniAppBookingFacadeState.CONFIRMED, MiniAppBookingFacadeState.IN_TRIP_PIPELINE):
            confirmed.append(item)
        elif fs == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION:
            active.append(item)
        else:
            history.append(item)
    visible, omitted = _sort_and_cap_history(history, max_items=history_max_items)
    return confirmed, active, visible, omitted
