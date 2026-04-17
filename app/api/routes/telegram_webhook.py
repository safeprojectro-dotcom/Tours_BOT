"""
Telegram Bot API webhook: POST updates from Telegram to the same aiogram dispatcher as dev polling.

Path: POST /telegram/webhook
Security: optional X-Telegram-Bot-Api-Secret-Token when TELEGRAM_WEBHOOK_SECRET is set.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.methods import TelegramMethod
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Public path on the API service (single source of truth for docs + CLI).
TELEGRAM_WEBHOOK_HTTP_PATH = "/telegram/webhook"

router = APIRouter(prefix="/telegram", tags=["telegram-bot"])


class TelegramWebhookAck(BaseModel):
    ok: bool = Field(default=True, description="Acknowledged for Telegram delivery.")


def _verify_webhook_secret(header_token: str | None, expected: str | None) -> bool:
    """Match Telegram's secret_token header; if no secret configured, accept (dev only)."""
    if not expected:
        return True
    if header_token is None:
        return False
    return secrets.compare_digest(header_token, expected)


def _log_temp_channel_post_chat_debug(payload: dict[str, Any]) -> None:
    """
    TEMPORARY — remove after TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID is confirmed.

    Logs channel identity for `channel_post` / `edited_channel_post` updates only.
    Does not branch on content or alter dispatch.
    """
    for update_type in ("channel_post", "edited_channel_post"):
        if update_type not in payload:
            continue
        inner = payload.get(update_type)
        if not isinstance(inner, dict):
            continue
        chat = inner.get("chat")
        if not isinstance(chat, dict):
            continue
        logger.info(
            "TEMP_DEBUG_SHOWCASE_CHANNEL update_type=%s chat.id=%s chat.title=%r chat.type=%s",
            update_type,
            chat.get("id"),
            chat.get("title"),
            chat.get("type"),
        )


async def _process_update(dispatcher: Dispatcher, bot: Bot, payload: dict[str, Any]) -> None:
    try:
        result = await dispatcher.feed_raw_update(bot=bot, update=payload)
        if isinstance(result, TelegramMethod):
            await dispatcher.silent_call_request(bot=bot, result=result)
    except Exception:
        logger.exception("telegram webhook: failed to process update")


@router.post("/webhook", response_model=TelegramWebhookAck)
async def receive_telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> TelegramWebhookAck:
    """
    Receives JSON Update objects from Telegram.

    Updates are processed in a background task (same pattern as aiogram SimpleRequestHandler
    with handle_in_background=True) so the HTTP response returns quickly.
    """
    settings = get_settings()
    bot: Bot | None = getattr(request.app.state, "telegram_bot", None)
    dispatcher: Dispatcher | None = getattr(request.app.state, "telegram_dispatcher", None)

    if not settings.telegram_bot_token or bot is None or dispatcher is None:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot is not configured (TELEGRAM_BOT_TOKEN missing on API service).",
        )

    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not _verify_webhook_secret(header, settings.telegram_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid or missing webhook secret token.")

    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Update payload must be a JSON object.")

    _log_temp_channel_post_chat_debug(payload)

    background_tasks.add_task(_process_update, dispatcher, bot, payload)
    return TelegramWebhookAck()
