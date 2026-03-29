from __future__ import annotations

from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.schemas.notification import NotificationOutboxRead
from app.services.notification_outbox_recovery import NotificationOutboxRecoveryService


def run_once(
    *,
    now: datetime | None = None,
    stale_for: timedelta | None = None,
    failed_limit: int = 100,
    stale_limit: int = 100,
) -> list[NotificationOutboxRead]:
    service = NotificationOutboxRecoveryService()
    with SessionLocal() as session:
        entries = service.recover_retryable_entries(
            session,
            now=now,
            stale_for=stale_for,
            failed_limit=failed_limit,
            stale_limit=stale_limit,
        )
        session.commit()
        return entries
