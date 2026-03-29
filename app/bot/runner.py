from __future__ import annotations

import asyncio

from aiogram import Bot

from app.bot.app import create_dispatcher
from app.core.config import get_settings
from app.core.logging import configure_logging


async def run_polling() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN must be set before starting the bot process.")

    configure_logging(settings.log_level)
    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=False)
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
