"""Presentation-only copy helpers (no domain rules)."""

from __future__ import annotations

from app.schemas.mini_app import MiniAppBookingFacadeState
from mini_app.ui_strings import shell


def booking_detail_context_note(language_code: str | None, facade_state: MiniAppBookingFacadeState) -> str:
    """Short paragraph clarifying what the user can do next for this booking state."""
    lg = language_code
    if facade_state == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION:
        return shell(lg, "booking_detail_note_active_hold")
    if facade_state in (MiniAppBookingFacadeState.CONFIRMED, MiniAppBookingFacadeState.IN_TRIP_PIPELINE):
        return shell(lg, "booking_detail_note_confirmed")
    return shell(lg, "booking_detail_note_released")
