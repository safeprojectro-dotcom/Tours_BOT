"""Minimal handoff persistence for support entry points (no operator notification yet)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.models.order import Order
from app.repositories.handoff import HandoffRepository


class HandoffEntryService:
    """Creates `handoffs` rows for MVP support signals; does not notify operators."""

    REASON_PRIVATE_CONTACT = "private_chat_contact"
    REASON_PRIVATE_HUMAN = "private_chat_human_request"
    REASON_MINI_APP_PREFIX = "mini_app_support"

    def __init__(
        self,
        *,
        handoff_repository: HandoffRepository | None = None,
    ) -> None:
        self._handoffs = handoff_repository or HandoffRepository()

    def _user_sync(self) -> TelegramUserContextService:
        settings = get_settings()
        return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)

    def create_for_telegram_user(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        reason: str,
        order_id: int | None = None,
        priority: str = "normal",
        telegram_language_code: str | None = None,
    ) -> int | None:
        """
        Persist a handoff row. Returns handoff id, or None if user could not be resolved
        or order ownership does not match.
        """
        user = self._user_sync().sync_private_user(
            session,
            telegram_user_id=telegram_user_id,
            username=None,
            first_name=None,
            last_name=None,
            telegram_language_code=telegram_language_code,
        )
        if order_id is not None:
            order = session.get(Order, order_id)
            if order is None or order.user_id != user.id:
                return None

        safe_reason = (reason or "support")[:255]
        row = self._handoffs.create(
            session,
            data={
                "user_id": user.id,
                "order_id": order_id,
                "reason": safe_reason,
                "priority": priority[:32] if priority else "normal",
                "status": "open",
                "assigned_operator_id": None,
            },
        )
        return row.id
