"""
Staging-only: clear orders / waitlist tied to TEST_BELGRADE_001 and restore seat availability.

Does not delete the tour, boarding points, translations, or content_items — only frees capacity for manual prepare smoke-tests.

Deletes child payment and notification rows for those orders first (explicit order for DBs that rely on FK cleanup),
then orders for this tour_id.

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
from app.models.enums import TourStatus
from app.models.notification_outbox import NotificationOutbox
from app.models.order import Order
from app.models.payment import Payment
from app.models.tour import Tour
from app.models.waitlist import WaitlistEntry

TEST_CODE = "TEST_BELGRADE_001"


def _clear_tour_booking_artifacts(session: Session, tour_id: int) -> int:
    """Remove dependent rows for this tour; return number of orders deleted."""
    order_ids = list(session.scalars(select(Order.id).where(Order.tour_id == tour_id)).all())
    if order_ids:
        session.execute(delete(Payment).where(Payment.order_id.in_(order_ids)))
        session.execute(delete(NotificationOutbox).where(NotificationOutbox.order_id.in_(order_ids)))
    session.execute(delete(Order).where(Order.tour_id == tour_id))
    session.execute(delete(WaitlistEntry).where(WaitlistEntry.tour_id == tour_id))
    session.flush()
    return len(order_ids)


def main() -> None:
    session = SessionLocal()
    try:
        tour = session.scalar(select(Tour).where(Tour.code == TEST_CODE))
        if tour is None:
            print(f"Nothing to do: no tour with code {TEST_CODE!r}. Run scripts/seed_test_belgrade_tour.py first.")
            return

        n_orders = _clear_tour_booking_artifacts(session, tour.id)
        tour.seats_available = tour.seats_total
        tour.status = TourStatus.OPEN_FOR_SALE
        session.commit()
        print(
            f"OK: reset tour id={tour.id} code={TEST_CODE}. "
            f"Removed {n_orders} order(s); seats_available={tour.seats_available}; status={tour.status.value}."
        )
    except Exception as exc:
        session.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
