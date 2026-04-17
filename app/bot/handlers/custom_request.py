"""Private chat: structured custom trip / group request intake (Track 4, Layer C)."""

from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    CUSTOM_REQUEST_CANCEL_CALLBACK,
    CUSTOM_REQUEST_TYPE_GROUP,
    CUSTOM_REQUEST_TYPE_OTHER,
    CUSTOM_REQUEST_TYPE_ROUTE,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.bot.state import CustomRequestState
from app.db.session import SessionLocal
from app.models.enums import CustomMarketplaceRequestType
from app.schemas.custom_marketplace import BotCustomRequestCreate
from app.services.custom_marketplace_request_service import CustomMarketplaceRequestService

router = Router(name="custom-request")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


def _user_service() -> TelegramUserContextService:
    return TelegramUserContextService()


def _type_from_callback(data: str) -> CustomMarketplaceRequestType | None:
    mapping = {
        CUSTOM_REQUEST_TYPE_GROUP: CustomMarketplaceRequestType.GROUP_TRIP,
        CUSTOM_REQUEST_TYPE_ROUTE: CustomMarketplaceRequestType.CUSTOM_ROUTE,
        CUSTOM_REQUEST_TYPE_OTHER: CustomMarketplaceRequestType.OTHER,
    }
    return mapping.get(data)


def _build_type_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=translate(language_code, "custom_request_type_group"), callback_data=CUSTOM_REQUEST_TYPE_GROUP)
    builder.button(text=translate(language_code, "custom_request_type_route"), callback_data=CUSTOM_REQUEST_TYPE_ROUTE)
    builder.button(text=translate(language_code, "custom_request_type_other"), callback_data=CUSTOM_REQUEST_TYPE_OTHER)
    builder.button(text=translate(language_code, "custom_request_cancel"), callback_data=CUSTOM_REQUEST_CANCEL_CALLBACK)
    builder.adjust(1)
    return builder


def _parse_travel_dates(text: str) -> tuple[date, date | None]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("empty")
    start = date.fromisoformat(lines[0])
    if len(lines) >= 2:
        end = date.fromisoformat(lines[1])
    else:
        end = None
    if end is not None and end < start:
        raise ValueError("range")
    return start, end


@router.message(Command("custom_request"))
async def cmd_custom_request(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    await state.clear()
    lg: str | None = message.from_user.language_code
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
        lg = user.preferred_language or lg
    await state.set_state(CustomRequestState.choosing_type)
    await message.answer(
        translate(lg, "custom_request_start"),
        reply_markup=_build_type_keyboard(lg).as_markup(),
    )


@router.callback_query(CustomRequestState.choosing_type, F.data == CUSTOM_REQUEST_CANCEL_CALLBACK)
async def callback_cancel_type(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None or query.from_user is None:
        return
    lg = query.from_user.language_code
    await state.clear()
    await query.message.answer(translate(lg, "custom_request_cancelled"))
    await query.answer()


@router.callback_query(CustomRequestState.choosing_type, F.data.in_({CUSTOM_REQUEST_TYPE_GROUP, CUSTOM_REQUEST_TYPE_ROUTE, CUSTOM_REQUEST_TYPE_OTHER}))
async def callback_chose_type(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None or query.from_user is None or query.data is None:
        return
    req_type = _type_from_callback(query.data)
    if req_type is None:
        await query.answer()
        return
    lg = query.from_user.language_code
    with SessionLocal() as session:
        user = _user_service().sync_private_user(
            session,
            telegram_user_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name,
            telegram_language_code=query.from_user.language_code,
        )
        session.commit()
        lg = user.preferred_language or lg
    await state.update_data(request_type=req_type.value)
    await state.set_state(CustomRequestState.travel_dates)
    await query.message.answer(translate(lg, "custom_request_dates_prompt"))
    await query.answer()


@router.message(CustomRequestState.travel_dates)
async def message_travel_dates(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    data = await state.get_data()
    lg = message.from_user.language_code
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
        lg = user.preferred_language or lg
    try:
        start, end = _parse_travel_dates(message.text)
    except ValueError:
        await message.answer(translate(lg, "custom_request_dates_invalid"))
        return
    await state.update_data(travel_date_start=start.isoformat(), travel_date_end=end.isoformat() if end else None)
    await state.set_state(CustomRequestState.route_notes)
    await message.answer(translate(lg, "custom_request_route_prompt"))


@router.message(CustomRequestState.route_notes)
async def message_route(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = message.from_user.language_code
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
        lg = user.preferred_language or lg
    notes = message.text.strip()
    if len(notes) < 3:
        await message.answer(translate(lg, "custom_request_route_too_short"))
        return
    await state.update_data(route_notes=notes)
    await state.set_state(CustomRequestState.group_size)
    await message.answer(translate(lg, "custom_request_group_size_prompt"))


@router.message(CustomRequestState.group_size)
async def message_group_size(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = message.from_user.language_code
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
        lg = user.preferred_language or lg
    raw = message.text.strip()
    group_size: int | None
    if raw == "-":
        group_size = None
    else:
        try:
            group_size = int(raw)
        except ValueError:
            await message.answer(translate(lg, "custom_request_group_size_invalid"))
            return
        if group_size < 1 or group_size > 999:
            await message.answer(translate(lg, "custom_request_group_size_invalid"))
            return
    await state.update_data(group_size=group_size)
    await state.set_state(CustomRequestState.special_conditions)
    await message.answer(translate(lg, "custom_request_special_prompt"))


@router.message(CustomRequestState.special_conditions)
async def message_special_finish(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = message.from_user.language_code
    user_id: int
    with SessionLocal() as session:
        user = _user_service().sync_private_user(
            session,
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            telegram_language_code=message.from_user.language_code,
        )
        user_id = user.id
        pref_lang = user.preferred_language
        session.commit()
        lg = pref_lang or lg
    raw = message.text.strip()
    special = None if raw == "-" else raw
    data = await state.get_data()
    await state.clear()
    try:
        gs = data.get("group_size")
        payload = BotCustomRequestCreate(
            user_id=user_id,
            request_type=CustomMarketplaceRequestType(str(data["request_type"])),
            travel_date_start=date.fromisoformat(str(data["travel_date_start"])),
            travel_date_end=date.fromisoformat(str(data["travel_date_end"])) if data.get("travel_date_end") else None,
            route_notes=str(data["route_notes"]),
            group_size=int(gs) if gs is not None else None,
            special_conditions=special,
        )
    except Exception:
        await message.answer(translate(lg, "custom_request_failed"))
        return
    try:
        with SessionLocal() as session:
            row = CustomMarketplaceRequestService().create_from_bot(session, payload=payload)
            session.commit()
            rid = row.id
    except Exception:
        await message.answer(translate(lg, "custom_request_failed"))
        return
    await message.answer(translate(lg, "custom_request_saved", request_id=str(rid)))
