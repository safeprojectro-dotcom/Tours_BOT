from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.notification_outbox import NotificationOutboxRepository
from app.schemas.notification import (
    NotificationDeliveryRead,
    NotificationDeliveryStatus,
    NotificationDispatchRead,
    NotificationDispatchStatus,
    NotificationOutboxRead,
    NotificationOutboxStatus,
    NotificationPayloadRead,
)


class NotificationOutboxService:
    def __init__(
        self,
        *,
        notification_outbox_repository: NotificationOutboxRepository | None = None,
    ) -> None:
        self.notification_outbox_repository = notification_outbox_repository or NotificationOutboxRepository()

    def enqueue_dispatch(
        self,
        session: Session,
        *,
        dispatch: NotificationDispatchRead,
    ) -> NotificationOutboxRead:
        existing = self.notification_outbox_repository.get_by_dispatch_key(
            session,
            dispatch_key=dispatch.dispatch_key,
        )
        if existing is not None:
            return NotificationOutboxRead.model_validate(existing)

        created = self.notification_outbox_repository.create(
            session,
            data={
                "dispatch_key": dispatch.dispatch_key,
                "channel": dispatch.channel,
                "event_type": dispatch.payload.event_type,
                "order_id": dispatch.payload.order_id,
                "user_id": dispatch.payload.user_id,
                "telegram_user_id": dispatch.payload.telegram_user_id,
                "language_code": dispatch.payload.language_code,
                "title": dispatch.payload.title,
                "message": dispatch.payload.message,
                "payload_metadata": self._normalize_json_value(dispatch.payload.metadata),
                "status": NotificationOutboxStatus.PENDING,
            },
        )
        return NotificationOutboxRead.model_validate(created)

    def enqueue_dispatches(
        self,
        session: Session,
        *,
        dispatches: list[NotificationDispatchRead],
    ) -> list[NotificationOutboxRead]:
        entries: list[NotificationOutboxRead] = []
        for dispatch in dispatches:
            entries.append(self.enqueue_dispatch(session, dispatch=dispatch))
        return entries

    def list_pending_entries(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationOutboxRead]:
        items = self.notification_outbox_repository.list_by_status(
            session,
            status=NotificationOutboxStatus.PENDING,
            limit=limit,
            offset=offset,
        )
        return [NotificationOutboxRead.model_validate(item) for item in items]

    def list_pending_dispatches(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationDispatchRead]:
        entries = self.list_pending_entries(session, limit=limit, offset=offset)
        dispatches: list[NotificationDispatchRead] = []
        for entry in entries:
            dispatches.append(self.to_dispatch(entry))
        return dispatches

    def pickup_pending_entries(
        self,
        session: Session,
        *,
        limit: int = 100,
    ) -> list[NotificationOutboxRead]:
        outbox_ids = self.notification_outbox_repository.list_pending_ids_for_pickup(
            session,
            limit=limit,
        )
        picked: list[NotificationOutboxRead] = []
        for outbox_id in outbox_ids:
            entry = self.notification_outbox_repository.get_for_update(session, outbox_id=outbox_id)
            if entry is None or entry.status != NotificationOutboxStatus.PENDING:
                continue
            updated = self.notification_outbox_repository.update(
                session,
                instance=entry,
                data={"status": NotificationOutboxStatus.PROCESSING},
            )
            picked.append(NotificationOutboxRead.model_validate(updated))
        return picked

    def pickup_pending_entries_by_ids(
        self,
        session: Session,
        *,
        outbox_ids: list[int],
    ) -> list[NotificationOutboxRead]:
        picked: list[NotificationOutboxRead] = []
        for outbox_id in outbox_ids:
            entry = self.notification_outbox_repository.get_for_update(session, outbox_id=outbox_id)
            if entry is None or entry.status != NotificationOutboxStatus.PENDING:
                continue
            updated = self.notification_outbox_repository.update(
                session,
                instance=entry,
                data={"status": NotificationOutboxStatus.PROCESSING},
            )
            picked.append(NotificationOutboxRead.model_validate(updated))
        return picked

    def apply_delivery_result(
        self,
        session: Session,
        *,
        delivery: NotificationDeliveryRead,
    ) -> NotificationOutboxRead | None:
        entry = self.notification_outbox_repository.get_by_dispatch_key(
            session,
            dispatch_key=delivery.dispatch_key,
        )
        if entry is None:
            return None

        next_status = (
            NotificationOutboxStatus.DELIVERED
            if delivery.status == NotificationDeliveryStatus.DELIVERED
            else NotificationOutboxStatus.FAILED
        )
        updated = self.notification_outbox_repository.update(
            session,
            instance=entry,
            data={"status": next_status},
        )
        return NotificationOutboxRead.model_validate(updated)

    @staticmethod
    def to_dispatch(entry: NotificationOutboxRead) -> NotificationDispatchRead:
        return NotificationDispatchRead(
            dispatch_key=entry.dispatch_key,
            channel=entry.channel,
            status=NotificationDispatchStatus.PREPARED,
            payload=NotificationPayloadRead(
                event_type=entry.event_type,
                order_id=entry.order_id,
                user_id=entry.user_id,
                telegram_user_id=entry.telegram_user_id,
                language_code=entry.language_code,
                title=entry.title,
                message=entry.message,
                metadata=entry.payload_metadata or {},
            ),
        )

    @classmethod
    def _normalize_json_value(cls, value):
        if isinstance(value, dict):
            return {str(key): cls._normalize_json_value(item) for key, item in value.items()}
        if isinstance(value, list | tuple):
            return [cls._normalize_json_value(item) for item in value]
        if isinstance(value, Decimal):
            return str(value)
        return value
