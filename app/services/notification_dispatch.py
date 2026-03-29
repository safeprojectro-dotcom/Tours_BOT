from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.notification import (
    NotificationChannel,
    NotificationDispatchRead,
    NotificationDispatchStatus,
    NotificationEventType,
)
from app.services.notification_preparation import NotificationPreparationService


class NotificationDispatchService:
    def __init__(
        self,
        *,
        notification_preparation_service: NotificationPreparationService | None = None,
    ) -> None:
        self.notification_preparation_service = notification_preparation_service or NotificationPreparationService()

    def prepare_dispatch(
        self,
        session: Session,
        *,
        order_id: int,
        event_type: NotificationEventType,
        language_code: str | None = None,
        channel: NotificationChannel = NotificationChannel.TELEGRAM_PRIVATE,
    ) -> NotificationDispatchRead | None:
        payload = self.notification_preparation_service.prepare_notification(
            session,
            order_id=order_id,
            event_type=event_type,
            language_code=language_code,
        )
        if payload is None:
            return None

        return NotificationDispatchRead(
            dispatch_key=self.build_dispatch_key(
                order_id=payload.order_id,
                event_type=payload.event_type,
                channel=channel,
                language_code=payload.language_code,
            ),
            channel=channel,
            status=NotificationDispatchStatus.PREPARED,
            payload=payload,
        )

    def prepare_available_dispatches(
        self,
        session: Session,
        *,
        order_id: int,
        language_code: str | None = None,
        channel: NotificationChannel = NotificationChannel.TELEGRAM_PRIVATE,
    ) -> list[NotificationDispatchRead]:
        event_types = self.notification_preparation_service.list_available_event_types(
            session,
            order_id=order_id,
        )
        dispatches: list[NotificationDispatchRead] = []
        seen_keys: set[str] = set()
        for event_type in event_types:
            dispatch = self.prepare_dispatch(
                session,
                order_id=order_id,
                event_type=event_type,
                language_code=language_code,
                channel=channel,
            )
            if dispatch is None or dispatch.dispatch_key in seen_keys:
                continue
            seen_keys.add(dispatch.dispatch_key)
            dispatches.append(dispatch)
        return dispatches

    @staticmethod
    def build_dispatch_key(
        *,
        order_id: int,
        event_type: NotificationEventType,
        channel: NotificationChannel,
        language_code: str,
    ) -> str:
        return f"{channel.value}:{event_type.value}:{order_id}:{language_code}"
