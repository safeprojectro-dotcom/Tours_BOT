"""U1: safe Mode 2 → Mode 3 context for custom-request prefill (UX only; no booking side effects)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.schemas.mini_app import MiniAppReservationPreparationRead, MiniAppTourDetailRead


@dataclass(frozen=True)
class CustomRequestPrefill:
    """Hints copied from a catalog tour the user was viewing — still a new custom request."""

    tour_code: str
    tour_title: str
    departure_date_iso: str
    return_date_iso: str | None
    source: str  # "catalog_detail" | "catalog_prepare"


def _date_iso(dt: datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC)
    return dt.date().isoformat()


def prefill_from_tour_detail(detail: MiniAppTourDetailRead) -> CustomRequestPrefill:
    tour = detail.tour
    title = (detail.localized_content.title or "").strip() or tour.code
    ret = _date_iso(tour.return_datetime)
    dep = _date_iso(tour.departure_datetime)
    return CustomRequestPrefill(
        tour_code=tour.code,
        tour_title=title,
        departure_date_iso=dep,
        return_date_iso=ret if ret != dep else None,
        source="catalog_detail",
    )


def prefill_from_reservation_preparation(prep: MiniAppReservationPreparationRead) -> CustomRequestPrefill:
    tour = prep.tour
    title = (tour.localized_content.title or "").strip() or tour.code
    ret = _date_iso(tour.return_datetime)
    dep = _date_iso(tour.departure_datetime)
    return CustomRequestPrefill(
        tour_code=tour.code,
        tour_title=title,
        departure_date_iso=dep,
        return_date_iso=ret if ret != dep else None,
        source="catalog_prepare",
    )
