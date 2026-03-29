from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.schemas.notification import NotificationDeliveryRead
from app.services.notification_outbox_retry_execution import NotificationOutboxRetryExecutionService


async def run_once_async(
    *,
    now: datetime | None = None,
    stale_for: timedelta | None = None,
    failed_limit: int = 100,
    stale_limit: int = 100,
) -> list[NotificationDeliveryRead]:
    service = NotificationOutboxRetryExecutionService()
    try:
        with SessionLocal() as session:
            deliveries = await service.execute_retryable_entries(
                session,
                now=now,
                stale_for=stale_for,
                failed_limit=failed_limit,
                stale_limit=stale_limit,
            )
            session.commit()
            return deliveries
    finally:
        await service.close()


def run_once(
    *,
    now: datetime | None = None,
    stale_for: timedelta | None = None,
    failed_limit: int = 100,
    stale_limit: int = 100,
) -> list[NotificationDeliveryRead]:
    return asyncio.run(
        run_once_async(
            now=now,
            stale_for=stale_for,
            failed_limit=failed_limit,
            stale_limit=stale_limit,
        )
    )
