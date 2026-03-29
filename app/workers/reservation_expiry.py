from __future__ import annotations

from datetime import datetime

from app.db.session import SessionLocal
from app.services.reservation_expiry import ReservationExpiryService


def run_once(*, now: datetime | None = None, limit: int = 100) -> int:
    service = ReservationExpiryService()
    with SessionLocal() as session:
        expired_count = service.expire_due_reservations(
            session,
            now=now,
            limit=limit,
        )
        session.commit()
        return expired_count
