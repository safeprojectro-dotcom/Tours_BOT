"""Showcase channel adapter boundary (B13B): transport I/O separate from content assembly.

``TelegramShowcaseChannelAdapter`` wraps :func:`telegram_showcase_client.send_showcase_publication`
with no behavior change vs calling it directly from moderation publish.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.services.supplier_offer_showcase_message import ShowcasePublication

TELEGRAM_SHOWCASE_PROVIDER = "telegram_showcase_channel"


@dataclass(frozen=True)
class ShowcaseChannelPublishRequest:
    """Neutral input to a channel adapter (B13). ``channel_ref`` is provider-specific (e.g. Telegram chat id)."""

    offer_id: int
    publication: ShowcasePublication
    channel_ref: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class ShowcaseChannelPublishResult:
    """Provider-specific publish receipt. ``message_id`` is an opaque string (Telegram uses decimal id)."""

    provider: str
    chat_id: str | None
    message_id: str | None
    raw_reference: str | None = None


class ShowcaseChannelAdapter(Protocol):
    def publish(self, request: ShowcaseChannelPublishRequest) -> ShowcaseChannelPublishResult:
        """Send ``request.publication`` to the channel. Telegram raises ``TelegramShowcaseSendError`` on Bot API failure."""


class TelegramShowcaseChannelAdapter:
    """Telegram Bot API implementation: same calls as pre-B13B :func:`telegram_showcase_client.send_showcase_publication` path."""

    def __init__(self, *, settings: Settings) -> None:
        self._settings = settings

    def publish(self, request: ShowcaseChannelPublishRequest) -> ShowcaseChannelPublishResult:
        from app.services.telegram_showcase_client import send_showcase_publication

        chat_id = (request.channel_ref or "").strip()
        token = (self._settings.telegram_bot_token or "").strip()
        mid = send_showcase_publication(
            bot_token=token,
            chat_id=chat_id,
            caption_html=request.publication.caption_html,
            photo_url=request.publication.photo_url,
        )
        return ShowcaseChannelPublishResult(
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            chat_id=chat_id,
            message_id=str(mid),
            raw_reference=None,
        )


def default_telegram_showcase_adapter(settings: Settings) -> TelegramShowcaseChannelAdapter:
    """Factory for the sole shipped showcase adapter (Telegram channel)."""
    return TelegramShowcaseChannelAdapter(settings=settings)


def telegram_showcase_channel_publish_request_preview(
    offer_id: int,
    publication: ShowcasePublication,
    *,
    settings: Settings,
) -> ShowcaseChannelPublishRequest:
    """Build the Telegram-channel ``ShowcaseChannelPublishRequest`` that publish would use (read-only / no I/O)."""
    channel_id = (settings.telegram_offer_showcase_channel_id or "").strip() or None
    return ShowcaseChannelPublishRequest(
        offer_id=offer_id,
        publication=publication,
        channel_ref=channel_id,
        idempotency_key=None,
    )
