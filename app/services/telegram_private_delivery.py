from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from aiogram import Bot

from app.core.config import Settings, get_settings


class TelegramPrivateDeliveryAdapter(Protocol):
    async def send_message(self, *, telegram_user_id: int, text: str) -> str | None: ...

    async def close(self) -> None: ...


class AiogramTelegramPrivateDeliveryAdapter:
    def __init__(self, *, bot: Bot) -> None:
        self.bot = bot

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "AiogramTelegramPrivateDeliveryAdapter":
        from aiogram import Bot

        resolved_settings = settings or get_settings()
        if not resolved_settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN must be set before sending telegram_private notifications.")
        return cls(bot=Bot(token=resolved_settings.telegram_bot_token))

    async def send_message(self, *, telegram_user_id: int, text: str) -> str | None:
        response = await self.bot.send_message(chat_id=telegram_user_id, text=text)
        return str(response.message_id)

    async def close(self) -> None:
        await self.bot.session.close()
