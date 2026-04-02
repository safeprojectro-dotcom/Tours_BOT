"""
Staging-only: clear orders / waitlist / content tied to TEST_BELGRADE_001 and restore seat availability.

Does not delete the tour, boarding points, or translations — only frees capacity for manual prepare smoke-tests.

Requires DATABASE_URL (e.g. from .env at project root).

Usage (from project root):
  python scripts/reset_test_belgrade_tour_state.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.content_item import ContentItem
from app.models.order import Order
from app.models.tour import Tour
from app.models.waitlist import WaitlistEntry

TEST_CODE = "TEST_BELGRADE_001"


def _clear_tour_booking_artifacts(session: Session, tour_id: int) -> int:
    """Remove dependent rows for this tour; return number of orders deleted."""
    orders = session.scalars(select(Order.id).where(Order.tour_id == tour_id)).all()
    session.execute(delete(Order).where(Order.tour_id == tour_id))
    session.execute(delete(WaitlistEntry).where(WaitlistEntry.tour_id == tour_id))
    session.execute(delete(ContentItem).where(ContentItem.tour_id == tour_id))
    session.flush()
    return len(orders)


def main() -> None:
    session = SessionLocal()
    try:
        tour = session.scalar(select(Tour).where(Tour.code == TEST_CODE))
        if tour is None:
            print(f"Nothing to do: no tour with code {TEST_CODE!r}. Run scripts/seed_test_belgrade_tour.py first.")
            return

        n_orders = _clear_tour_booking_artifacts(session, tour.id)
        tour.seats_available = tour.seats_total
        session.commit()
        print(
            f"OK: reset tour id={tour.id} code={TEST_CODE}. "
            f"Removed {n_orders} order(s); seats_available set to {tour.seats_available}."
        )
    except Exception as exc:
        session.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
