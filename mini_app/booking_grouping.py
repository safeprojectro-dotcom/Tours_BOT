"""My bookings list UI grouping by existing MiniAppBookingFacadeState (no domain changes)."""

from __future__ import annotations

from app.schemas.mini_app import MiniAppBookingFacadeState, MiniAppBookingListItemRead


def partition_bookings_for_my_bookings_ui(
    items: list[MiniAppBookingListItemRead],
) -> tuple[
    list[MiniAppBookingListItemRead],
    list[MiniAppBookingListItemRead],
    list[MiniAppBookingListItemRead],
]:
    """
    Split API list into three buckets for display order: confirmed → active holds → history.

    Uses the same facade_state values as the backend/Mini App booking facade.
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
    return confirmed, active, history
