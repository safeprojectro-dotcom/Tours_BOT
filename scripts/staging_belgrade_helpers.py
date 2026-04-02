"""
Shared staging helpers for TEST_BELGRADE_001 (reset + seed).

Keeps delete order and rolling calendar window in one place so smoke stays reproducible.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.models.notification_outbox import NotificationOutbox
from app.models.order import Order
from app.models.payment import Payment
from app.models.tour import BoardingPoint, Tour
from app.models.waitlist import WaitlistEntry

TEST_CODE = "TEST_BELGRADE_001"


def compute_staging_datetimes(*, now: datetime | None = None) -> tuple[datetime, datetime, datetime]:
    """
    Rolling future window: departure ~14 days ahead (08:44 UTC), return +12h,
    sales_deadline day before departure (or nudged forward if we are too close to calendar edge).
    """
    clock = now or datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    else:
        clock = clock.astimezone(UTC)

    dep_date = (clock + timedelta(days=14)).date()
    departure = datetime.combine(dep_date, time(8, 44, 32), tzinfo=UTC)
    if departure <= clock:
        departure = (clock + timedelta(days=2)).replace(hour=8, minute=44, second=32, microsecond=0)
        if departure.tzinfo is None:
            departure = departure.replace(tzinfo=UTC)

    return_dt = departure + timedelta(hours=12)

    sales_deadline = (departure - timedelta(days=1)).replace(hour=8, minute=44, second=32, microsecond=0)
    if sales_deadline <= clock:
        sales_deadline = clock + timedelta(hours=2)
    if sales_deadline >= departure:
        sales_deadline = departure - timedelta(hours=1)
    if sales_deadline <= clock:
        sales_deadline = clock + timedelta(minutes=30)

    return departure, return_dt, sales_deadline


def delete_orders_and_related_for_tour(session: Session, tour_id: int) -> int:
    """Delete payments + outbox + orders + waitlist for this tour. Returns deleted order count."""
    order_ids = list(session.scalars(select(Order.id).where(Order.tour_id == tour_id)).all())
    if order_ids:
        session.execute(delete(Payment).where(Payment.order_id.in_(order_ids)))
        session.execute(delete(NotificationOutbox).where(NotificationOutbox.order_id.in_(order_ids)))
    session.execute(delete(Order).where(Order.tour_id == tour_id))
    session.execute(delete(WaitlistEntry).where(WaitlistEntry.tour_id == tour_id))
    session.flush()
    return len(order_ids)


def apply_smoke_ready_tour_fields(tour: Tour, *, now: datetime | None = None) -> None:
    """Restore seats/status and refresh schedule so prepare + reservation expiry stay valid."""
    departure, return_dt, sales_deadline = compute_staging_datetimes(now=now)
    tour.departure_datetime = departure
    tour.return_datetime = return_dt
    tour.sales_deadline = sales_deadline
    tour.seats_available = tour.seats_total
    tour.status = TourStatus.OPEN_FOR_SALE


def count_orders_for_tour(session: Session, tour_id: int) -> int:
    return int(
        session.scalar(select(func.count()).select_from(Order).where(Order.tour_id == tour_id)) or 0
    )


def count_boarding_points(session: Session, tour_id: int) -> int:
    return int(
        session.scalar(select(func.count()).select_from(BoardingPoint).where(BoardingPoint.tour_id == tour_id))
        or 0
    )


def smoke_readiness_lines(session: Session, tour: Tour, *, now: datetime | None = None) -> list[str]:
    """Human-readable checks after reset/seed (stdout)."""
    clock = now or datetime.now(UTC)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=UTC)
    else:
        clock = clock.astimezone(UTC)

    n_orders = count_orders_for_tour(session, tour.id)
    n_bp = count_boarding_points(session, tour.id)
    lines = [
        "--- Smoke readiness (TEST_BELGRADE_001) ---",
        f"tour_id={tour.id} code={tour.code}",
        f"status={tour.status.value} (expect open_for_sale)",
        f"seats_available={tour.seats_available} seats_total={tour.seats_total} (expect equal)",
        f"orders_remaining_for_tour={n_orders} (expect 0)",
        f"boarding_points={n_bp} (expect >= 1)",
        f"departure_utc={tour.departure_datetime.isoformat()}",
        f"return_utc={tour.return_datetime.isoformat()}",
        f"sales_deadline_utc={tour.sales_deadline.isoformat() if tour.sales_deadline else None}",
    ]
    ok = (
        tour.status == TourStatus.OPEN_FOR_SALE
        and tour.seats_available == tour.seats_total
        and tour.seats_total > 0
        and n_orders == 0
        and n_bp >= 1
        and tour.departure_datetime > clock
        and tour.sales_deadline is not None
        and tour.sales_deadline > clock
        and tour.sales_deadline < tour.departure_datetime
    )
    lines.append(f"SMOKE_READY={'YES' if ok else 'NO'} (if NO, fix data or re-run seed/reset)")
    return lines
