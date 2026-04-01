from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Initialize aiogram Bot + Dispatcher when TELEGRAM_BOT_TOKEN is set (webhook mode on API process)."""
    settings = get_settings()
    app.state.telegram_bot = None
    app.state.telegram_dispatcher = None
    if settings.telegram_bot_token:
        from aiogram import Bot

        from app.bot.app import create_dispatcher

        bot = Bot(token=settings.telegram_bot_token)
        dispatcher = create_dispatcher()
        await dispatcher.emit_startup(bot=bot, dispatcher=dispatcher, bots=[bot])
        app.state.telegram_bot = bot
        app.state.telegram_dispatcher = dispatcher
    yield
    bot = getattr(app.state, "telegram_bot", None)
    dispatcher = getattr(app.state, "telegram_dispatcher", None)
    if bot is not None and dispatcher is not None:
        await dispatcher.emit_shutdown(bot=bot, dispatcher=dispatcher, bots=[bot])
        await bot.session.close()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=_lifespan,
    )
    if settings.app_debug or settings.app_env.lower() == "local":
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router)
    return app


app = create_app()
