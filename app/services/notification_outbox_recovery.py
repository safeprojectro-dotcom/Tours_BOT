from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories.notification_outbox import NotificationOutboxRepository
from app.schemas.notification import NotificationOutboxRead, NotificationOutboxStatus


class NotificationOutboxRecoveryService:
    DEFAULT_STALE_PROCESSING_AGE = timedelta(minutes=15)

    def __init__(
        self,
        *,
        notification_outbox_repository: NotificationOutboxRepository | None = None,
    ) -> None:
        self.notification_outbox_repository = notification_outbox_repository or NotificationOutboxRepository()

    def retry_failed_entries(
        self,
        session: Session,
        *,
        limit: int = 100,
    ) -> list[NotificationOutboxRead]:
        outbox_ids = self.notification_outbox_repository.list_failed_ids_for_retry(
            session,
            limit=limit,
        )
        return self._reset_entries_to_pending(session, outbox_ids=outbox_ids, expected_status=NotificationOutboxStatus.FAILED)

    def recover_stale_processing_entries(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        stale_for: timedelta | None = None,
        limit: int = 100,
    ) -> list[NotificationOutboxRead]:
        current_time = now or datetime.now(UTC)
        stale_age = stale_for or self.DEFAULT_STALE_PROCESSING_AGE
        outbox_ids = self.notification_outbox_repository.list_stale_processing_ids(
            session,
            stale_before=current_time - stale_age,
            limit=limit,
        )
        return self._reset_entries_to_pending(
            session,
            outbox_ids=outbox_ids,
            expected_status=NotificationOutboxStatus.PROCESSING,
        )

    def recover_retryable_entries(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        stale_for: timedelta | None = None,
        failed_limit: int = 100,
        stale_limit: int = 100,
    ) -> list[NotificationOutboxRead]:
        recovered: list[NotificationOutboxRead] = []
        recovered.extend(self.retry_failed_entries(session, limit=failed_limit))
        recovered.extend(
            self.recover_stale_processing_entries(
                session,
                now=now,
                stale_for=stale_for,
                limit=stale_limit,
            )
        )
        return recovered

    def _reset_entries_to_pending(
        self,
        session: Session,
        *,
        outbox_ids: list[int],
        expected_status: NotificationOutboxStatus,
    ) -> list[NotificationOutboxRead]:
        recovered: list[NotificationOutboxRead] = []
        for outbox_id in outbox_ids:
            entry = self.notification_outbox_repository.get_for_update(session, outbox_id=outbox_id)
            if entry is None or entry.status != expected_status:
                continue
            updated = self.notification_outbox_repository.update(
                session,
                instance=entry,
                data={"status": NotificationOutboxStatus.PENDING},
            )
            recovered.append(NotificationOutboxRead.model_validate(updated))
        return recovered
