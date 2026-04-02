"""
Manual staging utility: upsert one test tour (TEST_BELGRADE_001) with two boarding points.

Clears prior orders (and payment/outbox rows) before replacing boarding/translations so re-seed is reliable.
Uses rolling departure/sales deadlines (see staging_belgrade_helpers.compute_staging_datetimes).

Requires DATABASE_URL (e.g. from .env at project root).

Usage (from project root, PowerShell):
  python scripts/seed_test_belgrade_tour.py
"""

from __future__ import annotations

import sys
from datetime import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.content_item import ContentItem
from app.models.enums import TourStatus
from app.models.tour import BoardingPoint, Tour, TourTranslation
from staging_belgrade_helpers import (
    TEST_CODE,
    compute_staging_datetimes,
    delete_orders_and_related_for_tour,
    smoke_readiness_lines,
)

BOARDING = (
    ("Timisoara", "Piata 700, Timisoara", time(6, 30, 0), "Main departure point"),
    ("Lugoj", "Central Station, Lugoj", time(7, 15, 0), "Secondary boarding point"),
)


def _clear_existing_test_tour_children(session: Session, tour_id: int) -> None:
    """Remove rows that block re-seed (scoped to this tour only). Orders first (FK-safe)."""
    delete_orders_and_related_for_tour(session, tour_id)
    session.execute(delete(ContentItem).where(ContentItem.tour_id == tour_id))
    session.execute(delete(TourTranslation).where(TourTranslation.tour_id == tour_id))
    session.execute(delete(BoardingPoint).where(BoardingPoint.tour_id == tour_id))
    session.flush()


def _upsert_tour(session: Session) -> Tour:
    departure, return_dt, sales_deadline = compute_staging_datetimes()
    existing = session.scalar(select(Tour).where(Tour.code == TEST_CODE))
    payload = {
        "title_default": "Test Belgrade Tour",
        "short_description_default": "One-day test tour for Mini App validation",
        "full_description_default": "Manual test tour for catalog, reservation, and payment-entry checks.",
        "duration_days": 1,
        "departure_datetime": departure,
        "return_datetime": return_dt,
        "base_price": Decimal("199.00"),
        "currency": "EUR",
        "seats_total": 20,
        "seats_available": 20,
        "sales_deadline": sales_deadline,
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
        tid = tour.id
        session.commit()

        tour = session.scalar(select(Tour).where(Tour.id == tid))
        if tour is None:
            raise RuntimeError("tour missing after commit")
        print(f"OK: seeded tour id={tour.id} code={TEST_CODE} with {len(BOARDING)} boarding points.")
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
