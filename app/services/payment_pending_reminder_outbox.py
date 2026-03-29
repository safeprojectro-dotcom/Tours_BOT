from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.schemas.notification import NotificationChannel, NotificationOutboxRead
from app.services.notification_outbox import NotificationOutboxService
from app.services.payment_pending_reminder import PaymentPendingReminderService


class PaymentPendingReminderOutboxService:
    def __init__(
        self,
        *,
        payment_pending_reminder_service: PaymentPendingReminderService | None = None,
        notification_outbox_service: NotificationOutboxService | None = None,
    ) -> None:
        self.payment_pending_reminder_service = payment_pending_reminder_service or PaymentPendingReminderService()
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
        dispatches = self.payment_pending_reminder_service.prepare_due_reminders(
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
