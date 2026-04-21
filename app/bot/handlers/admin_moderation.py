"""Y28.1: Telegram admin moderation workspace (narrow operational client)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ADMIN_OFFERS_ACTION_APPROVE,
    ADMIN_OFFERS_ACTION_CALLBACK_PREFIX,
    ADMIN_OFFERS_ACTION_PUBLISH,
    ADMIN_OFFERS_ACTION_REJECT,
    ADMIN_OFFERS_ACTION_RETRACT,
    ADMIN_OFFERS_NAV_BACK,
    ADMIN_OFFERS_NAV_HOME,
    ADMIN_OFFERS_NAV_NEXT,
    ADMIN_OFFERS_NAV_PREV,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.bot.state import AdminModerationState
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SupplierOfferLifecycle
from app.models.supplier import Supplier
from app.schemas.supplier_admin import SupplierOfferRead
from app.services.supplier_offer_execution_link_service import SupplierOfferExecutionLinkService
from app.services.supplier_offer_moderation_service import (
    SupplierOfferModerationNotFoundError,
    SupplierOfferModerationService,
    SupplierOfferModerationStateError,
    SupplierOfferPublicationConfigError,
)
from app.services.supplier_offer_supplier_notification_service import SupplierOfferSupplierNotificationService

router = Router(name="admin-moderation")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

_QUEUE_LIMIT = 20


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _is_admin_allowed(telegram_user_id: int) -> bool:
    return telegram_user_id in set(get_settings().telegram_admin_allowlist_ids)


def _status_key(status: SupplierOfferLifecycle) -> str:
    return f"supplier_offers_status_{status.value}"


def _action_button_rows(language_code: str | None, offer: SupplierOfferRead) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if offer.lifecycle_status == SupplierOfferLifecycle.READY_FOR_MODERATION:
        rows.append((translate(language_code, "admin_offer_action_approve"), f"{ADMIN_OFFERS_ACTION_APPROVE}:{offer.id}"))
        rows.append((translate(language_code, "admin_offer_action_reject"), f"{ADMIN_OFFERS_ACTION_REJECT}:{offer.id}"))
    if offer.lifecycle_status == SupplierOfferLifecycle.APPROVED:
        rows.append((translate(language_code, "admin_offer_action_publish"), f"{ADMIN_OFFERS_ACTION_PUBLISH}:{offer.id}"))
    if offer.lifecycle_status == SupplierOfferLifecycle.PUBLISHED:
        rows.append((translate(language_code, "admin_offer_action_retract"), f"{ADMIN_OFFERS_ACTION_RETRACT}:{offer.id}"))
    return rows


def _detail_keyboard(language_code: str | None, offer: SupplierOfferRead) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for title, action_payload in _action_button_rows(language_code, offer):
        kb.button(
            text=title,
            callback_data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{action_payload}",
        )
    kb.button(text=translate(language_code, "admin_offer_nav_prev"), callback_data=ADMIN_OFFERS_NAV_PREV)
    kb.button(text=translate(language_code, "admin_offer_nav_next"), callback_data=ADMIN_OFFERS_NAV_NEXT)
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.button(text=translate(language_code, "admin_offer_nav_home"), callback_data=ADMIN_OFFERS_NAV_HOME)
    kb.adjust(2, 2, 2)
    return kb


def _load_queue_ids(session) -> list[int]:
    items = SupplierOfferModerationService().list_offers(
        session,
        lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
        limit=_QUEUE_LIMIT,
        offset=0,
    )
    return [offer.id for offer in items]


def _queue_text(language_code: str | None, *, offers: list[SupplierOfferRead]) -> str:
    lines = [translate(language_code, "admin_offer_workspace_title", count=str(len(offers)))]
    for offer in offers:
        lines.append(f"#{offer.id} · {translate(language_code, _status_key(offer.lifecycle_status))} · {offer.title}")
    return "\n".join(lines)


def _offer_detail_text(session, language_code: str | None, *, offer: SupplierOfferRead) -> str:
    supplier = session.get(Supplier, offer.supplier_id)
    supplier_label = supplier.display_name if supplier is not None else f"#{offer.supplier_id}"
    publication_key = (
        "admin_offer_publication_active"
        if offer.lifecycle_status == SupplierOfferLifecycle.PUBLISHED
        else "admin_offer_publication_inactive"
    )
    lines = [
        translate(language_code, "admin_offer_detail_title", offer_id=str(offer.id)),
        translate(language_code, "admin_offer_detail_supplier", supplier=supplier_label),
        translate(language_code, "admin_offer_detail_lifecycle", status=translate(language_code, _status_key(offer.lifecycle_status))),
        translate(language_code, "admin_offer_detail_publication", status=translate(language_code, publication_key)),
        translate(language_code, "admin_offer_detail_route", description=offer.description),
        translate(
            language_code,
            "admin_offer_detail_schedule",
            departure=offer.departure_datetime.isoformat(timespec="minutes").replace("T", " "),
            return_at=offer.return_datetime.isoformat(timespec="minutes").replace("T", " "),
        ),
        translate(
            language_code,
            "admin_offer_detail_price",
            price=str(offer.base_price) if offer.base_price is not None else "-",
            currency=offer.currency or "-",
            seats=str(offer.seats_total),
        ),
    ]
    if offer.moderation_rejection_reason:
        lines.append(
            translate(
                language_code,
                "admin_offer_detail_reject_reason",
                reason=offer.moderation_rejection_reason,
            )
        )
    return "\n".join(lines)


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


async def _store_queue_state(state: FSMContext, *, queue_ids: list[int], queue_index: int, current_offer_id: int | None) -> None:
    await state.set_state(AdminModerationState.browsing_offer_queue)
    await state.update_data(
        queue_offer_ids=queue_ids,
        queue_index=queue_index,
        current_offer_id=current_offer_id,
    )


async def _show_current_offer(message: Message, state: FSMContext, *, language_code: str | None) -> None:
    data = await state.get_data()
    current_offer_id = data.get("current_offer_id")
    if not isinstance(current_offer_id, int):
        await message.answer(translate(language_code, "admin_offer_no_current"))
        return
    with SessionLocal() as session:
        offer_row = SupplierOfferModerationService()._offers.get_any(session, offer_id=current_offer_id)
        if offer_row is None:
            await message.answer(translate(language_code, "admin_offer_no_current"))
            return
        offer = SupplierOfferModerationService()._to_read(offer_row)
        detail_text = _offer_detail_text(session, language_code, offer=offer)
        await message.answer(detail_text, reply_markup=_detail_keyboard(language_code, offer).as_markup())


@router.message(Command("admin_ops", "admin_offers", "admin_queue"))
async def cmd_admin_offers(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    with SessionLocal() as session:
        user = _user_service().sync_private_user(
            session,
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            telegram_language_code=message.from_user.language_code,
        )
        session.commit()
        lg = user.preferred_language or message.from_user.language_code
    if await _deny_if_not_allowed(message, language_code=lg):
        await state.clear()
        return
    with SessionLocal() as session:
        queue_ids = _load_queue_ids(session)
        if not queue_ids:
            await state.clear()
            await message.answer(translate(lg, "admin_offer_workspace_empty"))
            return
        offers = [
            SupplierOfferModerationService()._to_read(row)
            for row in [SupplierOfferModerationService()._offers.get_any(session, offer_id=oid) for oid in queue_ids]
            if row is not None
        ]
        await _store_queue_state(state, queue_ids=queue_ids, queue_index=0, current_offer_id=queue_ids[0])
        await message.answer(_queue_text(lg, offers=offers))
        current = offers[0]
        await message.answer(
            _offer_detail_text(session, lg, offer=current),
            reply_markup=_detail_keyboard(lg, current).as_markup(),
        )


@router.callback_query(F.data.in_({ADMIN_OFFERS_NAV_HOME, ADMIN_OFFERS_NAV_BACK, ADMIN_OFFERS_NAV_NEXT, ADMIN_OFFERS_NAV_PREV}))
async def admin_queue_navigation(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.data is None or query.message is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    if await _deny_if_not_allowed(query, language_code=lg):
        await state.clear()
        return
    if query.data == ADMIN_OFFERS_NAV_HOME:
        await state.clear()
        await query.message.answer(translate(lg, "admin_offer_workspace_home"))
        await query.answer()
        return
    if query.data == ADMIN_OFFERS_NAV_BACK:
        data = await state.get_data()
        queue_ids = [x for x in data.get("queue_offer_ids", []) if isinstance(x, int)]
        with SessionLocal() as session:
            offers = [
                SupplierOfferModerationService()._to_read(row)
                for row in [SupplierOfferModerationService()._offers.get_any(session, offer_id=oid) for oid in queue_ids]
                if row is not None
            ]
        if offers:
            await query.message.answer(_queue_text(lg, offers=offers))
        else:
            await query.message.answer(translate(lg, "admin_offer_workspace_empty"))
        await query.answer()
        return

    data = await state.get_data()
    queue_ids = [x for x in data.get("queue_offer_ids", []) if isinstance(x, int)]
    if not queue_ids:
        await query.message.answer(translate(lg, "admin_offer_no_current"))
        await query.answer()
        return
    idx_raw = data.get("queue_index", 0)
    idx = idx_raw if isinstance(idx_raw, int) else 0
    if query.data == ADMIN_OFFERS_NAV_NEXT:
        idx = (idx + 1) % len(queue_ids)
    else:
        idx = (idx - 1) % len(queue_ids)
    current_offer_id = queue_ids[idx]
    await _store_queue_state(state, queue_ids=queue_ids, queue_index=idx, current_offer_id=current_offer_id)
    with SessionLocal() as session:
        row = SupplierOfferModerationService()._offers.get_any(session, offer_id=current_offer_id)
        if row is None:
            await query.message.answer(translate(lg, "admin_offer_no_current"))
            await query.answer()
            return
        offer = SupplierOfferModerationService()._to_read(row)
        await query.message.answer(
            _offer_detail_text(session, lg, offer=offer),
            reply_markup=_detail_keyboard(lg, offer).as_markup(),
        )
    await query.answer()


def _parse_action(data: str) -> tuple[str, int] | None:
    raw = data.removeprefix(ADMIN_OFFERS_ACTION_CALLBACK_PREFIX)
    parts = raw.split(":", 1)
    if len(parts) != 2:
        return None
    action_name, offer_id_raw = parts
    try:
        return action_name, int(offer_id_raw)
    except ValueError:
        return None


def _refresh_queue(current_offer_id: int, *, session) -> tuple[list[int], int, int]:
    queue_ids = _load_queue_ids(session)
    if queue_ids:
        if current_offer_id in queue_ids:
            idx = queue_ids.index(current_offer_id)
            return queue_ids, idx, current_offer_id
        idx = 0
        return queue_ids, idx, queue_ids[0]
    return [], 0, current_offer_id


@router.callback_query(F.data.startswith(ADMIN_OFFERS_ACTION_CALLBACK_PREFIX))
async def admin_offer_action(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.data is None or query.message is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    if await _deny_if_not_allowed(query, language_code=lg):
        await state.clear()
        return
    parsed = _parse_action(query.data)
    if parsed is None:
        await query.answer()
        return
    action_name, offer_id = parsed
    moderation = SupplierOfferModerationService()
    try:
        with SessionLocal() as session:
            if action_name == "reject":
                await state.set_state(AdminModerationState.awaiting_reject_reason)
                await state.update_data(current_offer_id=offer_id, reject_offer_id=offer_id)
                await query.message.answer(translate(lg, "admin_offer_reject_prompt", offer_id=str(offer_id)))
                await query.answer()
                return
            if action_name == "approve":
                moderation.approve(session, offer_id=offer_id)
                session.commit()
                try:
                    SupplierOfferSupplierNotificationService().notify_approved(session, offer_id=offer_id)
                except Exception:
                    pass
                done_key = "admin_offer_action_done_approve"
            elif action_name == "publish":
                moderation.publish(session, offer_id=offer_id)
                session.commit()
                try:
                    SupplierOfferSupplierNotificationService().notify_published(session, offer_id=offer_id)
                except Exception:
                    pass
                done_key = "admin_offer_action_done_publish"
            elif action_name == "retract":
                moderation.retract_published(session, offer_id=offer_id)
                SupplierOfferExecutionLinkService().close_active_link(
                    session,
                    offer_id=offer_id,
                    reason="retracted",
                    allow_missing=True,
                )
                session.commit()
                try:
                    SupplierOfferSupplierNotificationService().notify_retracted(session, offer_id=offer_id)
                except Exception:
                    pass
                done_key = "admin_offer_action_done_retract"
            else:
                await query.answer()
                return
            queue_ids, idx, current_offer_id = _refresh_queue(offer_id, session=session)
            await _store_queue_state(state, queue_ids=queue_ids, queue_index=idx, current_offer_id=current_offer_id)
            await query.message.answer(translate(lg, done_key, offer_id=str(offer_id)))
            row = moderation._offers.get_any(session, offer_id=current_offer_id)
            if row is not None:
                offer = moderation._to_read(row)
                await query.message.answer(
                    _offer_detail_text(session, lg, offer=offer),
                    reply_markup=_detail_keyboard(lg, offer).as_markup(),
                )
            elif not queue_ids:
                await state.clear()
                await query.message.answer(translate(lg, "admin_offer_workspace_empty"))
    except (SupplierOfferModerationNotFoundError, SupplierOfferModerationStateError, SupplierOfferPublicationConfigError) as exc:
        detail = getattr(exc, "message", str(exc))
        await query.message.answer(translate(lg, "admin_offer_action_unavailable", detail=detail))
    await query.answer()


@router.message(AdminModerationState.awaiting_reject_reason)
async def admin_offer_reject_reason(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _deny_if_not_allowed(message, language_code=lg):
        await state.clear()
        return
    text = message.text.strip()
    folded = text.casefold()
    if folded in {"home", "acasa", "acasă"}:
        await state.clear()
        await message.answer(translate(lg, "admin_offer_workspace_home"))
        return
    if folded in {"back", "inapoi", "înapoi"}:
        await state.set_state(AdminModerationState.browsing_offer_queue)
        await _show_current_offer(message, state, language_code=lg)
        return
    if len(text) < 3:
        await message.answer(translate(lg, "admin_offer_reject_reason_too_short"))
        return
    data = await state.get_data()
    reject_offer_id = data.get("reject_offer_id") or data.get("current_offer_id")
    if not isinstance(reject_offer_id, int):
        await message.answer(translate(lg, "admin_offer_no_current"))
        return
    moderation = SupplierOfferModerationService()
    try:
        with SessionLocal() as session:
            moderation.reject(session, offer_id=reject_offer_id, reason=text)
            session.commit()
            try:
                SupplierOfferSupplierNotificationService().notify_rejected(
                    session,
                    offer_id=reject_offer_id,
                    reason=text,
                )
            except Exception:
                pass
            queue_ids, idx, current_offer_id = _refresh_queue(reject_offer_id, session=session)
            await _store_queue_state(state, queue_ids=queue_ids, queue_index=idx, current_offer_id=current_offer_id)
            await state.update_data(reject_offer_id=None)
            await message.answer(translate(lg, "admin_offer_action_done_reject", offer_id=str(reject_offer_id)))
            row = moderation._offers.get_any(session, offer_id=current_offer_id)
            if row is not None:
                offer = moderation._to_read(row)
                await message.answer(
                    _offer_detail_text(session, lg, offer=offer),
                    reply_markup=_detail_keyboard(lg, offer).as_markup(),
                )
            elif not queue_ids:
                await state.clear()
                await message.answer(translate(lg, "admin_offer_workspace_empty"))
    except (SupplierOfferModerationNotFoundError, SupplierOfferModerationStateError) as exc:
        detail = getattr(exc, "message", str(exc))
        await message.answer(translate(lg, "admin_offer_action_unavailable", detail=detail))
