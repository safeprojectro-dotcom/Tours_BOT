"""S1D-1: operational sales-push eligibility + plain-text preview (read-only; no Telegram channel publish)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import TourStatus
from app.repositories.tour import TourRepository
from app.schemas.admin_operational_sales_push_preview import AdminOperationalSalesPushPreviewRead
from app.services.admin_departure_passenger_counts_service import AdminDeparturePassengerCountsService


def _format_departure_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(microsecond=0).isoformat()


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class AdminOperationalSalesPushPreviewService:
    """S1D-1: system-confirmed counts via S1A; dual triggers — predeparture window and/or low seats."""

    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        departure_counts: AdminDeparturePassengerCountsService | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
        self._counts = departure_counts or AdminDeparturePassengerCountsService()

    def read_for_tour(
        self,
        session: Session,
        *,
        tour_id: int,
        now: datetime | None = None,
    ) -> AdminOperationalSalesPushPreviewRead | None:
        tour = self._tours.get(session, tour_id)
        if tour is None:
            return None

        current = _to_utc(now or datetime.now(UTC))
        counts = self._counts.read_for_tour(session, tour_id=tour_id, now=current)
        if counts is None:
            return None

        settings = get_settings()
        days_before = settings.predeparture_sales_push_days_before
        low_threshold = settings.low_availability_seats_threshold

        warnings = list(counts.readiness_warnings)
        trusted = "s1a_inventory_vs_active_order_seats_mismatch" not in warnings

        blocks: list[str] = []
        if tour.status != TourStatus.OPEN_FOR_SALE:
            blocks.append("s1d1_tour_not_open_for_sale")

        dep_utc = _to_utc(tour.departure_datetime)
        remaining = dep_utc - current

        if remaining <= timedelta(0):
            blocks.append("s1d1_departure_in_past")

        if tour.sales_deadline is not None and current >= _to_utc(tour.sales_deadline):
            blocks.append("s1d1_sales_deadline_passed")

        if counts.seats_available < 1:
            blocks.append("s1d1_no_seats_available")

        if not trusted:
            blocks.append("s1d1_inventory_unverified")

        base_ok = not blocks

        window = timedelta(days=days_before)
        pre_trigger = (
            base_ok and timedelta(0) < remaining <= window and counts.seats_available >= 1
        )
        low_trigger = (
            base_ok and 1 <= counts.seats_available <= low_threshold
        )

        eligible = base_ok and (pre_trigger or low_trigger)

        if base_ok and not (pre_trigger or low_trigger):
            blocks.append("s1d1_no_operational_sales_push_trigger")

        preview: str | None = None
        if eligible:
            parts: list[str] = ["Operational sales push preview:"]
            if pre_trigger:
                parts.append(
                    f"Predeparture urgency: departure within {days_before} day(s) "
                    f"(UTC {_format_departure_utc_iso(tour.departure_datetime)})."
                )
            if low_trigger:
                n = counts.seats_available
                seat_word = "seat" if n == 1 else "seats"
                parts.append(f"Low availability urgency: only {n} {seat_word} remain.")
            parts.append(f"Tour {tour.code} — {tour.title_default}.")
            parts.append("Inventory confirmed from Layer A; not published to Telegram.")
            preview = " ".join(parts)

        return AdminOperationalSalesPushPreviewRead(
            tour_id=tour.id,
            tour_code=tour.code,
            tour_title_default=tour.title_default,
            departure_datetime=tour.departure_datetime,
            seats_available=counts.seats_available,
            seats_inventory_trusted=trusted,
            predeparture_sales_push_days_before=days_before,
            low_availability_seats_threshold=low_threshold,
            predeparture_urgency_triggered=pre_trigger,
            low_availability_urgency_triggered=low_trigger,
            eligible_for_operational_sales_push_preview=eligible,
            eligibility_block_codes=blocks,
            preview_plain=preview,
            readiness_warnings=warnings,
            computed_at_utc=counts.computed_at_utc,
        )
