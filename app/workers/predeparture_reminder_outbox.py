from __future__ import annotations

from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.schemas.notification import NotificationOutboxRead
from app.services.predeparture_reminder_outbox import PredepartureReminderOutboxService


def run_once(
    *,
    now: datetime | None = None,
    due_within: timedelta | None = None,
    limit: int = 100,
) -> list[NotificationOutboxRead]:
    service = PredepartureReminderOutboxService()
    with SessionLocal() as session:
        entries = service.enqueue_due_reminders(
            session,
            now=now,
            due_within=due_within,
            limit=limit,
        )
        session.commit()
        return entries
