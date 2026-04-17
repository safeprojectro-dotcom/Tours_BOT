"""Refresh dedicated smoke tours so departures and sales deadlines stay in the future.

Does not alter booking, payment, or marketplace business rules — only upserts/fixes
rows for stable tour codes used in manual or automated smoke checks.

Run: ``python -m app.scripts.ensure_smoke_tours``

Optional env: ``SMOKE_TOURS_DAYS_AHEAD`` (default ``60``) — days from UTC "today"
until departure date (08:00 UTC).
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.enums import TourSalesMode, TourStatus
from app.models.tour import BoardingPoint, Tour


SMOKE_PER_SEAT_CODE = "SMOKE_PER_SEAT_001"
SMOKE_FULL_BUS_CODE = "SMOKE_FULL_BUS_001"


def compute_smoke_tour_schedule(
    *,
    now: datetime,
    days_ahead: int = 60,
    duration_days: int = 2,
) -> tuple[datetime, datetime, datetime]:
    """Return ``departure_datetime``, ``return_datetime``, ``sales_deadline`` (timezone-aware UTC).

    Guarantees (when ``days_ahead >= 2``): all three are strictly after ``now``,
    ``return_datetime > departure_datetime``, and ``sales_deadline < departure_datetime``.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware (use UTC).")
    if days_ahead < 2:
        raise ValueError("days_ahead must be at least 2 so sales_deadline remains in the future.")
    if duration_days < 1:
        raise ValueError("duration_days must be >= 1.")

    dep_date = (now.astimezone(UTC) + timedelta(days=days_ahead)).date()
    departure = datetime.combine(dep_date, time(8, 0), tzinfo=UTC)
    return_dt = departure + timedelta(days=duration_days)
    # Day before departure, same clock time — still strictly after ``now`` when days_ahead >= 2
    sales_deadline = departure - timedelta(days=1)
    return departure, return_dt, sales_deadline


def _ensure_boarding_point(session: Session, tour: Tour) -> None:
    n = session.scalar(
        select(func.count()).select_from(BoardingPoint).where(BoardingPoint.tour_id == tour.id),
    )
    if (n or 0) > 0:
        return
    session.add(
        BoardingPoint(
            tour_id=tour.id,
            city="Smoke City",
            address="Smoke boarding (auto)",
            time=time(6, 30),
            notes="Created by ensure_smoke_tours",
        ),
    )


def _apply_smoke_tour(
    session: Session,
    *,
    code: str,
    title: str,
    sales_mode: TourSalesMode,
    seats_total: int,
    seats_available: int,
    base_price: Decimal,
    departure: datetime,
    return_dt: datetime,
    sales_deadline: datetime,
) -> str:
    tour = session.scalar(select(Tour).where(Tour.code == code))
    if tour is None:
        tour = Tour(
            code=code,
            title_default=title,
            short_description_default="Automated smoke tour — refresh with ensure_smoke_tours.",
            full_description_default="See docs / COMMIT_PUSH_DEPLOY.md (smoke tour refresh).",
            duration_days=max(1, (return_dt - departure).days or 1),
            departure_datetime=departure,
            return_datetime=return_dt,
            base_price=base_price,
            currency="EUR",
            seats_total=seats_total,
            seats_available=min(seats_available, seats_total),
            sales_deadline=sales_deadline,
            sales_mode=sales_mode,
            status=TourStatus.OPEN_FOR_SALE,
            guaranteed_flag=False,
        )
        session.add(tour)
        session.flush()
        _ensure_boarding_point(session, tour)
        return f"created {code}"

    tour.title_default = title
    tour.duration_days = max(1, (return_dt - departure).days or 1)
    tour.departure_datetime = departure
    tour.return_datetime = return_dt
    tour.sales_deadline = sales_deadline
    tour.sales_mode = sales_mode
    tour.status = TourStatus.OPEN_FOR_SALE
    tour.base_price = base_price
    tour.currency = "EUR"
    # Dedicated smoke codes: normalize inventory so catalog/preparation smokes stay green.
    # Use only on dev/staging (or empty DBs); resetting seats can conflict with existing orders.
    tour.seats_total = seats_total
    tour.seats_available = min(seats_available, seats_total)
    _ensure_boarding_point(session, tour)
    return f"updated {code}"


def ensure_smoke_tours(*, session: Session, days_ahead: int = 60) -> list[str]:
    """Idempotently create or refresh smoke tours. Commits are the caller's responsibility."""
    now = datetime.now(UTC)
    departure, return_dt, sales_deadline = compute_smoke_tour_schedule(
        now=now,
        days_ahead=days_ahead,
        duration_days=2,
    )
    lines: list[str] = []
    lines.append(
        _apply_smoke_tour(
            session,
            code=SMOKE_PER_SEAT_CODE,
            title="Smoke per-seat catalog / booking",
            sales_mode=TourSalesMode.PER_SEAT,
            seats_total=50,
            seats_available=30,
            base_price=Decimal("99.00"),
            departure=departure,
            return_dt=return_dt,
            sales_deadline=sales_deadline,
        ),
    )
    lines.append(
        _apply_smoke_tour(
            session,
            code=SMOKE_FULL_BUS_CODE,
            title="Smoke full-bus policy / preparation",
            sales_mode=TourSalesMode.FULL_BUS,
            seats_total=49,
            seats_available=49,
            base_price=Decimal("2499.00"),
            departure=departure,
            return_dt=return_dt,
            sales_deadline=sales_deadline,
        ),
    )
    return lines


def main() -> int:
    raw = os.environ.get("SMOKE_TOURS_DAYS_AHEAD", "60").strip()
    try:
        days_ahead = int(raw)
    except ValueError:
        print(f"Invalid SMOKE_TOURS_DAYS_AHEAD={raw!r}", file=sys.stderr)
        return 2
    if days_ahead < 2:
        print("SMOKE_TOURS_DAYS_AHEAD must be >= 2", file=sys.stderr)
        return 2

    session = SessionLocal()
    try:
        lines = ensure_smoke_tours(session=session, days_ahead=days_ahead)
        session.commit()
    except Exception as exc:  # noqa: BLE001 — script boundary
        session.rollback()
        print(f"ensure_smoke_tours failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
