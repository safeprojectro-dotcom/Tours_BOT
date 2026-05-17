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
    cockpit_outbox_list_callback,
    cockpit_outbox_list_keyboard,
    cockpit_outbox_item_detail_keyboard,
    cockpit_queue_from_abbrev,
    cockpit_queue_keyboard,
    cockpit_safety_detail_keyboard,
    cockpit_summary_keyboard,
    find_card_in_cockpit,
    format_cockpit_card_detail_text,
    format_cockpit_clarification_outbox_item_detail_text,
    format_cockpit_clarification_outbox_list_text,
    format_cockpit_queue_text,
    format_cockpit_safety_detail_text,
    format_cockpit_summary_text,
    parse_cockpit_card_callback,
    parse_cockpit_outbox_item_callback,
    parse_cockpit_outbox_list_callback,
    parse_cockpit_outbox_save_callback,
    parse_cockpit_outbox_status_callback,
    outbox_status_verb_to_workflow,
)
from app.bot.constants import (
    ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_CLOSE,
    ADMIN_AUTOMATION_COCKPIT_HOME,
    ADMIN_AUTOMATION_COCKPIT_OUTBOX_ITEM_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_OUTBOX_LIST_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_OUTBOX_SAVE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_OUTBOX_STATUS_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_REFRESH,
    ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_SAFETY_DETAIL,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.admin_automation_cockpit_service import AdminAutomationCockpitService
from app.schemas.supplier_clarification_outbox import SupplierClarificationOutboxStatusPatchRequest
from app.services.supplier_clarification_outbox_service import (
    SupplierClarificationOutboxInvalidTransitionError,
    SupplierClarificationOutboxItemNotFoundError,
    SupplierClarificationOutboxOfferNotFoundError,
    SupplierClarificationOutboxService,
)

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


async def _present_outbox_item_detail(
    query: CallbackQuery,
    *,
    language_code: str,
    queue_code: str,
    card_source_type: str,
    supplier_offer_id: int,
    item_id: int,
) -> bool:
    """Render item detail; returns False if the item is missing or does not belong to the offer."""
    refresh_cb = cockpit_card_callback(queue_code, card_source_type, supplier_offer_id)
    list_cb = cockpit_outbox_list_callback(queue_code, card_source_type, supplier_offer_id)
    with SessionLocal() as session:
        try:
            item = SupplierClarificationOutboxService().get_by_id(session, item_id=item_id)
        except SupplierClarificationOutboxItemNotFoundError:
            return False
    if item.supplier_offer_id != supplier_offer_id:
        return False
    body = format_cockpit_clarification_outbox_item_detail_text(
        language_code,
        supplier_offer_id=supplier_offer_id,
        item=item,
    )
    kb = cockpit_outbox_item_detail_keyboard(
        language_code,
        queue_code=queue_code,
        card_source_type=card_source_type,
        supplier_offer_id=supplier_offer_id,
        item=item,
        list_callback=list_cb,
        card_refresh_callback=refresh_cb,
    )
    await _edit_or_answer(query=query, message=None, text=body, reply_markup=kb.as_markup())
    return True


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


@router.callback_query(F.data == ADMIN_AUTOMATION_COCKPIT_SAFETY_DETAIL)
async def cb_cockpit_safety_detail(query: CallbackQuery) -> None:
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
        text=format_cockpit_safety_detail_text(lg, read),
        reply_markup=cockpit_safety_detail_keyboard(lg).as_markup(),
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
            card=card,
        ).as_markup(),
    )
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_OUTBOX_SAVE_PREFIX))
async def cb_cockpit_clarification_outbox_save(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    parsed = parse_cockpit_outbox_save_callback(query.data)
    if parsed is None:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    queue_code, source_type, source_id = parsed
    read = _load_card_read(queue_code)
    card = find_card_in_cockpit(read, queue_code=queue_code, source_type=source_type, source_id=source_id)
    if card is None or card.clarification_draft is None:
        await query.answer(translate(lg, "admin_automation_cockpit_outbox_save_failed"), show_alert=True)
        return
    try:
        with SessionLocal() as session:
            result = SupplierClarificationOutboxService().upsert_from_draft(
                session,
                draft=card.clarification_draft,
                created_by_telegram_user_id=query.from_user.id,
            )
            session.commit()
    except SupplierClarificationOutboxOfferNotFoundError:
        await query.answer(translate(lg, "admin_automation_cockpit_outbox_save_failed"), show_alert=True)
        return
    msg_key = (
        "admin_automation_cockpit_outbox_saved_replay"
        if result.replayed_existing
        else "admin_automation_cockpit_outbox_saved_new"
    )
    await query.answer(translate(lg, msg_key), show_alert=False)


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_OUTBOX_LIST_PREFIX))
async def cb_cockpit_clarification_outbox_list(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    parsed = parse_cockpit_outbox_list_callback(query.data)
    if parsed is None or parsed[1] != "supplier_offer":
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    queue_code, _source_type, source_id = parsed
    refresh_cb = cockpit_card_callback(queue_code, "supplier_offer", source_id)
    with SessionLocal() as session:
        items = SupplierClarificationOutboxService().list_for_supplier_offer(
            session,
            supplier_offer_id=source_id,
            limit=20,
        )
    body = format_cockpit_clarification_outbox_list_text(
        lg,
        supplier_offer_id=source_id,
        items=items,
    )
    await _edit_or_answer(
        query=query,
        message=None,
        text=body,
        reply_markup=cockpit_outbox_list_keyboard(
            lg,
            queue_code=queue_code,
            source_type="supplier_offer",
            supplier_offer_id=source_id,
            items=items,
            card_refresh_callback=refresh_cb,
        ).as_markup(),
    )
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_OUTBOX_ITEM_PREFIX))
async def cb_cockpit_clarification_outbox_item_detail(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    parsed = parse_cockpit_outbox_item_callback(query.data)
    if parsed is None or parsed[1] != "supplier_offer":
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    queue_code, card_source_type, offer_id, item_id = parsed
    ok = await _present_outbox_item_detail(
        query,
        language_code=lg,
        queue_code=queue_code,
        card_source_type=card_source_type,
        supplier_offer_id=offer_id,
        item_id=item_id,
    )
    if not ok:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    await query.answer()


@router.callback_query(F.data.startswith(ADMIN_AUTOMATION_COCKPIT_OUTBOX_STATUS_PREFIX))
async def cb_cockpit_clarification_outbox_status(query: CallbackQuery) -> None:
    if query.from_user is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _deny_if_not_allowed(query, language_code=lg):
        await query.answer()
        return
    parsed = parse_cockpit_outbox_status_callback(query.data)
    if parsed is None:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    queue_code, card_source_type, offer_id, item_id, verb = parsed
    if card_source_type != "supplier_offer":
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    target = outbox_status_verb_to_workflow(verb)
    if target is None:
        await query.answer(translate(lg, "admin_automation_cockpit_outbox_transition_denied"), show_alert=True)
        return
    patch_body = SupplierClarificationOutboxStatusPatchRequest(workflow_status=target)
    try:
        with SessionLocal() as session:
            SupplierClarificationOutboxService().apply_status_patch(
                session,
                item_id=item_id,
                body=patch_body,
                reviewed_by_telegram_user_id=query.from_user.id,
            )
            session.commit()
    except SupplierClarificationOutboxItemNotFoundError:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    except SupplierClarificationOutboxInvalidTransitionError:
        await query.answer(translate(lg, "admin_automation_cockpit_outbox_transition_denied"), show_alert=True)
        return
    ok = await _present_outbox_item_detail(
        query,
        language_code=lg,
        queue_code=queue_code,
        card_source_type=card_source_type,
        supplier_offer_id=offer_id,
        item_id=item_id,
    )
    if not ok:
        await query.answer(translate(lg, "admin_offer_no_current"), show_alert=True)
        return
    await query.answer(translate(lg, "admin_automation_cockpit_outbox_transition_ok"), show_alert=False)
