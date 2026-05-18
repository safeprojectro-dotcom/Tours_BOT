"""S1D-2: admin-gated operational sales push to Telegram channel (re-check eligibility before send)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.schemas.admin_operational_sales_push_publish import AdminOperationalSalesPushChannelPublishResultRead
from app.services.admin_operational_sales_push_preview_service import (
    AdminOperationalSalesPushPreviewService,
    channel_plain_text_for_operational_sales_push_read,
)
from app.services.telegram_showcase_client import (
    TelegramShowcaseSendError,
    send_channel_plain_message,
)

logger = logging.getLogger(__name__)


class OperationalSalesPushPublishTourNotFoundError(Exception):
    pass


class OperationalSalesPushPublishNotEligibleError(Exception):
    def __init__(self, *, block_codes: list[str]) -> None:
        self.block_codes = list(block_codes)
        super().__init__("operational_sales_push_not_eligible")


class OperationalSalesPushPublishConfigError(Exception):
    """Bot token or channel chat id missing from configuration."""


class AdminOperationalSalesPushPublishService:
    """S1D-2: re-run S1D-1 preview; if still eligible, post plain text to showcase channel."""

    _ACTOR_SURFACE = "s1d2_admin_operational_sales_push_channel_publish"

    def __init__(
        self,
        *,
        preview: AdminOperationalSalesPushPreviewService | None = None,
    ) -> None:
        self._preview = preview or AdminOperationalSalesPushPreviewService()

    def _channel_chat_id(self, settings: Settings) -> str | None:
        return (settings.telegram_offer_showcase_channel_id or "").strip() or None

    def publish_for_tour(
        self,
        session: Session,
        *,
        tour_id: int,
        settings: Settings | None = None,
    ) -> AdminOperationalSalesPushChannelPublishResultRead:
        cfg = settings or get_settings()
        token = (cfg.telegram_bot_token or "").strip()
        chat_id = self._channel_chat_id(cfg)
        if not token or not chat_id:
            raise OperationalSalesPushPublishConfigError()

        read = self._preview.read_for_tour(session, tour_id=tour_id)
        if read is None:
            raise OperationalSalesPushPublishTourNotFoundError()

        if not read.eligible_for_operational_sales_push_preview:
            raise OperationalSalesPushPublishNotEligibleError(block_codes=list(read.eligibility_block_codes))

        text = channel_plain_text_for_operational_sales_push_read(read)
        if not text:
            raise OperationalSalesPushPublishNotEligibleError(block_codes=["operational_sales_push_empty_channel_text"])

        try:
            message_id = send_channel_plain_message(
                bot_token=token,
                chat_id=chat_id,
                text=text,
            )
        except TelegramShowcaseSendError as exc:
            logger.exception(
                "s1d2_operational_sales_push_channel_send_failed",
                extra={"tour_id": tour_id, "actor_surface": self._ACTOR_SURFACE},
            )
            raise exc

        logger.info(
            "s1d2_operational_sales_push_published",
            extra={
                "tour_id": tour_id,
                "telegram_message_id": message_id,
                "telegram_chat_id": chat_id,
                "actor_surface": self._ACTOR_SURFACE,
            },
        )

        return AdminOperationalSalesPushChannelPublishResultRead(
            tour_id=read.tour_id,
            telegram_message_id=message_id,
            telegram_chat_id=chat_id,
            message_plain_sent=text,
            eligibility_recheck=read,
        )
