from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.schemas.notification import NotificationChannel, NotificationOutboxRead
from app.services.notification_outbox import NotificationOutboxService
from app.services.post_trip_reminder import PostTripReminderService


class PostTripReminderOutboxService:
    def __init__(
        self,
        *,
        post_trip_reminder_service: PostTripReminderService | None = None,
        notification_outbox_service: NotificationOutboxService | None = None,
    ) -> None:
        self.post_trip_reminder_service = post_trip_reminder_service or PostTripReminderService()
        self.notification_outbox_service = notification_outbox_service or NotificationOutboxService()

    def enqueue_due_reminders(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        due_within: timedelta | None = None,
        limit: int = 100,
        channel: NotificationChannel = NotificationChannel.TELEGRAM_PRIVATE,
    ) -> list[NotificationOutboxRead]:
        dispatches = self.post_trip_reminder_service.prepare_due_reminders(
            session,
            now=now,
            due_within=due_within,
            limit=limit,
            channel=channel,
        )
        return self.notification_outbox_service.enqueue_dispatches(
            session,
            dispatches=dispatches,
        )
