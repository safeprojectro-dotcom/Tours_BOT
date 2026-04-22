"""Y2.1: supplier Telegram onboarding entry + FSM (identity binding; admin review gate)."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK,
    SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK,
    SUPPLIER_ONBOARDING_LEGAL_ENTITY_AUTHORIZED_CARRIER,
    SUPPLIER_ONBOARDING_LEGAL_ENTITY_CALLBACK_PREFIX,
    SUPPLIER_ONBOARDING_LEGAL_ENTITY_COMPANY,
    SUPPLIER_ONBOARDING_LEGAL_ENTITY_INDIVIDUAL_ENTREPRENEUR,
    SUPPLIER_ONBOARDING_CAPABILITY_CALLBACK_PREFIX,
    SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_GUIDE,
    SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_GUIDE_WATER,
    SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_ONLY,
    SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_WATER,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.bot.state import SupplierOnboardingState
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SupplierLegalEntityType, SupplierServiceComposition
from app.services.supplier_onboarding_service import SupplierOnboardingService

router = Router(name="supplier-onboarding")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")
_REG_CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9./-]{1,63}$")
_STEP_SEQUENCE: list[State] = [
    SupplierOnboardingState.entering_display_name,
    SupplierOnboardingState.entering_contact_info,
    SupplierOnboardingState.entering_region,
    SupplierOnboardingState.choosing_legal_entity_type,
    SupplierOnboardingState.entering_legal_registered_name,
    SupplierOnboardingState.entering_legal_registration_code,
    SupplierOnboardingState.entering_permit_license_type,
    SupplierOnboardingState.entering_permit_license_number,
    SupplierOnboardingState.choosing_service_composition,
    SupplierOnboardingState.entering_fleet_summary,
]


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _reply_nav_keyboard(language_code: str | None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translate(language_code, "supplier_offer_nav_back")),
                KeyboardButton(text=translate(language_code, "supplier_offer_nav_home")),
            ]
        ],
        resize_keyboard=True,
        selective=True,
    )


def _capability_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_onboarding_capability_transport_only"),
        callback_data=SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_ONLY,
    )
    kb.button(
        text=translate(language_code, "supplier_onboarding_capability_transport_guide"),
        callback_data=SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_GUIDE,
    )
    kb.button(
        text=translate(language_code, "supplier_onboarding_capability_transport_water"),
        callback_data=SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_WATER,
    )
    kb.button(
        text=translate(language_code, "supplier_onboarding_capability_transport_guide_water"),
        callback_data=SUPPLIER_ONBOARDING_CAPABILITY_TRANSPORT_GUIDE_WATER,
    )
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK)
    kb.adjust(1)
    return kb


def _legal_entity_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_onboarding_legal_entity_company"),
        callback_data=SUPPLIER_ONBOARDING_LEGAL_ENTITY_COMPANY,
    )
    kb.button(
        text=translate(language_code, "supplier_onboarding_legal_entity_individual_entrepreneur"),
        callback_data=SUPPLIER_ONBOARDING_LEGAL_ENTITY_INDIVIDUAL_ENTREPRENEUR,
    )
    kb.button(
        text=translate(language_code, "supplier_onboarding_legal_entity_authorized_carrier"),
        callback_data=SUPPLIER_ONBOARDING_LEGAL_ENTITY_AUTHORIZED_CARRIER,
    )
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK)
    kb.adjust(1)
    return kb


def _capability_from_callback(data: str) -> SupplierServiceComposition | None:
    raw = data.removeprefix(SUPPLIER_ONBOARDING_CAPABILITY_CALLBACK_PREFIX)
    try:
        return SupplierServiceComposition(raw)
    except ValueError:
        return None


def _legal_entity_from_callback(data: str) -> SupplierLegalEntityType | None:
    raw = data.removeprefix(SUPPLIER_ONBOARDING_LEGAL_ENTITY_CALLBACK_PREFIX)
    try:
        return SupplierLegalEntityType(raw)
    except ValueError:
        return None


def _is_short(value: str) -> bool:
    return len(value.strip()) < 2


def _is_back_text(text: str) -> bool:
    s = text.strip().casefold()
    return s in {"înapoi", "inapoi", "back"}


def _is_home_text(text: str) -> bool:
    s = text.strip().casefold()
    return s in {"acasă", "acasa", "home"}


def _state_name_from_context(raw_state: str | State | None) -> str | None:
    if raw_state is None:
        return None
    if isinstance(raw_state, State):
        return raw_state.state.split(":", 1)[1]
    state_str = str(raw_state)
    if "SupplierOnboardingState:" in state_str:
        tail = state_str.split("SupplierOnboardingState:", 1)[1]
        return tail.replace("'>", "").replace(">", "").replace("'", "").strip()
    if ":" in state_str:
        return state_str.split(":", 1)[1]
    if "." in state_str:
        return state_str.split(".", 1)[1]
    return state_str


def _current_step_index(state_name: str | None) -> int | None:
    if state_name is None:
        return None
    for i, step in enumerate(_STEP_SEQUENCE):
        if step.state.endswith(state_name):
            return i
    return None


async def _prompt_for_state(
    message: Message,
    state: FSMContext,
    *,
    language_code: str | None,
    state_name: str | None = None,
) -> None:
    step_name = state_name or _state_name_from_context(await state.get_state())
    if step_name == "entering_display_name":
        await message.answer(translate(language_code, "supplier_onboarding_display_name_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_contact_info":
        await message.answer(translate(language_code, "supplier_onboarding_contact_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_region":
        await message.answer(translate(language_code, "supplier_onboarding_region_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "choosing_legal_entity_type":
        await message.answer(
            translate(language_code, "supplier_onboarding_legal_entity_prompt"),
            reply_markup=_legal_entity_keyboard(language_code).as_markup(),
        )
        return
    if step_name == "entering_legal_registered_name":
        await message.answer(translate(language_code, "supplier_onboarding_legal_registered_name_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_legal_registration_code":
        await message.answer(translate(language_code, "supplier_onboarding_legal_registration_code_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_permit_license_type":
        await message.answer(translate(language_code, "supplier_onboarding_permit_license_type_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_permit_license_number":
        await message.answer(translate(language_code, "supplier_onboarding_permit_license_number_prompt"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "choosing_service_composition":
        await message.answer(
            translate(language_code, "supplier_onboarding_capability_prompt"),
            reply_markup=_capability_keyboard(language_code).as_markup(),
        )
        return
    if step_name == "entering_fleet_summary":
        await message.answer(translate(language_code, "supplier_onboarding_fleet_prompt"), reply_markup=_reply_nav_keyboard(language_code))


async def _handle_nav_text(message: Message, state: FSMContext, language_code: str | None) -> bool:
    text = (message.text or "").strip()
    if not text:
        return False
    if _is_home_text(text):
        await state.clear()
        await message.answer(translate(language_code, "supplier_onboarding_cancelled_home"))
        return True
    if not _is_back_text(text):
        return False
    raw_state = await state.get_state()
    state_name = _state_name_from_context(raw_state)
    idx = _current_step_index(state_name)
    if idx is None:
        return False
    if idx <= 0:
        await state.set_state(_STEP_SEQUENCE[0])
        await _prompt_for_state(message, state, language_code=language_code, state_name="entering_display_name")
        return True
    prev_state = _STEP_SEQUENCE[idx - 1]
    await state.set_state(prev_state)
    await _prompt_for_state(message, state, language_code=language_code, state_name=prev_state.state.split(":")[1])
    return True


async def _handle_nav_callback(query: CallbackQuery, state: FSMContext, language_code: str | None) -> bool:
    if query.data == SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK:
        await state.clear()
        if query.message is not None:
            await query.message.answer(translate(language_code, "supplier_onboarding_cancelled_home"))
        await query.answer()
        return True
    if query.data != SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK:
        return False
    if query.message is None:
        await query.answer()
        return True
    raw_state = await state.get_state()
    state_name = _state_name_from_context(raw_state)
    idx = _current_step_index(state_name)
    if idx is None:
        await query.answer()
        return True
    if idx <= 0:
        await state.set_state(_STEP_SEQUENCE[0])
        await _prompt_for_state(query.message, state, language_code=language_code, state_name="entering_display_name")
        await query.answer()
        return True
    prev_state = _STEP_SEQUENCE[idx - 1]
    await state.set_state(prev_state)
    await _prompt_for_state(query.message, state, language_code=language_code, state_name=prev_state.state.split(":")[1])
    await query.answer()
    return True


@router.message(Command("supplier"))
async def cmd_supplier_entry(message: Message, state: FSMContext) -> None:
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
        existing = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=message.from_user.id)
    await state.clear()
    if existing is not None:
        st = existing.onboarding_status.value
        if st == "pending_review":
            await message.answer(translate(lg, "supplier_onboarding_already_pending"))
            return
        if st == "approved":
            await message.answer(translate(lg, "supplier_onboarding_already_approved"))
            return
        await message.answer(translate(lg, "supplier_onboarding_rejected_status"))
    await state.set_state(SupplierOnboardingState.entering_display_name)
    await message.answer(
        "\n\n".join(
            [
                translate(lg, "supplier_onboarding_start"),
                translate(lg, "supplier_onboarding_display_name_prompt"),
            ]
        ),
        reply_markup=_reply_nav_keyboard(lg),
    )


@router.message(SupplierOnboardingState.entering_display_name)
async def onboarding_display_name(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(display_name=message.text.strip())
    await state.set_state(SupplierOnboardingState.entering_contact_info)
    await message.answer(translate(lg, "supplier_onboarding_contact_prompt"), reply_markup=_reply_nav_keyboard(lg))


@router.message(SupplierOnboardingState.entering_contact_info)
async def onboarding_contact_info(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(contact_info=message.text.strip())
    await state.set_state(SupplierOnboardingState.entering_region)
    await message.answer(translate(lg, "supplier_onboarding_region_prompt"), reply_markup=_reply_nav_keyboard(lg))


@router.message(SupplierOnboardingState.entering_region)
async def onboarding_region(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(region=message.text.strip())
    await state.set_state(SupplierOnboardingState.choosing_legal_entity_type)
    await message.answer(
        translate(lg, "supplier_onboarding_legal_entity_prompt"),
        reply_markup=_legal_entity_keyboard(lg).as_markup(),
    )


@router.callback_query(
    F.data.in_({SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK, SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK}),
)
async def onboarding_nav_callback(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.data is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    await _handle_nav_callback(query, state, lg)


@router.callback_query(
    SupplierOnboardingState.choosing_legal_entity_type,
    F.data.startswith(SUPPLIER_ONBOARDING_LEGAL_ENTITY_CALLBACK_PREFIX),
)
async def onboarding_legal_entity(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    if await _handle_nav_callback(query, state, lg):
        return
    entity = _legal_entity_from_callback(query.data)
    if entity is None:
        await query.answer()
        return
    await state.update_data(legal_entity_type=entity.value)
    await state.set_state(SupplierOnboardingState.entering_legal_registered_name)
    await query.message.answer(
        translate(lg, "supplier_onboarding_legal_registered_name_prompt"),
        reply_markup=_reply_nav_keyboard(lg),
    )
    await query.answer()


@router.message(SupplierOnboardingState.entering_legal_registered_name)
async def onboarding_legal_registered_name(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(legal_registered_name=message.text.strip())
    await state.set_state(SupplierOnboardingState.entering_legal_registration_code)
    await message.answer(translate(lg, "supplier_onboarding_legal_registration_code_prompt"), reply_markup=_reply_nav_keyboard(lg))


@router.message(SupplierOnboardingState.entering_legal_registration_code)
async def onboarding_legal_registration_code(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    code = message.text.strip().upper()
    if not _REG_CODE_RE.fullmatch(code):
        await message.answer(translate(lg, "supplier_onboarding_invalid_registration_code"))
        return
    await state.update_data(legal_registration_code=code)
    await state.set_state(SupplierOnboardingState.entering_permit_license_type)
    await message.answer(translate(lg, "supplier_onboarding_permit_license_type_prompt"), reply_markup=_reply_nav_keyboard(lg))


@router.message(SupplierOnboardingState.entering_permit_license_type)
async def onboarding_permit_license_type(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(permit_license_type=message.text.strip())
    await state.set_state(SupplierOnboardingState.entering_permit_license_number)
    await message.answer(translate(lg, "supplier_onboarding_permit_license_number_prompt"), reply_markup=_reply_nav_keyboard(lg))


@router.message(SupplierOnboardingState.entering_permit_license_number)
async def onboarding_permit_license_number(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _handle_nav_text(message, state, lg):
        return
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(permit_license_number=message.text.strip())
    await state.set_state(SupplierOnboardingState.choosing_service_composition)
    await message.answer(
        translate(lg, "supplier_onboarding_capability_prompt"),
        reply_markup=_capability_keyboard(lg).as_markup(),
    )


@router.callback_query(
    SupplierOnboardingState.choosing_service_composition,
    F.data.startswith(SUPPLIER_ONBOARDING_CAPABILITY_CALLBACK_PREFIX),
)
async def onboarding_capability(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    if await _handle_nav_callback(query, state, lg):
        return
    cap = _capability_from_callback(query.data)
    if cap is None:
        await query.answer()
        return
    await state.update_data(service_composition=cap.value)
    await state.set_state(SupplierOnboardingState.entering_fleet_summary)
    await query.message.answer(translate(lg, "supplier_onboarding_fleet_prompt"), reply_markup=_reply_nav_keyboard(lg))
    await query.answer()


@router.message(SupplierOnboardingState.entering_fleet_summary)
async def onboarding_finish(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
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
    if await _handle_nav_text(message, state, lg):
        return
    data = await state.get_data()
    await state.clear()
    fleet = message.text.strip()
    fleet_summary = None if fleet == "-" else fleet
    try:
        service_composition = SupplierServiceComposition(str(data["service_composition"]))
        with SessionLocal() as session:
            _, result_code = SupplierOnboardingService().submit_from_telegram(
                session,
                telegram_user_id=message.from_user.id,
                display_name=str(data["display_name"]),
                contact_info=str(data["contact_info"]),
                region=str(data["region"]),
                legal_entity_type=SupplierLegalEntityType(str(data["legal_entity_type"])),
                legal_registered_name=str(data["legal_registered_name"]),
                legal_registration_code=str(data["legal_registration_code"]),
                permit_license_type=str(data["permit_license_type"]),
                permit_license_number=str(data["permit_license_number"]),
                service_composition=service_composition,
                fleet_summary=fleet_summary,
            )
            session.commit()
    except Exception:
        await message.answer(translate(lg, "supplier_onboarding_failed"))
        return
    if result_code == "resubmitted":
        await message.answer(translate(lg, "supplier_onboarding_resubmitted"))
        return
    if result_code == "already_pending":
        await message.answer(translate(lg, "supplier_onboarding_already_pending"))
        return
    if result_code == "already_approved":
        await message.answer(translate(lg, "supplier_onboarding_already_approved"))
        return
    await message.answer(translate(lg, "supplier_onboarding_submitted"))
