from __future__ import annotations

from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.schemas.notification import NotificationDispatchRead
from app.services.payment_pending_reminder import PaymentPendingReminderService


def run_once(
    *,
    now: datetime | None = None,
    due_within: timedelta | None = None,
    limit: int = 100,
) -> list[NotificationDispatchRead]:
    service = PaymentPendingReminderService()
    with SessionLocal() as session:
        return service.prepare_due_reminders(
            session,
            now=now,
            due_within=due_within,
            limit=limit,
        )
