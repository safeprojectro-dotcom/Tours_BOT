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
# Reusable home row + catalog list (two Telegram messages; Step 12B edit-or-replace)
HOME_MESSAGE = "home_message"
CATALOG_MESSAGE = "catalog_message"

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


async def _clear_language_and_filter_prompts(bot: Bot, chat_id: int) -> None:
    for cat in (LANGUAGE_PROMPT, FILTER_STEP):
        await _pop_and_delete(bot, chat_id, cat)


async def register_catalog_bundle(bot: Bot, chat_id: int, welcome_message_id: int, list_message_id: int) -> None:
    """
    Replace the previous home/catalog pair and clear stale language picker + filter prompts
    so browse flows do not stack duplicates.
    """
    for cat in (LANGUAGE_PROMPT, FILTER_STEP, HOME_MESSAGE, CATALOG_MESSAGE):
        await _pop_and_delete(bot, chat_id, cat)
    d = _store.setdefault(chat_id, {})
    d[HOME_MESSAGE] = welcome_message_id
    d[CATALOG_MESSAGE] = list_message_id


async def send_or_edit_home_catalog_pair(
    message: Message,
    *,
    welcome_text: str,
    welcome_markup: Any,
    catalog_text: str,
    catalog_markup: Any,
    prefer_edit: bool,
) -> None:
    """
    When prefer_edit: try to update the last registered home + catalog bot messages in chat.
    On any edit failure (or missing ids), delete tracked ids if needed and fall back to send + register.
    When not prefer_edit: always send two new messages and register (same as before Step 12B).
    """
    bot = message.bot
    chat_id = message.chat.id

    if prefer_edit:
        bucket = _store.get(chat_id)
        hid = bucket.get(HOME_MESSAGE) if bucket else None
        cid = bucket.get(CATALOG_MESSAGE) if bucket else None
        if hid is not None and cid is not None:
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=hid,
                    text=welcome_text,
                    reply_markup=welcome_markup,
                )
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=cid,
                    text=catalog_text,
                    reply_markup=catalog_markup,
                )
                await _clear_language_and_filter_prompts(bot, chat_id)
                return
            except Exception:
                logger.debug(
                    "edit home/catalog failed chat_id=%s hid=%s cid=%s; fallback send",
                    chat_id,
                    hid,
                    cid,
                    exc_info=True,
                )
                b = _store.get(chat_id)
                if b:
                    for mid in (hid, cid):
                        await _delete_silently(bot, chat_id, mid)
                    b.pop(HOME_MESSAGE, None)
                    b.pop(CATALOG_MESSAGE, None)
                    if not b:
                        _store.pop(chat_id, None)

    sent_w = await message.answer(welcome_text, reply_markup=welcome_markup)
    sent_c = await message.answer(catalog_text, reply_markup=catalog_markup)
    await register_catalog_bundle(bot, chat_id, sent_w.message_id, sent_c.message_id)


async def answer_and_register_language_prompt(message: Message, text: str, reply_markup: Any = None) -> Message:
    sent = await message.answer(text, reply_markup=reply_markup)
    await register_transient(message.bot, message.chat.id, LANGUAGE_PROMPT, sent.message_id)
    return sent


async def answer_and_register_filter_step(message: Message, text: str, reply_markup: Any = None) -> Message:
    sent = await message.answer(text, reply_markup=reply_markup)
    await register_transient(message.bot, message.chat.id, FILTER_STEP, sent.message_id)
    return sent
