from __future__ import annotations

from app.schemas.notification import (
    NotificationChannel,
    NotificationDeliveryRead,
    NotificationDeliveryStatus,
    NotificationDispatchRead,
)
from app.services.telegram_private_delivery import (
    AiogramTelegramPrivateDeliveryAdapter,
    TelegramPrivateDeliveryAdapter,
)


class NotificationDeliveryService:
    def __init__(
        self,
        *,
        telegram_private_adapter: TelegramPrivateDeliveryAdapter | None = None,
    ) -> None:
        self.telegram_private_adapter = telegram_private_adapter
        self._owns_telegram_private_adapter = telegram_private_adapter is None

    async def deliver_dispatch(self, dispatch: NotificationDispatchRead) -> NotificationDeliveryRead:
        if dispatch.channel != NotificationChannel.TELEGRAM_PRIVATE:
            return NotificationDeliveryRead(
                dispatch_key=dispatch.dispatch_key,
                channel=dispatch.channel,
                status=NotificationDeliveryStatus.FAILED,
                payload=dispatch.payload,
                error_message=f"Unsupported notification channel: {dispatch.channel.value}",
            )

        adapter = self._get_telegram_private_adapter()
        try:
            provider_message_id = await adapter.send_message(
                telegram_user_id=dispatch.payload.telegram_user_id,
                text=self.render_dispatch_text(dispatch),
            )
            return NotificationDeliveryRead(
                dispatch_key=dispatch.dispatch_key,
                channel=dispatch.channel,
                status=NotificationDeliveryStatus.DELIVERED,
                payload=dispatch.payload,
                provider_message_id=provider_message_id,
            )
        except Exception as exc:
            return NotificationDeliveryRead(
                dispatch_key=dispatch.dispatch_key,
                channel=dispatch.channel,
                status=NotificationDeliveryStatus.FAILED,
                payload=dispatch.payload,
                error_message=str(exc),
            )

    async def deliver_dispatches(self, dispatches: list[NotificationDispatchRead]) -> list[NotificationDeliveryRead]:
        deliveries: list[NotificationDeliveryRead] = []
        for dispatch in dispatches:
            deliveries.append(await self.deliver_dispatch(dispatch))
        return deliveries

    async def close(self) -> None:
        if self.telegram_private_adapter is None or not self._owns_telegram_private_adapter:
            return
        await self.telegram_private_adapter.close()

    def _get_telegram_private_adapter(self) -> TelegramPrivateDeliveryAdapter:
        if self.telegram_private_adapter is None:
            self.telegram_private_adapter = AiogramTelegramPrivateDeliveryAdapter.from_settings()
        return self.telegram_private_adapter

    @staticmethod
    def render_dispatch_text(dispatch: NotificationDispatchRead) -> str:
        return f"{dispatch.payload.title}\n\n{dispatch.payload.message}"
