"""Narrow group chat handler — trigger gating + short ack only (Phase 7 / Step 3).

Integration point: ``create_dispatcher`` includes this router. Private chat is unchanged
(``private_entry`` router filters to ``chat.type == private``).

Without ``TELEGRAM_BOT_USERNAME``, mention triggers are skipped by ``resolve_group_trigger_ack_reply``;
configure it for staging/production group behavior.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.core.config import get_settings
from app.services.group_chat_gating import resolve_group_trigger_ack_reply

router = Router(name="group-gating")
router.message.filter(
    F.chat.type.in_({"group", "supergroup"}),
    F.text,
)


@router.message()
async def group_text_trigger_gating(message: Message) -> None:
    settings = get_settings()
    text = message.text or ""
    reply = resolve_group_trigger_ack_reply(text, bot_username=settings.telegram_bot_username)
    if reply is None:
        return
    await message.reply(reply)
