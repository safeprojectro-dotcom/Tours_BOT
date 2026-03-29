from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.schemas.notification import NotificationDeliveryRead
from app.services.notification_outbox_processing import NotificationOutboxProcessingService
from app.services.notification_outbox_recovery import NotificationOutboxRecoveryService


class NotificationOutboxRetryExecutionService:
    def __init__(
        self,
        *,
        notification_outbox_recovery_service: NotificationOutboxRecoveryService | None = None,
        notification_outbox_processing_service: NotificationOutboxProcessingService | None = None,
    ) -> None:
        self.notification_outbox_recovery_service = (
            notification_outbox_recovery_service or NotificationOutboxRecoveryService()
        )
        self.notification_outbox_processing_service = (
            notification_outbox_processing_service or NotificationOutboxProcessingService()
        )

    async def process_retryable_pending_entries(
        self,
        session: Session,
        *,
        outbox_ids: list[int],
    ) -> list[NotificationDeliveryRead]:
        return await self.notification_outbox_processing_service.process_pending_entries_by_ids(
            session,
            outbox_ids=outbox_ids,
        )

    async def execute_retryable_entries(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        stale_for: timedelta | None = None,
        failed_limit: int = 100,
        stale_limit: int = 100,
    ) -> list[NotificationDeliveryRead]:
        recovered_entries = self.notification_outbox_recovery_service.recover_retryable_entries(
            session,
            now=now,
            stale_for=stale_for,
            failed_limit=failed_limit,
            stale_limit=stale_limit,
        )
        return await self.process_retryable_pending_entries(
            session,
            outbox_ids=[entry.id for entry in recovered_entries],
        )

    async def close(self) -> None:
        await self.notification_outbox_processing_service.close()
