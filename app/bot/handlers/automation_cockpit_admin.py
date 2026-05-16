"""A1V: read-only Automation Cockpit in Telegram for allowlisted admins."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from app.bot.automation_cockpit_telegram import (
    cockpit_card_callback,
    cockpit_card_keyboard,
    cockpit_queue_from_abbrev,
    cockpit_queue_keyboard,
    cockpit_summary_keyboard,
    find_card_in_cockpit,
    format_cockpit_card_detail_text,
    format_cockpit_queue_text,
    format_cockpit_summary_text,
    parse_cockpit_card_callback,
)
from app.bot.constants import (
    ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_CLOSE,
    ADMIN_AUTOMATION_COCKPIT_HOME,
    ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_REFRESH,
    ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.admin_automation_cockpit_service import AdminAutomationCockpitService

logger = logging.getLogger(__name__)

router = Router(name="automation_cockpit_admin")


def _is_admin_allowed(telegram_user_id: int) -> bool:
    return telegram_user_id in set(get_settings().telegram_admin_allowlist_ids)


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _plain_trim(text: str, *, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


async def _deny_if_not_allowed(message: Message | CallbackQuery, *, language_code: str | None) -> bool:
    from_user = message.from_user
    if from_user is None or _is_admin_allowed(from_user.id):
        return False
    text = translate(language_code, "admin_offer_gate_denied")
    if isinstance(message, CallbackQuery):
        if message.message is not None:
            await message.message.answer(text)
        await message.answer()
    else:
        await message.answer(text)
    return True


async def _resolve_language(telegram_user_id: int, telegram_language_code: str | None) -> str | None:
    with SessionLocal() as session:
        return _user_service().resolve_language(
            session,
            telegram_user_id=telegram_user_id,
            telegram_language_code=telegram_language_code,
        )


async def _edit_or_answer(
    *,
    query: CallbackQuery | None,
    message: Message | None,
    text: str,
    reply_markup,
) -> None:
    trimmed = _plain_trim(text)
    if query is not None and query.message is not None:
        try:
            await query.message.edit_text(trimmed, reply_markup=reply_markup)
            return
        except TelegramBadRequest as exc:
            logger.debug("cockpit edit_text fallback: %s", exc)
            await query.message.answer(trimmed, reply_markup=reply_markup)
        return
    if message is not None:
        await message.answer(trimmed, reply_markup=reply_markup)


def _load_summary_read():
    with SessionLocal() as session:
        return AdminAutomationCockpitService().read_cockpit(session, materialize_cards=False, limit_per_queue=5)


def _load_queue_read(queue_code: str):
    with SessionLocal() as session:
        return AdminAutomationCockpitService().read_cockpit(
            session,
            materialize_cards=True,
            include_queues=frozenset({queue_code}),
            limit_per_queue=5,
        )


def _load_card_read(queue_code: str):
    with SessionLocal() as session:
        return AdminAutomationCockpitService().read_cockpit(
            session,
            materialize_cards=True,
            include_queues=frozenset({queue_code}),
            limit_per_queue=80,
        )


@router.message(Command("admin_cockpit"))
async def cmd_admin_cockpit(message: Message) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _deny_if_not_allowed(message, language_code=lg):
        return
    read = _load_summary_read()
    await message.answer(
        _plain_trim(format_cockpit_summary_text(lg, read)),
        reply_markup=cockpit_summary_keyboard(lg).as_markup(),
    )


@router.callback_query(F.data == ADMIN_AUTOMATION_COCKPIT_HOME)
async def cb_cockpit_home(query: CallbackQuery) -> None:
    if query.from_user is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    read = _load_summary_read()
    await _edit_or_answer(
        query=query,
        message=None,
        text=format_cockpit_summary_text(lg, read),
        reply_markup=cockpit_summary_keyboard(lg).as_markup(),
    )
    await query.answer()


@router.callback_query(F.data == ADMIN_AUTOMATION_COCKPIT_REFRESH)
async def cb_cockpit_refresh_home(query: CallbackQuery) -> None:
    if query.from_user is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    read = _load_summary_read()
    await _edit_or_answer(
        query=query,
        message=None,
        text=format_cockpit_summary_text(lg, read),
        reply_markup=cockpit_summary_keyboard(lg).as_markup(),
    )
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX))
async def cb_cockpit_refresh_queue(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    abbrev = query.data.removeprefix(ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX)
    queue_code = cockpit_queue_from_abbrev(abbrev)
    if queue_code is None:
        await query.answer(translate(lg, "admin_automation_cockpit_queue_missing"), show_alert=True)
        return
    read = _load_queue_read(queue_code)
    await _edit_or_answer(
        query=query,
        message=None,
        text=format_cockpit_queue_text(lg, read, queue_code=queue_code),
        reply_markup=cockpit_queue_keyboard(lg, read, queue_code=queue_code).as_markup(),
    )
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX))
async def cb_cockpit_queue(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    abbrev = query.data.removeprefix(ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX)
    queue_code = cockpit_queue_from_abbrev(abbrev)
    if queue_code is None:
        await query.answer(translate(lg, "admin_automation_cockpit_queue_missing"), show_alert=True)
        return
    read = _load_queue_read(queue_code)
    await _edit_or_answer(
        query=query,
        message=None,
        text=format_cockpit_queue_text(lg, read, queue_code=queue_code),
        reply_markup=cockpit_queue_keyboard(lg, read, queue_code=queue_code).as_markup(),
    )
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_CLOSE))
async def cb_cockpit_close(query: CallbackQuery) -> None:
    if query.from_user is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    if query.message is not None:
        try:
            await query.message.delete()
        except TelegramBadRequest:
            await query.message.answer(translate(lg, "admin_offer_workspace_home"))
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX))
async def cb_cockpit_card(query: CallbackQuery) -> None:
    """Card open/refresh: ``ac:c:<q>:<st>:<id>``."""
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    parsed = parse_cockpit_card_callback(query.data)
    if parsed is None:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    queue_code, source_type, source_id = parsed
    read = _load_card_read(queue_code)
    card = find_card_in_cockpit(read, queue_code=queue_code, source_type=source_type, source_id=source_id)
    if card is None:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    refresh_cb = cockpit_card_callback(queue_code, source_type, source_id)
    await _edit_or_answer(
        query=query,
        message=None,
        text=format_cockpit_card_detail_text(lg, card),
        reply_markup=cockpit_card_keyboard(
            lg,
            queue_code=queue_code,
            card_refresh_callback=refresh_cb,
        ).as_markup(),
    )
    await query.answer()
