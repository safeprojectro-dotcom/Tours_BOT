"""
Staging-only: clear booking artifacts for TEST_BELGRADE_001 and restore smoke-ready state.

Removes payments, notification_outbox rows, orders, and waitlist for this tour; restores seats;
sets status open_for_sale; rolls departure/return/sales_deadline forward so dates are not stale.

Does not delete boarding points, translations, or content_items.

Requires DATABASE_URL (e.g. from .env at project root).

Usage (from project root, PowerShell):
  python scripts/reset_test_belgrade_tour_state.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.tour import Tour
from staging_belgrade_helpers import (
    TEST_CODE,
    apply_smoke_ready_tour_fields,
    delete_orders_and_related_for_tour,
    smoke_readiness_lines,
)


def main() -> None:
    session = SessionLocal()
    try:
        tour = session.scalar(select(Tour).where(Tour.code == TEST_CODE))
        if tour is None:
            print(f"Nothing to do: no tour with code {TEST_CODE!r}. Run scripts/seed_test_belgrade_tour.py first.")
            return

        n_orders = delete_orders_and_related_for_tour(session, tour.id)
        apply_smoke_ready_tour_fields(tour)
        session.commit()

        tid = tour.id
        session.expire_all()
        tour = session.scalar(select(Tour).where(Tour.id == tid))
        if tour is None:
            raise RuntimeError("tour missing after commit")

        print(
            f"OK: reset tour id={tour.id} code={TEST_CODE}. "
            f"Removed {n_orders} order(s); seats_available={tour.seats_available}; status={tour.status.value}."
        )
        for line in smoke_readiness_lines(session, tour):
            print(line)
    except Exception as exc:
        session.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
