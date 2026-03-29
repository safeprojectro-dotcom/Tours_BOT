from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories.order import OrderRepository
from app.schemas.notification import NotificationChannel, NotificationDispatchRead, NotificationEventType
from app.services.notification_dispatch import NotificationDispatchService


class DepartureDayReminderService:
    DEFAULT_REMINDER_WINDOW = timedelta(hours=24)

    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        notification_dispatch_service: NotificationDispatchService | None = None,
    ) -> None:
        self.order_repository = order_repository or OrderRepository()
        self.notification_dispatch_service = notification_dispatch_service or NotificationDispatchService()

    def list_due_order_ids(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        due_within: timedelta | None = None,
        limit: int = 100,
    ) -> list[int]:
        current_time = now or datetime.now(UTC)
        reminder_window = due_within or self.DEFAULT_REMINDER_WINDOW
        return self.order_repository.list_departure_day_reminder_order_ids(
            session,
            now=current_time,
            due_within=reminder_window,
            limit=limit,
        )

    def prepare_due_reminders(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        due_within: timedelta | None = None,
        limit: int = 100,
        channel: NotificationChannel = NotificationChannel.TELEGRAM_PRIVATE,
    ) -> list[NotificationDispatchRead]:
        order_ids = self.list_due_order_ids(
            session,
            now=now,
            due_within=due_within,
            limit=limit,
        )
        dispatches: list[NotificationDispatchRead] = []
        seen_keys: set[str] = set()
        for order_id in order_ids:
            dispatch = self.notification_dispatch_service.prepare_dispatch(
                session,
                order_id=order_id,
                event_type=NotificationEventType.DEPARTURE_DAY_REMINDER,
                channel=channel,
            )
            if dispatch is None or dispatch.dispatch_key in seen_keys:
                continue
            seen_keys.add(dispatch.dispatch_key)
            dispatches.append(dispatch)
        return dispatches
