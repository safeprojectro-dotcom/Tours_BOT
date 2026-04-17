"""Customer-facing catalog visibility (read-side): time windows only — admin unchanged."""

from __future__ import annotations

from datetime import UTC, datetime


def tour_is_customer_catalog_visible(
    *,
    departure_datetime: datetime,
    sales_deadline: datetime | None,
    now: datetime | None = None,
) -> bool:
    """True when a tour may appear on customer catalog/detail/preparation/waitlist entry paths.

    Hidden when departure is in the past, or when ``sales_deadline`` is set and has passed.
    Does not replace ``TourStatus`` checks — callers still enforce ``open_for_sale`` (etc.).
    """
    ref = (now or datetime.now(UTC)).astimezone(UTC)
    dep = departure_datetime if departure_datetime.tzinfo else departure_datetime.replace(tzinfo=UTC)
    dep = dep.astimezone(UTC)
    if dep < ref:
        return False
    if sales_deadline is not None:
        sd = sales_deadline if sales_deadline.tzinfo else sales_deadline.replace(tzinfo=UTC)
        sd = sd.astimezone(UTC)
        if sd < ref:
            return False
    return True
