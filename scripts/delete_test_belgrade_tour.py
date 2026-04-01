"""
Manual staging utility: delete only the test tour TEST_BELGRADE_001 and its dependent rows.

Not run automatically. Requires DATABASE_URL.

Usage (from project root):
  python scripts/delete_test_belgrade_tour.py
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
from app.models.tour import BoardingPoint, Tour, TourTranslation
from app.models.waitlist import WaitlistEntry

TEST_CODE = "TEST_BELGRADE_001"


def main() -> None:
    session = SessionLocal()
    try:
        tour = session.scalar(select(Tour).where(Tour.code == TEST_CODE))
        if tour is None:
            print(f"Nothing to do: no tour with code {TEST_CODE!r}.")
            return

        tid = tour.id
        session.execute(delete(Order).where(Order.tour_id == tid))
        session.execute(delete(WaitlistEntry).where(WaitlistEntry.tour_id == tid))
        session.execute(delete(ContentItem).where(ContentItem.tour_id == tid))
        session.execute(delete(TourTranslation).where(TourTranslation.tour_id == tid))
        session.execute(delete(BoardingPoint).where(BoardingPoint.tour_id == tid))
        session.delete(tour)
        session.commit()
        print(f"OK: deleted tour id={tid} code={TEST_CODE} and related rows.")
    except Exception as exc:
        session.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
