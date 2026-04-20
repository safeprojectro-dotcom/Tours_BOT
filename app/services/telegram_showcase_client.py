"""Send showcase messages via Telegram Bot API (sync httpx)."""

from __future__ import annotations

from typing import Any

import httpx


class TelegramShowcaseSendError(Exception):
    def __init__(self, message: str, *, telegram_description: str | None = None) -> None:
        self.telegram_description = telegram_description
        super().__init__(message)


def _post_telegram_api(
    *,
    bot_token: str,
    method: str,
    payload: dict[str, Any],
    timeout_s: float,
) -> int:
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
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


def send_channel_html_message(*, bot_token: str, chat_id: str, text: str, timeout_s: float = 30.0) -> int:
    """POST sendMessage; return message_id. Raises TelegramShowcaseSendError on failure."""
    return _post_telegram_api(
        bot_token=bot_token,
        method="sendMessage",
        payload={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout_s=timeout_s,
    )


def send_private_text_message(*, bot_token: str, telegram_user_id: int, text: str, timeout_s: float = 30.0) -> int:
    """POST sendMessage to private user chat; return message_id."""
    return _post_telegram_api(
        bot_token=bot_token,
        method="sendMessage",
        payload={
            "chat_id": str(telegram_user_id),
            "text": text,
        },
        timeout_s=timeout_s,
    )


def delete_channel_message(
    *,
    bot_token: str,
    chat_id: str,
    message_id: int,
    timeout_s: float = 30.0,
) -> bool:
    """Best-effort deleteMessage for a channel post; return Telegram result bool."""
    url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                },
            )
    except httpx.HTTPError as exc:
        raise TelegramShowcaseSendError(f"telegram_http_error: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise TelegramShowcaseSendError(f"telegram_invalid_json: {response.text[:200]}") from exc

    if response.status_code != 200 or not data.get("ok"):
        desc = data.get("description") if isinstance(data, dict) else None
        raise TelegramShowcaseSendError(
            f"telegram_delete_failed: {desc or response.text[:200]}",
            telegram_description=str(desc) if desc else None,
        )
    return bool(data.get("result"))


def send_channel_photo(
    *,
    bot_token: str,
    chat_id: str,
    photo: str,
    caption: str,
    timeout_s: float = 30.0,
) -> int:
    """POST sendPhoto with HTML caption (max 1024 chars per Bot API)."""
    cap = caption if len(caption) <= 1024 else caption[:1023] + "…"
    return _post_telegram_api(
        bot_token=bot_token,
        method="sendPhoto",
        payload={
            "chat_id": chat_id,
            "photo": photo,
            "caption": cap,
            "parse_mode": "HTML",
        },
        timeout_s=timeout_s,
    )


def send_showcase_publication(
    *,
    bot_token: str,
    chat_id: str,
    caption_html: str,
    photo_url: str | None,
    timeout_s: float = 30.0,
) -> int:
    """Photo + caption when ``photo_url`` is set; otherwise text-only sendMessage."""
    safe_photo = (photo_url or "").strip()
    if safe_photo:
        return send_channel_photo(
            bot_token=bot_token,
            chat_id=chat_id,
            photo=safe_photo,
            caption=caption_html,
            timeout_s=timeout_s,
        )
    return send_channel_html_message(
        bot_token=bot_token,
        chat_id=chat_id,
        text=caption_html,
        timeout_s=timeout_s,
    )
