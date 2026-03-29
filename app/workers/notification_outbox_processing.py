from __future__ import annotations

import asyncio

from app.db.session import SessionLocal
from app.schemas.notification import NotificationDeliveryRead
from app.services.notification_outbox_processing import NotificationOutboxProcessingService


async def run_once_async(*, limit: int = 100) -> list[NotificationDeliveryRead]:
    service = NotificationOutboxProcessingService()
    try:
        with SessionLocal() as session:
            deliveries = await service.process_pending_entries(
                session,
                limit=limit,
            )
            session.commit()
            return deliveries
    finally:
        await service.close()


def run_once(*, limit: int = 100) -> list[NotificationDeliveryRead]:
    return asyncio.run(run_once_async(limit=limit))
