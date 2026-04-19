"""Y2.2: supplier Telegram offer intake (approved supplier gate, draft save, explicit moderation submit)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX,
    SUPPLIER_OFFER_RESTART_CALLBACK,
    SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX,
    SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.bot.state import SupplierOfferIntakeState
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SupplierOfferLifecycle, SupplierOnboardingStatus, SupplierOfferPaymentMode, TourSalesMode
from app.models.enums import SupplierServiceComposition
from app.models.supplier import Supplier
from app.schemas.supplier_admin import SupplierOfferCreate, SupplierOfferUpdate
from app.services.supplier_offer_service import (
    SupplierOfferImmutableError,
    SupplierOfferLifecycleNotAllowedError,
    SupplierOfferNotFoundError,
    SupplierOfferReadinessError,
    SupplierOfferService,
)
from app.services.supplier_onboarding_service import SupplierOnboardingService

router = Router(name="supplier-offer-intake")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _sales_mode_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text=translate(language_code, "supplier_offer_opt_sales_per_seat"), callback_data=f"{SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX}{TourSalesMode.PER_SEAT.value}")
    kb.button(text=translate(language_code, "supplier_offer_opt_sales_full_bus"), callback_data=f"{SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX}{TourSalesMode.FULL_BUS.value}")
    kb.adjust(1)
    return kb


def _payment_mode_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_offer_opt_payment_platform_checkout"),
        callback_data=f"{SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX}{SupplierOfferPaymentMode.PLATFORM_CHECKOUT.value}",
    )
    kb.button(
        text=translate(language_code, "supplier_offer_opt_payment_assisted_closure"),
        callback_data=f"{SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX}{SupplierOfferPaymentMode.ASSISTED_CLOSURE.value}",
    )
    kb.adjust(1)
    return kb


def _submit_keyboard(language_code: str | None, *, offer_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_offer_submit_now"),
        callback_data=f"{SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX}{offer_id}",
    )
    kb.button(text=translate(language_code, "supplier_offer_restart"), callback_data=SUPPLIER_OFFER_RESTART_CALLBACK)
    kb.adjust(1)
    return kb


def _parse_dt(raw: str) -> datetime | None:
    txt = raw.strip()
    if not txt:
        return None
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        try:
            dt = datetime.strptime(txt, "%Y-%m-%d %H:%M")
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _parse_positive_int(raw: str) -> int | None:
    txt = raw.strip()
    if not txt:
        return None
    try:
        v = int(txt)
    except ValueError:
        return None
    if v <= 0:
        return None
    return v


def _parse_non_negative_decimal(raw: str) -> Decimal | None:
    txt = raw.strip().replace(",", ".")
    if not txt:
        return None
    try:
        v = Decimal(txt)
    except InvalidOperation:
        return None
    if v < 0:
        return None
    return v


def _supplier_access_status(supplier: Supplier | None) -> str:
    if supplier is None:
        return "not_onboarded"
    if supplier.onboarding_status == SupplierOnboardingStatus.APPROVED:
        return "approved"
    if supplier.onboarding_status == SupplierOnboardingStatus.PENDING_REVIEW:
        return "pending"
    return "rejected"


def _gate_message_key(status_code: str) -> str:
    return {
        "not_onboarded": "supplier_offer_gate_not_onboarded",
        "pending": "supplier_offer_gate_pending",
        "rejected": "supplier_offer_gate_rejected",
    }[status_code]


def _first_draft_offer_id(session, *, supplier_id: int) -> int | None:
    offers = SupplierOfferService().list_offers(session, supplier_id=supplier_id, limit=50, offset=0)
    for o in offers:
        if o.lifecycle_status == SupplierOfferLifecycle.DRAFT:
            return o.id
    return None


async def _resolve_language(telegram_user_id: int, telegram_language_code: str | None) -> str | None:
    with SessionLocal() as session:
        return _user_service().resolve_language(
            session,
            telegram_user_id=telegram_user_id,
            telegram_language_code=telegram_language_code,
        )


@router.message(Command("supplier_offer"))
async def cmd_supplier_offer(message: Message, state: FSMContext) -> None:
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
        supplier = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=message.from_user.id)
    status_code = _supplier_access_status(supplier)
    if status_code != "approved":
        await message.answer(translate(lg, _gate_message_key(status_code)))
        await state.clear()
        return
    await state.clear()
    await state.set_state(SupplierOfferIntakeState.entering_title)
    await message.answer(
        "\n\n".join(
            [
                translate(lg, "supplier_offer_start"),
                translate(lg, "supplier_offer_prompt_title"),
            ]
        )
    )


@router.message(SupplierOfferIntakeState.entering_title)
async def intake_title(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    title = message.text.strip()
    if len(title) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"))
        return
    await state.update_data(title=title)
    await state.set_state(SupplierOfferIntakeState.entering_description)
    await message.answer(translate(lg, "supplier_offer_prompt_description"))


@router.message(SupplierOfferIntakeState.entering_description)
async def intake_description(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    description = message.text.strip()
    if len(description) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"))
        return
    await state.update_data(description=description)
    await state.set_state(SupplierOfferIntakeState.entering_departure_datetime)
    await message.answer(translate(lg, "supplier_offer_prompt_departure"))


@router.message(SupplierOfferIntakeState.entering_departure_datetime)
async def intake_departure(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    dt = _parse_dt(message.text)
    if dt is None:
        await message.answer(translate(lg, "supplier_offer_invalid_datetime"))
        return
    await state.update_data(departure_datetime=dt.isoformat())
    await state.set_state(SupplierOfferIntakeState.entering_return_datetime)
    await message.answer(translate(lg, "supplier_offer_prompt_return"))


@router.message(SupplierOfferIntakeState.entering_return_datetime)
async def intake_return(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    ret = _parse_dt(message.text)
    if ret is None:
        await message.answer(translate(lg, "supplier_offer_invalid_datetime"))
        return
    data = await state.get_data()
    dep = _parse_dt(str(data.get("departure_datetime") or ""))
    if dep is None or ret < dep:
        await message.answer(translate(lg, "supplier_offer_invalid_datetime"))
        return
    await state.update_data(return_datetime=ret.isoformat())
    await state.set_state(SupplierOfferIntakeState.entering_seats_total)
    await message.answer(translate(lg, "supplier_offer_prompt_seats_total"))


@router.message(SupplierOfferIntakeState.entering_seats_total)
async def intake_seats(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    seats = _parse_positive_int(message.text)
    if seats is None:
        await message.answer(translate(lg, "supplier_offer_invalid_seats_total"))
        return
    await state.update_data(seats_total=seats)
    await state.set_state(SupplierOfferIntakeState.entering_base_price)
    await message.answer(translate(lg, "supplier_offer_prompt_base_price"))


@router.message(SupplierOfferIntakeState.entering_base_price)
async def intake_price(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    price = _parse_non_negative_decimal(message.text)
    if price is None:
        await message.answer(translate(lg, "supplier_offer_invalid_price"))
        return
    await state.update_data(base_price=str(price))
    await state.set_state(SupplierOfferIntakeState.entering_currency)
    await message.answer(translate(lg, "supplier_offer_prompt_currency"))


@router.message(SupplierOfferIntakeState.entering_currency)
async def intake_currency(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    currency = message.text.strip().upper()
    if not currency:
        await message.answer(translate(lg, "supplier_offer_invalid_currency"))
        return
    await state.update_data(currency=currency)
    await state.set_state(SupplierOfferIntakeState.choosing_sales_mode)
    await message.answer(
        translate(lg, "supplier_offer_prompt_sales_mode"),
        reply_markup=_sales_mode_keyboard(lg).as_markup(),
    )


@router.callback_query(
    SupplierOfferIntakeState.choosing_sales_mode,
    F.data.startswith(SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX),
)
async def intake_sales_mode(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    raw = query.data.removeprefix(SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX)
    try:
        mode = TourSalesMode(raw)
    except ValueError:
        await query.answer()
        return
    await state.update_data(sales_mode=mode.value)
    await state.set_state(SupplierOfferIntakeState.choosing_payment_mode)
    await query.message.answer(
        translate(lg, "supplier_offer_prompt_payment_mode"),
        reply_markup=_payment_mode_keyboard(lg).as_markup(),
    )
    await query.answer()


@router.callback_query(
    SupplierOfferIntakeState.choosing_payment_mode,
    F.data.startswith(SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX),
)
async def intake_payment_mode(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    raw = query.data.removeprefix(SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX)
    try:
        mode = SupplierOfferPaymentMode(raw)
    except ValueError:
        await query.answer()
        return
    await state.update_data(payment_mode=mode.value)
    await state.set_state(SupplierOfferIntakeState.entering_program_text)
    await query.message.answer(translate(lg, "supplier_offer_prompt_program_text"))
    await query.answer()


@router.message(SupplierOfferIntakeState.entering_program_text)
async def intake_program_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    program_text = message.text.strip()
    if len(program_text) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"))
        return
    await state.update_data(program_text=program_text)
    await state.set_state(SupplierOfferIntakeState.entering_vehicle_or_notes)
    await message.answer(translate(lg, "supplier_offer_prompt_vehicle_or_notes"))


@router.message(SupplierOfferIntakeState.entering_vehicle_or_notes)
async def intake_vehicle_or_notes(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    vehicle_or_notes = message.text.strip()
    if len(vehicle_or_notes) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"))
        return
    data = await state.get_data()
    with SessionLocal() as session:
        supplier = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=message.from_user.id)
        status_code = _supplier_access_status(supplier)
        if supplier is None or status_code != "approved":
            await state.clear()
            await message.answer(translate(lg, _gate_message_key(status_code)))
            return
        svc = SupplierOfferService()
        dep = datetime.fromisoformat(str(data["departure_datetime"]))
        ret = datetime.fromisoformat(str(data["return_datetime"]))
        create_payload = SupplierOfferCreate(
            title=str(data["title"]),
            description=str(data["description"]),
            program_text=str(data["program_text"]),
            departure_datetime=dep,
            return_datetime=ret,
            vehicle_label=vehicle_or_notes,
            seats_total=int(data["seats_total"]),
            base_price=Decimal(str(data["base_price"])),
            currency=str(data["currency"]),
            service_composition=supplier.onboarding_service_composition or SupplierServiceComposition.TRANSPORT_ONLY,
            sales_mode=TourSalesMode(str(data["sales_mode"])),
            payment_mode=SupplierOfferPaymentMode(str(data["payment_mode"])),
        )
        draft_offer_id = _first_draft_offer_id(session, supplier_id=supplier.id)
        try:
            if draft_offer_id is None:
                saved = svc.create_offer(session, supplier_id=supplier.id, payload=create_payload)
            else:
                saved = svc.update_offer(
                    session,
                    supplier_id=supplier.id,
                    offer_id=draft_offer_id,
                    payload=SupplierOfferUpdate(
                        title=create_payload.title,
                        description=create_payload.description,
                        program_text=create_payload.program_text,
                        departure_datetime=create_payload.departure_datetime,
                        return_datetime=create_payload.return_datetime,
                        vehicle_label=create_payload.vehicle_label,
                        seats_total=create_payload.seats_total,
                        base_price=create_payload.base_price,
                        currency=create_payload.currency,
                        service_composition=create_payload.service_composition,
                        sales_mode=create_payload.sales_mode,
                        payment_mode=create_payload.payment_mode,
                        lifecycle_status=SupplierOfferLifecycle.DRAFT,
                    ),
                )
        except SupplierOfferReadinessError:
            await message.answer(translate(lg, "supplier_offer_submit_failed"))
            return
        session.commit()
    await state.update_data(draft_offer_id=saved.id)
    await state.set_state(SupplierOfferIntakeState.awaiting_submit_action)
    await message.answer(translate(lg, "supplier_offer_draft_saved", offer_id=str(saved.id)))
    await message.answer(
        translate(lg, "supplier_offer_submit_ready"),
        reply_markup=_submit_keyboard(lg, offer_id=saved.id).as_markup(),
    )


@router.callback_query(
    SupplierOfferIntakeState.awaiting_submit_action,
    F.data.startswith(SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX),
)
async def submit_offer_to_moderation(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    try:
        offer_id = int(query.data.removeprefix(SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX))
    except ValueError:
        await query.answer()
        return
    with SessionLocal() as session:
        supplier = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=query.from_user.id)
        status_code = _supplier_access_status(supplier)
        if supplier is None or status_code != "approved":
            await state.clear()
            await query.message.answer(translate(lg, _gate_message_key(status_code)))
            await query.answer()
            return
        try:
            SupplierOfferService().update_offer(
                session,
                supplier_id=supplier.id,
                offer_id=offer_id,
                payload=SupplierOfferUpdate(lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION),
            )
        except (
            SupplierOfferReadinessError,
            SupplierOfferLifecycleNotAllowedError,
            SupplierOfferImmutableError,
            SupplierOfferNotFoundError,
        ):
            await query.message.answer(translate(lg, "supplier_offer_submit_failed"))
            await query.answer()
            return
        session.commit()
    await state.clear()
    await query.message.answer(translate(lg, "supplier_offer_submitted", offer_id=str(offer_id)))
    await query.answer()


@router.callback_query(
    SupplierOfferIntakeState.awaiting_submit_action,
    F.data == SUPPLIER_OFFER_RESTART_CALLBACK,
)
async def restart_offer_intake(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    await state.clear()
    await state.set_state(SupplierOfferIntakeState.entering_title)
    await query.message.answer(translate(lg, "supplier_offer_restart_done"))
    await query.answer()
