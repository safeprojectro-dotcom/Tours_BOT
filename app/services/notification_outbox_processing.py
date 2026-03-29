from __future__ import annotations

from app.schemas.notification import NotificationDeliveryRead, NotificationOutboxRead
from app.services.notification_delivery import NotificationDeliveryService
from app.services.notification_outbox import NotificationOutboxService
from sqlalchemy.orm import Session


class NotificationOutboxProcessingService:
    def __init__(
        self,
        *,
        notification_outbox_service: NotificationOutboxService | None = None,
        notification_delivery_service: NotificationDeliveryService | None = None,
    ) -> None:
        self.notification_outbox_service = notification_outbox_service or NotificationOutboxService()
        self.notification_delivery_service = notification_delivery_service or NotificationDeliveryService()

    async def process_pending_entries(
        self,
        session: Session,
        *,
        limit: int = 100,
    ) -> list[NotificationDeliveryRead]:
        picked_entries = self.notification_outbox_service.pickup_pending_entries(
            session,
            limit=limit,
        )
        return await self._deliver_picked_entries(session, picked_entries=picked_entries)

    async def process_pending_entries_by_ids(
        self,
        session: Session,
        *,
        outbox_ids: list[int],
    ) -> list[NotificationDeliveryRead]:
        picked_entries = self.notification_outbox_service.pickup_pending_entries_by_ids(
            session,
            outbox_ids=outbox_ids,
        )
        return await self._deliver_picked_entries(session, picked_entries=picked_entries)

    async def _deliver_picked_entries(
        self,
        session: Session,
        *,
        picked_entries: list[NotificationOutboxRead],
    ) -> list[NotificationDeliveryRead]:
        deliveries: list[NotificationDeliveryRead] = []
        for entry in picked_entries:
            dispatch = self.notification_outbox_service.to_dispatch(entry)
            delivery = await self.notification_delivery_service.deliver_dispatch(dispatch)
            self.notification_outbox_service.apply_delivery_result(
                session,
                delivery=delivery,
            )
            deliveries.append(delivery)
        return deliveries

    async def close(self) -> None:
        await self.notification_delivery_service.close()
