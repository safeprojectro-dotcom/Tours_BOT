"""Send showcase messages via Telegram Bot API (sync httpx)."""

from __future__ import annotations

from typing import Any

import httpx


class TelegramShowcaseSendError(Exception):
    def __init__(self, message: str, *, telegram_description: str | None = None) -> None:
        self.telegram_description = telegram_description
        super().__init__(message)


def send_channel_html_message(*, bot_token: str, chat_id: str, text: str, timeout_s: float = 30.0) -> int:
    """POST sendMessage; return message_id. Raises TelegramShowcaseSendError on failure."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise TelegramShowcaseSendError(f"telegram_http_error: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise TelegramShowcaseSendError(f"telegram_invalid_json: {response.text[:200]}") from exc

    if response.status_code != 200 or not data.get("ok"):
        desc = data.get("description") if isinstance(data, dict) else None
        raise TelegramShowcaseSendError(
            f"telegram_send_failed: {desc or response.text[:200]}",
            telegram_description=str(desc) if desc else None,
        )
    result = data.get("result") or {}
    mid = result.get("message_id")
    if mid is None:
        raise TelegramShowcaseSendError("telegram_missing_message_id")
    return int(mid)
