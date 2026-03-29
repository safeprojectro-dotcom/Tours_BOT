from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.schemas.notification import NotificationChannel, NotificationDeliveryRead
from app.services.notification_delivery import NotificationDeliveryService
from app.services.payment_pending_reminder import PaymentPendingReminderService


class PaymentPendingReminderDeliveryService:
    def __init__(
        self,
        *,
        payment_pending_reminder_service: PaymentPendingReminderService | None = None,
        notification_delivery_service: NotificationDeliveryService | None = None,
    ) -> None:
        self.payment_pending_reminder_service = payment_pending_reminder_service or PaymentPendingReminderService()
        self.notification_delivery_service = notification_delivery_service or NotificationDeliveryService()

    async def deliver_due_reminders(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        due_within: timedelta | None = None,
        limit: int = 100,
        channel: NotificationChannel = NotificationChannel.TELEGRAM_PRIVATE,
    ) -> list[NotificationDeliveryRead]:
        dispatches = self.payment_pending_reminder_service.prepare_due_reminders(
            session,
            now=now,
            due_within=due_within,
            limit=limit,
            channel=channel,
        )
        return await self.notification_delivery_service.deliver_dispatches(dispatches)

    async def close(self) -> None:
        await self.notification_delivery_service.close()
