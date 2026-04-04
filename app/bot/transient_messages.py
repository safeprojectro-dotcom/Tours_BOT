"""
Best-effort deletion of previous bot messages in the same category (private chat hygiene).

In-memory only — resets on process restart. No DB migrations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiogram import Bot

from aiogram.types import Message

logger = logging.getLogger(__name__)

# One active language-picker message per chat
LANGUAGE_PROMPT = "language_prompt"
# Date / destination / budget prompt — single slot so prompts replace each other
FILTER_STEP = "filter_step"
# Welcome + catalog list (two Telegram messages)
CATALOG_WELCOME = "catalog_welcome"
CATALOG_LIST = "catalog_list"

# chat_id -> category -> message_id
_store: dict[int, dict[str, int]] = {}


async def _delete_silently(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        logger.debug("delete_message skipped chat_id=%s message_id=%s", chat_id, message_id)


async def _pop_and_delete(bot: Bot, chat_id: int, category: str) -> None:
    bucket = _store.get(chat_id)
    if not bucket:
        return
    mid = bucket.pop(category, None)
    if mid is not None:
        await _delete_silently(bot, chat_id, mid)
    if not bucket:
        _store.pop(chat_id, None)


async def register_transient(bot: Bot, chat_id: int, category: str, message_id: int) -> None:
    """Store a new service message id; delete the previous one in the same category if any."""
    await _pop_and_delete(bot, chat_id, category)
    _store.setdefault(chat_id, {})[category] = message_id


async def register_catalog_bundle(bot: Bot, chat_id: int, welcome_message_id: int, list_message_id: int) -> None:
    """
    Replace the previous home/catalog pair and clear stale language picker + filter prompts
    so /start and /tours do not stack duplicates.
    """
    for cat in (LANGUAGE_PROMPT, FILTER_STEP, CATALOG_WELCOME, CATALOG_LIST):
        await _pop_and_delete(bot, chat_id, cat)
    d = _store.setdefault(chat_id, {})
    d[CATALOG_WELCOME] = welcome_message_id
    d[CATALOG_LIST] = list_message_id


async def answer_and_register_language_prompt(message: Message, text: str, reply_markup: Any = None) -> Message:
    sent = await message.answer(text, reply_markup=reply_markup)
    await register_transient(message.bot, message.chat.id, LANGUAGE_PROMPT, sent.message_id)
    return sent


async def answer_and_register_filter_step(message: Message, text: str, reply_markup: Any = None) -> Message:
    sent = await message.answer(text, reply_markup=reply_markup)
    await register_transient(message.bot, message.chat.id, FILTER_STEP, sent.message_id)
    return sent
