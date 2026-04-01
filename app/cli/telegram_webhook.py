"""
Explicit Telegram setWebhook / deleteWebhook / getWebhookInfo (no auto-registration in app startup).

Usage (from repo root, with .env loaded):

  python -m app.cli.telegram_webhook set
  python -m app.cli.telegram_webhook info
  python -m app.cli.telegram_webhook delete
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from aiogram import Bot
from aiogram.methods import DeleteWebhook, GetWebhookInfo, SetWebhook

from app.api.routes.telegram_webhook import TELEGRAM_WEBHOOK_HTTP_PATH
from app.core.config import get_settings


def _build_webhook_url() -> str:
    settings = get_settings()
    if not settings.telegram_webhook_base_url:
        raise SystemExit(
            "TELEGRAM_WEBHOOK_BASE_URL is required for 'set' (public HTTPS origin of this API, no trailing slash).",
        )
    base = settings.telegram_webhook_base_url.strip().rstrip("/")
    return f"{base}{TELEGRAM_WEBHOOK_HTTP_PATH}"


async def _cmd_set() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN must be set.")
    url = _build_webhook_url()
    secret = (settings.telegram_webhook_secret or "").strip() or None
    bot = Bot(token=settings.telegram_bot_token)
    try:
        # secret_token: Telegram sends X-Telegram-Bot-Api-Secret-Token; must match [A-Za-z0-9_-]{1,256}
        await bot(SetWebhook(url=url, secret_token=secret, drop_pending_updates=False))
        print(f"setWebhook OK: {url}")
        if secret:
            print("secret_token: configured (header required on incoming requests)")
        else:
            print("warning: secret_token not set — staging/prod should set TELEGRAM_WEBHOOK_SECRET")
    finally:
        await bot.session.close()


async def _cmd_delete() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN must be set.")
    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot(DeleteWebhook(drop_pending_updates=False))
        print("deleteWebhook OK (polling can be used locally after this).")
    finally:
        await bot.session.close()


async def _cmd_info() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN must be set.")
    bot = Bot(token=settings.telegram_bot_token)
    try:
        info = await bot(GetWebhookInfo())
        print(f"url: {info.url!r}")
        print(f"has_custom_certificate: {info.has_custom_certificate}")
        print(f"pending_update_count: {info.pending_update_count}")
        if info.last_error_date:
            print(f"last_error_date: {info.last_error_date}")
        if info.last_error_message:
            print(f"last_error_message: {info.last_error_message}")
        if info.max_connections is not None:
            print(f"max_connections: {info.max_connections}")
    finally:
        await bot.session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram webhook operations (explicit, manual).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("set", help=f"Register webhook at TELEGRAM_WEBHOOK_BASE_URL + {TELEGRAM_WEBHOOK_HTTP_PATH}")
    sub.add_parser("delete", help="Remove webhook (use before local polling)")
    sub.add_parser("info", help="Print getWebhookInfo")
    args = parser.parse_args()

    if args.command == "set":
        asyncio.run(_cmd_set())
    elif args.command == "delete":
        asyncio.run(_cmd_delete())
    elif args.command == "info":
        asyncio.run(_cmd_info())
    else:  # pragma: no cover
        parser.error("unknown command")
        sys.exit(2)


if __name__ == "__main__":
    main()
