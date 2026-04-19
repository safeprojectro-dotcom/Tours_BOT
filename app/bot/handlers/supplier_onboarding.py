"""Y2.1: supplier Telegram onboarding entry + FSM (identity binding; admin review gate)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
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
from app.models.enums import SupplierServiceComposition
from app.services.supplier_onboarding_service import SupplierOnboardingService

router = Router(name="supplier-onboarding")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


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
    kb.adjust(1)
    return kb


def _capability_from_callback(data: str) -> SupplierServiceComposition | None:
    raw = data.removeprefix(SUPPLIER_ONBOARDING_CAPABILITY_CALLBACK_PREFIX)
    try:
        return SupplierServiceComposition(raw)
    except ValueError:
        return None


def _is_short(value: str) -> bool:
    return len(value.strip()) < 2


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
        )
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
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(display_name=message.text.strip())
    await state.set_state(SupplierOnboardingState.entering_contact_info)
    await message.answer(translate(lg, "supplier_onboarding_contact_prompt"))


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
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(contact_info=message.text.strip())
    await state.set_state(SupplierOnboardingState.entering_region)
    await message.answer(translate(lg, "supplier_onboarding_region_prompt"))


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
    if _is_short(message.text):
        await message.answer(translate(lg, "supplier_onboarding_invalid_short"))
        return
    await state.update_data(region=message.text.strip())
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
    cap = _capability_from_callback(query.data)
    if cap is None:
        await query.answer()
        return
    await state.update_data(service_composition=cap.value)
    await state.set_state(SupplierOnboardingState.entering_fleet_summary)
    await query.message.answer(translate(lg, "supplier_onboarding_fleet_prompt"))
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
