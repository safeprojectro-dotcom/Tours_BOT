"""Narrow group chat handler — trigger gating + short safe reply + private CTA link (Phase 7 / Steps 3–5).

Uses ``resolve_group_trigger_ack_reply`` (group trigger + optional handoff-category reply shaping +
deep link; **no** handoff persistence). Private chat is unchanged (``private_entry`` filters to private).

Without ``TELEGRAM_BOT_USERNAME``, the resolver stays silent in groups.
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
