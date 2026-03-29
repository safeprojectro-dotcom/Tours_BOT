from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.schemas.notification import NotificationDeliveryRead
from app.services.payment_pending_reminder_delivery import PaymentPendingReminderDeliveryService


async def run_once_async(
    *,
    now: datetime | None = None,
    due_within: timedelta | None = None,
    limit: int = 100,
) -> list[NotificationDeliveryRead]:
    service = PaymentPendingReminderDeliveryService()
    try:
        with SessionLocal() as session:
            return await service.deliver_due_reminders(
                session,
                now=now,
                due_within=due_within,
                limit=limit,
            )
    finally:
        await service.close()


def run_once(
    *,
    now: datetime | None = None,
    due_within: timedelta | None = None,
    limit: int = 100,
) -> list[NotificationDeliveryRead]:
    return asyncio.run(
        run_once_async(
            now=now,
            due_within=due_within,
            limit=limit,
        )
    )
