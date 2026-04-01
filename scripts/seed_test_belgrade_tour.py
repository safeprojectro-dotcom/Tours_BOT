"""
Manual staging utility: upsert one test tour (TEST_BELGRADE_001) with two boarding points.

Not run automatically. Requires DATABASE_URL (e.g. from .env at project root).

Usage (from project root):
  python scripts/seed_test_belgrade_tour.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.content_item import ContentItem
from app.models.enums import TourStatus
from app.models.order import Order
from app.models.tour import BoardingPoint, Tour, TourTranslation
from app.models.waitlist import WaitlistEntry

TEST_CODE = "TEST_BELGRADE_001"

DEPARTURE = datetime(2026, 4, 10, 8, 44, 32, tzinfo=UTC)
RETURN_DT = datetime(2026, 4, 10, 20, 44, 32, tzinfo=UTC)
SALES_DEADLINE = datetime(2026, 4, 9, 8, 44, 32, tzinfo=UTC)

BOARDING = (
    ("Timisoara", "Piata 700, Timisoara", time(6, 30, 0), "Main departure point"),
    ("Lugoj", "Central Station, Lugoj", time(7, 15, 0), "Secondary boarding point"),
)


def _clear_existing_test_tour_children(session: Session, tour_id: int) -> None:
    """Remove rows that block re-seed or replacement boarding points (scoped to this tour only)."""
    session.execute(delete(Order).where(Order.tour_id == tour_id))
    session.execute(delete(WaitlistEntry).where(WaitlistEntry.tour_id == tour_id))
    session.execute(delete(ContentItem).where(ContentItem.tour_id == tour_id))
    session.execute(delete(TourTranslation).where(TourTranslation.tour_id == tour_id))
    session.execute(delete(BoardingPoint).where(BoardingPoint.tour_id == tour_id))
    session.flush()


def _upsert_tour(session: Session) -> Tour:
    existing = session.scalar(select(Tour).where(Tour.code == TEST_CODE))
    payload = {
        "title_default": "Test Belgrade Tour",
        "short_description_default": "One-day test tour for Mini App validation",
        "full_description_default": "Manual test tour for catalog, reservation, and payment-entry checks.",
        "duration_days": 1,
        "departure_datetime": DEPARTURE,
        "return_datetime": RETURN_DT,
        "base_price": Decimal("199.00"),
        "currency": "EUR",
        "seats_total": 20,
        "seats_available": 20,
        "sales_deadline": SALES_DEADLINE,
        "status": TourStatus.OPEN_FOR_SALE,
        "guaranteed_flag": True,
    }
    if existing is not None:
        _clear_existing_test_tour_children(session, existing.id)
        for key, value in payload.items():
            setattr(existing, key, value)
        session.flush()
        return existing

    tour = Tour(
        code=TEST_CODE,
        **payload,
    )
    session.add(tour)
    session.flush()
    return tour


def _insert_boarding_points(session: Session, tour_id: int) -> None:
    for city, address, t, notes in BOARDING:
        session.add(
            BoardingPoint(
                tour_id=tour_id,
                city=city,
                address=address,
                time=t,
                notes=notes,
            )
        )


def main() -> None:
    session = SessionLocal()
    try:
        tour = _upsert_tour(session)
        _insert_boarding_points(session, tour.id)
        session.commit()
        print(f"OK: seeded tour id={tour.id} code={TEST_CODE} with {len(BOARDING)} boarding points.")
    except Exception as exc:
        session.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
