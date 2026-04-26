"""Y2.2a + B3: structured supplier offer intake (B2 fields, one question at a time)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    SUPPLIER_OFFER_COVER_NONE,
    SUPPLIER_OFFER_COVER_URL,
    SUPPLIER_OFFER_NAV_BACK_CALLBACK,
    SUPPLIER_OFFER_NAV_CALLBACK_PREFIX,
    SUPPLIER_OFFER_NAV_HOME_CALLBACK,
    SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX,
    SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX,
    SUPPLIER_OFFER_SCHEDULE_ONE,
    SUPPLIER_OFFER_SCHEDULE_RECURRING,
    SUPPLIER_OFFER_SCHEDULE_CALLBACK_PREFIX,
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

_STRICT_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)?$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_URL_START_RE = re.compile(r"^https?://", re.IGNORECASE)
_SKIP = frozenset({"-", "—", "skip", "n/a", "na"})


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


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _state_name_from_context(raw_state: str | State | None) -> str | None:
    if raw_state is None:
        return None
    if isinstance(raw_state, State):
        return raw_state.state.split(":", 1)[1]
    state_str = str(raw_state)
    if "SupplierOfferIntakeState:" in state_str:
        tail = state_str.split("SupplierOfferIntakeState:", 1)[1]
        return tail.replace("'>", "").replace(">", "").replace("'", "").strip()
    if ":" in state_str:
        return state_str.split(":", 1)[1]
    if "." in state_str:
        return state_str.split(".", 1)[1]
    return state_str


def _back_state_name(state_name: str | None, data: dict) -> str | None:
    """Previous step for Back navigation (B3 branching for schedule + cover)."""
    if state_name is None:
        return None
    b: dict[str, str] = {
        "entering_route_facts": "entering_title",
        "choosing_schedule_kind": "entering_route_facts",
        "entering_recurrence_summary": "choosing_schedule_kind",
        "entering_departure_point": "entering_recurrence_summary"
        if (data or {}).get("schedule_kind") == "recurring"
        else "choosing_schedule_kind",
        "entering_departure_datetime": "entering_departure_point",
        "entering_return_datetime": "entering_departure_datetime",
        "entering_seats_total": "entering_return_datetime",
        "choosing_sales_mode": "entering_seats_total",
        "choosing_payment_mode": "choosing_sales_mode",
        "entering_base_price": "choosing_payment_mode",
        "entering_currency": "entering_base_price",
        "entering_program_text": "entering_currency",
        "entering_included_text": "entering_program_text",
        "entering_excluded_text": "entering_included_text",
        "choosing_cover_media": "entering_excluded_text",
        "entering_cover_url": "choosing_cover_media",
        "entering_vehicle_or_notes": "entering_cover_url" if (data or {}).get("cover_step") == "url" else "choosing_cover_media",
        "optional_short_hook": "entering_vehicle_or_notes",
        "optional_marketing_summary": "optional_short_hook",
        "optional_discount_line": "optional_marketing_summary",
        "awaiting_submit_action": "optional_discount_line",
    }
    return b.get(state_name)


def _sales_mode_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_offer_opt_sales_per_seat"),
        callback_data=f"{SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX}{TourSalesMode.PER_SEAT.value}",
    )
    kb.button(
        text=translate(language_code, "supplier_offer_opt_sales_full_bus"),
        callback_data=f"{SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX}{TourSalesMode.FULL_BUS.value}",
    )
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_OFFER_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_OFFER_NAV_HOME_CALLBACK)
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
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_OFFER_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_OFFER_NAV_HOME_CALLBACK)
    kb.adjust(1)
    return kb


def _schedule_kind_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_offer_schedule_one_trip"),
        callback_data=SUPPLIER_OFFER_SCHEDULE_ONE,
    )
    kb.button(
        text=translate(language_code, "supplier_offer_schedule_recurring"),
        callback_data=SUPPLIER_OFFER_SCHEDULE_RECURRING,
    )
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_OFFER_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_OFFER_NAV_HOME_CALLBACK)
    kb.adjust(1)
    return kb


def _cover_choice_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_offer_cover_send_url"),
        callback_data=SUPPLIER_OFFER_COVER_URL,
    )
    kb.button(
        text=translate(language_code, "supplier_offer_cover_no_photo"),
        callback_data=SUPPLIER_OFFER_COVER_NONE,
    )
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_OFFER_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_OFFER_NAV_HOME_CALLBACK)
    kb.adjust(1)
    return kb


def _submit_keyboard(language_code: str | None, *, offer_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "supplier_offer_submit_now"),
        callback_data=f"{SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX}{offer_id}",
    )
    kb.button(text=translate(language_code, "supplier_offer_nav_back"), callback_data=SUPPLIER_OFFER_NAV_BACK_CALLBACK)
    kb.button(text=translate(language_code, "supplier_offer_nav_home"), callback_data=SUPPLIER_OFFER_NAV_HOME_CALLBACK)
    kb.adjust(1)
    return kb


def _parse_dt(raw: str) -> datetime | None:
    txt = raw.strip()
    if not txt:
        return None
    if not _STRICT_DATETIME_RE.fullmatch(txt):
        return None
    normalized = txt.replace(" ", "T").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
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


def _is_skip_text(text: str) -> bool:
    return text.strip().casefold() in _SKIP


def _is_back_text(text: str) -> bool:
    s = text.strip().casefold()
    return s in {"înapoi", "inapoi", "back"}


def _is_home_text(text: str) -> bool:
    s = text.strip().casefold()
    return s in {"acasă", "acasa", "home"}


def _price_prompt_key(sales_mode_raw: str | None) -> str:
    if sales_mode_raw == TourSalesMode.FULL_BUS.value:
        return "supplier_offer_prompt_price_full_bus"
    return "supplier_offer_prompt_price_per_seat"


def _payment_mode_label(language_code: str | None, raw: str) -> str:
    if raw == SupplierOfferPaymentMode.ASSISTED_CLOSURE.value:
        return translate(language_code, "supplier_offer_opt_payment_assisted_closure")
    return translate(language_code, "supplier_offer_opt_payment_platform_checkout")


def _sales_mode_label(language_code: str | None, raw: str) -> str:
    if raw == TourSalesMode.FULL_BUS.value:
        return translate(language_code, "supplier_offer_opt_sales_full_bus")
    return translate(language_code, "supplier_offer_opt_sales_per_seat")


def _review_summary(language_code: str | None, *, data: dict[str, object]) -> str:
    return translate(
        language_code,
        "supplier_offer_review_summary",
        title=str(data.get("title", "")),
        departure_point=str(data.get("departure_point", "")),
        departure_datetime=str(data.get("departure_datetime", "")).replace("T", " "),
        return_datetime=str(data.get("return_datetime", "")).replace("T", " "),
        sales_mode=_sales_mode_label(language_code, str(data.get("sales_mode", TourSalesMode.PER_SEAT.value))),
        payment_mode=_payment_mode_label(
            language_code,
            str(data.get("payment_mode", SupplierOfferPaymentMode.PLATFORM_CHECKOUT.value)),
        ),
        base_price=str(data.get("base_price", "")),
        currency=str(data.get("currency", "")),
        description=str(data.get("description", "")),
        program_text=str(data.get("program_text", "")),
        included_text=str(data.get("included_text", "")),
        excluded_text=str(data.get("excluded_text", "")),
        cover=str(data.get("cover_media_display", "—")),
        schedule_note=str(data.get("schedule_note", "")),
        short_hook_line=str(data.get("optional_short_hook", "") or "—"),
        marketing_line=str(data.get("optional_marketing", "") or "—"),
        discount_line=str(data.get("discount_line", "—") or "—"),
        seats_total=str(data.get("seats_total", "") or "—"),
        vehicle_label=str(data.get("vehicle_label", "") or "—"),
    )


def _schedule_note(data: dict) -> str:
    if data.get("schedule_kind") == "recurring" and (data.get("recurrence_rule") or "").strip():
        return str(data.get("recurrence_rule", ""))
    return "—"


def _cover_display(data: dict) -> str:
    if data.get("cover_step") == "none":
        return "no photo yet (declared)"
    return str(data.get("cover_media_reference") or "—")


def _build_create_payload(supplier: Supplier, data: dict) -> SupplierOfferCreate:
    dep = datetime.fromisoformat(str(data["departure_datetime"]))
    ret = datetime.fromisoformat(str(data["return_datetime"]))
    cover = (data.get("cover_media_reference") or "").strip() or None
    no_photo = data.get("cover_step") == "none"
    media_refs: list[dict] | None = None
    if cover:
        media_refs = [{"role": "cover", "ref": cover}]

    rtype: str | None = None
    rrule: str | None = None
    if data.get("schedule_kind") == "recurring":
        rtype = "custom"
        rrule = (data.get("recurrence_rule") or "").strip() or None

    sup_notes: str | None = (data.get("supplier_admin_notes") or "").strip() or None
    if no_photo:
        no_tag = "No cover/photo at intake (declared by supplier)."
        sup_notes = f"{sup_notes} | {no_tag}" if sup_notes else no_tag

    return SupplierOfferCreate(
        title=str(data["title"]),
        description=str(data["description"]),
        program_text=str(data.get("program_text") or ""),
        departure_datetime=dep,
        return_datetime=ret,
        vehicle_label=str(data.get("vehicle_label", "")).strip() or "—",
        boarding_places_text=str(data.get("departure_point", "")).strip() or None,
        seats_total=int(data["seats_total"]),
        base_price=Decimal(str(data["base_price"])),
        currency=str(data["currency"]),
        service_composition=supplier.onboarding_service_composition or SupplierServiceComposition.TRANSPORT_ONLY,
        sales_mode=TourSalesMode(str(data["sales_mode"])),
        payment_mode=SupplierOfferPaymentMode(str(data["payment_mode"])),
        included_text=(data.get("included_text") or "").strip() or None,
        excluded_text=(data.get("excluded_text") or "").strip() or None,
        cover_media_reference=cover,
        media_references=media_refs,
        recurrence_type=rtype,
        recurrence_rule=rrule,
        supplier_admin_notes=sup_notes,
    )


def _first_draft_offer_id(session, *, supplier_id: int) -> int | None:
    offers = SupplierOfferService().list_offers(session, supplier_id=supplier_id, limit=50, offset=0)
    for o in offers:
        if o.lifecycle_status == SupplierOfferLifecycle.DRAFT:
            return o.id
    return None


async def _prompt_for_state(
    message: Message,
    state: FSMContext,
    *,
    language_code: str | None,
    state_name: str | None = None,
) -> None:
    step_name = state_name or _state_name_from_context(await state.get_state())
    if step_name == "entering_title":
        await message.answer(translate(language_code, "supplier_offer_prompt_title"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_route_facts":
        await message.answer(translate(language_code, "supplier_offer_prompt_route_facts"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "choosing_schedule_kind":
        await message.answer(
            translate(language_code, "supplier_offer_prompt_schedule_kind"),
            reply_markup=_schedule_kind_keyboard(language_code).as_markup(),
        )
        return
    if step_name == "entering_recurrence_summary":
        await message.answer(translate(language_code, "supplier_offer_prompt_recurrence"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_departure_point":
        await message.answer(translate(language_code, "supplier_offer_prompt_departure_point"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_departure_datetime":
        await message.answer(translate(language_code, "supplier_offer_prompt_departure"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_return_datetime":
        await message.answer(translate(language_code, "supplier_offer_prompt_return"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_seats_total":
        await message.answer(translate(language_code, "supplier_offer_prompt_seats_total"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "choosing_sales_mode":
        await message.answer(
            translate(language_code, "supplier_offer_prompt_sales_mode"),
            reply_markup=_sales_mode_keyboard(language_code).as_markup(),
        )
        return
    if step_name == "choosing_payment_mode":
        await message.answer(
            translate(language_code, "supplier_offer_prompt_payment_mode"),
            reply_markup=_payment_mode_keyboard(language_code).as_markup(),
        )
        return
    if step_name == "entering_base_price":
        sdata = await state.get_data()
        await message.answer(translate(language_code, _price_prompt_key(str(sdata.get("sales_mode")))), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_currency":
        await message.answer(translate(language_code, "supplier_offer_prompt_currency"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_program_text":
        await message.answer(translate(language_code, "supplier_offer_prompt_program_facts"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_included_text":
        await message.answer(translate(language_code, "supplier_offer_prompt_included"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_excluded_text":
        await message.answer(translate(language_code, "supplier_offer_prompt_excluded"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "choosing_cover_media":
        await message.answer(
            translate(language_code, "supplier_offer_prompt_cover"),
            reply_markup=_cover_choice_keyboard(language_code).as_markup(),
        )
        return
    if step_name == "entering_cover_url":
        await message.answer(translate(language_code, "supplier_offer_prompt_cover_url"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "entering_vehicle_or_notes":
        await message.answer(translate(language_code, "supplier_offer_prompt_vehicle_or_notes"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "optional_short_hook":
        await message.answer(translate(language_code, "supplier_offer_prompt_optional_short_hook"), reply_markup=_reply_nav_keyboard(language_code))
        return
    if step_name == "optional_marketing_summary":
        await message.answer(
            translate(language_code, "supplier_offer_prompt_optional_marketing"), reply_markup=_reply_nav_keyboard(language_code)
        )
        return
    if step_name == "optional_discount_line":
        await message.answer(
            translate(language_code, "supplier_offer_prompt_optional_discount"), reply_markup=_reply_nav_keyboard(language_code)
        )
        return
    if step_name == "awaiting_submit_action":
        sdata = await state.get_data()
        offer_id = int(sdata.get("draft_offer_id") or 0)
        if offer_id > 0:
            await message.answer(
                translate(language_code, "supplier_offer_submit_ready"),
                reply_markup=_submit_keyboard(language_code, offer_id=offer_id).as_markup(),
            )


def _intake_state(prev: str) -> State:
    st = getattr(SupplierOfferIntakeState, prev, None)
    if not isinstance(st, State):
        raise KeyError(prev)
    return st


async def _go_back_message(message: Message, state: FSMContext, language_code: str | None) -> bool:
    state_name = _state_name_from_context(await state.get_state())
    data = await state.get_data()
    prev = _back_state_name(state_name, data)
    if not prev:
        return False
    try:
        await state.set_state(_intake_state(prev))
    except KeyError:
        return False
    await _prompt_for_state(message, state, language_code=language_code, state_name=prev)
    return True


async def _go_back_callback(query: CallbackQuery, state: FSMContext, language_code: str | None) -> bool:
    if query.message is None:
        return False
    data = await state.get_data()
    state_name = _state_name_from_context(await state.get_state())
    prev = _back_state_name(state_name, data)
    if not prev:
        return False
    try:
        await state.set_state(_intake_state(prev))
    except KeyError:
        return False
    await _prompt_for_state(query.message, state, language_code=language_code, state_name=prev)
    return True


async def _handle_nav_text(message: Message, state: FSMContext, language_code: str | None) -> bool:
    text = (message.text or "").strip()
    if not text:
        return False
    if _is_home_text(text):
        await state.clear()
        await message.answer(translate(language_code, "supplier_offer_cancelled_home"))
        return True
    if not _is_back_text(text):
        return False
    return await _go_back_message(message, state, language_code)


async def _handle_nav_callback(query: CallbackQuery, state: FSMContext, language_code: str | None) -> bool:
    if query.data == SUPPLIER_OFFER_NAV_HOME_CALLBACK:
        await state.clear()
        if query.message is not None:
            await query.message.answer(translate(language_code, "supplier_offer_cancelled_home"))
        await query.answer()
        return True
    if query.data != SUPPLIER_OFFER_NAV_BACK_CALLBACK:
        return False
    if query.message is None:
        await query.answer()
        return True
    await _go_back_callback(query, state, language_code)
    await query.answer()
    return True


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
    await message.answer(translate(lg, "supplier_offer_start"))
    await message.answer(translate(lg, "supplier_offer_nav_help"), reply_markup=_reply_nav_keyboard(lg))
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_title")


@router.message(SupplierOfferIntakeState.entering_title)
async def intake_title(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if lg is None:
        lg = message.from_user.language_code or "en"
    try:
        if await _handle_nav_text(message, state, lg):
            return
        if not message.text:
            await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
            return
        title = message.text.strip()
        if len(title) < 2:
            await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
            return
        await state.update_data(title=title)
        await state.set_state(SupplierOfferIntakeState.entering_route_facts)
        await _prompt_for_state(message, state, language_code=lg, state_name="entering_route_facts")
    except Exception:
        await message.answer(translate(lg, "supplier_offer_step_processing_failed"), reply_markup=_reply_nav_keyboard(lg))


@router.message(SupplierOfferIntakeState.entering_route_facts)
async def intake_route_facts(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if lg is None:
        lg = message.from_user.language_code or "en"
    try:
        if await _handle_nav_text(message, state, lg):
            return
        if not message.text:
            await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
            return
        description = message.text.strip()
        if len(description) < 2:
            await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
            return
        await state.update_data(description=description)
        await state.set_state(SupplierOfferIntakeState.choosing_schedule_kind)
        await _prompt_for_state(message, state, language_code=lg, state_name="choosing_schedule_kind")
    except Exception:
        await message.answer(translate(lg, "supplier_offer_step_processing_failed"), reply_markup=_reply_nav_keyboard(lg))


@router.callback_query(
    SupplierOfferIntakeState.choosing_schedule_kind,
    F.data.in_({SUPPLIER_OFFER_SCHEDULE_ONE, SUPPLIER_OFFER_SCHEDULE_RECURRING}),
)
async def intake_schedule_kind_cb(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _handle_nav_callback(query, state, lg):
        return
    if query.data == SUPPLIER_OFFER_SCHEDULE_ONE:
        await state.update_data(schedule_kind="one_trip", recurrence_rule="")
        await state.set_state(SupplierOfferIntakeState.entering_departure_point)
        await _prompt_for_state(query.message, state, language_code=lg, state_name="entering_departure_point")
    else:
        await state.update_data(schedule_kind="recurring")
        await state.set_state(SupplierOfferIntakeState.entering_recurrence_summary)
        await _prompt_for_state(query.message, state, language_code=lg, state_name="entering_recurrence_summary")
    await query.answer()


@router.message(SupplierOfferIntakeState.choosing_schedule_kind)
async def intake_schedule_kind_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    await message.answer(translate(lg, "supplier_offer_use_buttons_schedule"), reply_markup=_schedule_kind_keyboard(lg).as_markup())


@router.message(SupplierOfferIntakeState.entering_recurrence_summary)
async def intake_recurrence_summary(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    line = message.text.strip()
    if len(line) < 4:
        await message.answer(translate(lg, "supplier_offer_recurrence_too_short"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(recurrence_rule=line)
    await state.set_state(SupplierOfferIntakeState.entering_departure_point)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_departure_point")


@router.message(SupplierOfferIntakeState.entering_departure_point)
async def intake_departure_point(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    departure_point = message.text.strip()
    if len(departure_point) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(departure_point=departure_point)
    await state.set_state(SupplierOfferIntakeState.entering_departure_datetime)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_departure_datetime")


@router.message(SupplierOfferIntakeState.entering_departure_datetime)
async def intake_departure(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    dt = _parse_dt(message.text)
    if dt is None:
        await message.answer(translate(lg, "supplier_offer_invalid_datetime"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(departure_datetime=dt.isoformat())
    await state.set_state(SupplierOfferIntakeState.entering_return_datetime)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_return_datetime")


@router.message(SupplierOfferIntakeState.entering_return_datetime)
async def intake_return(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    ret = _parse_dt(message.text)
    if ret is None:
        await message.answer(translate(lg, "supplier_offer_invalid_datetime"), reply_markup=_reply_nav_keyboard(lg))
        return
    data = await state.get_data()
    dep = _parse_dt(str(data.get("departure_datetime") or ""))
    if dep is None or ret < dep:
        await message.answer(translate(lg, "supplier_offer_invalid_return_before_departure"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(return_datetime=ret.isoformat())
    await state.set_state(SupplierOfferIntakeState.entering_seats_total)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_seats_total")


@router.message(SupplierOfferIntakeState.entering_seats_total)
async def intake_seats(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    seats = _parse_positive_int(message.text)
    if seats is None:
        await message.answer(translate(lg, "supplier_offer_invalid_seats_total"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(seats_total=seats)
    await state.set_state(SupplierOfferIntakeState.choosing_sales_mode)
    await _prompt_for_state(message, state, language_code=lg, state_name="choosing_sales_mode")


@router.message(SupplierOfferIntakeState.choosing_sales_mode)
async def intake_sales_mode_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    await message.answer(translate(lg, "supplier_offer_use_buttons_sales"), reply_markup=_sales_mode_keyboard(lg).as_markup())


@router.message(SupplierOfferIntakeState.entering_base_price)
async def intake_price(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    price = _parse_non_negative_decimal(message.text)
    if price is None:
        await message.answer(translate(lg, "supplier_offer_invalid_price"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(base_price=str(price))
    await state.set_state(SupplierOfferIntakeState.entering_currency)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_currency")


@router.message(SupplierOfferIntakeState.entering_currency)
async def intake_currency(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    currency = message.text.strip().upper()
    if not _CURRENCY_RE.fullmatch(currency):
        await message.answer(translate(lg, "supplier_offer_invalid_currency"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(currency=currency)
    await state.set_state(SupplierOfferIntakeState.entering_program_text)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_program_text")


@router.callback_query(
    SupplierOfferIntakeState.choosing_sales_mode,
    F.data.startswith(SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX),
)
async def intake_sales_mode(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _handle_nav_callback(query, state, lg):
        return
    raw = query.data.removeprefix(SUPPLIER_OFFER_SALES_MODE_CALLBACK_PREFIX)
    try:
        mode = TourSalesMode(raw)
    except ValueError:
        await query.answer()
        return
    await state.update_data(sales_mode=mode.value)
    await state.set_state(SupplierOfferIntakeState.choosing_payment_mode)
    await _prompt_for_state(query.message, state, language_code=lg, state_name="choosing_payment_mode")
    await query.answer()


@router.callback_query(
    SupplierOfferIntakeState.choosing_payment_mode,
    F.data.startswith(SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX),
)
async def intake_payment_mode(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _handle_nav_callback(query, state, lg):
        return
    raw = query.data.removeprefix(SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX)
    try:
        mode = SupplierOfferPaymentMode(raw)
    except ValueError:
        await query.answer()
        return
    await state.update_data(payment_mode=mode.value)
    await state.set_state(SupplierOfferIntakeState.entering_base_price)
    await _prompt_for_state(query.message, state, language_code=lg, state_name="entering_base_price")
    await query.answer()


@router.message(SupplierOfferIntakeState.choosing_payment_mode)
async def intake_payment_mode_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    await message.answer(translate(lg, "supplier_offer_use_buttons_payment"), reply_markup=_payment_mode_keyboard(lg).as_markup())


@router.message(SupplierOfferIntakeState.entering_program_text)
async def intake_program_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    program_text = message.text.strip()
    if len(program_text) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(program_text=program_text)
    await state.set_state(SupplierOfferIntakeState.entering_included_text)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_included_text")


@router.message(SupplierOfferIntakeState.entering_included_text)
async def intake_included(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    inc = message.text.strip()
    if len(inc) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(included_text=inc)
    await state.set_state(SupplierOfferIntakeState.entering_excluded_text)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_excluded_text")


@router.message(SupplierOfferIntakeState.entering_excluded_text)
async def intake_excluded(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    exc = message.text.strip()
    if len(exc) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(excluded_text=exc)
    await state.set_state(SupplierOfferIntakeState.choosing_cover_media)
    await _prompt_for_state(message, state, language_code=lg, state_name="choosing_cover_media")


@router.callback_query(
    SupplierOfferIntakeState.choosing_cover_media,
    F.data.in_({SUPPLIER_OFFER_COVER_URL, SUPPLIER_OFFER_COVER_NONE}),
)
async def intake_cover_choice_cb(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _handle_nav_callback(query, state, lg):
        return
    if query.data == SUPPLIER_OFFER_COVER_URL:
        await state.update_data(cover_step="url")
        await state.set_state(SupplierOfferIntakeState.entering_cover_url)
        await _prompt_for_state(query.message, state, language_code=lg, state_name="entering_cover_url")
    else:
        await state.update_data(cover_step="none", cover_media_reference="")
        await state.set_state(SupplierOfferIntakeState.entering_vehicle_or_notes)
        await _prompt_for_state(query.message, state, language_code=lg, state_name="entering_vehicle_or_notes")
    await query.answer()


@router.message(SupplierOfferIntakeState.choosing_cover_media)
async def intake_cover_text_fallback(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    await message.answer(translate(lg, "supplier_offer_use_buttons_cover"), reply_markup=_cover_choice_keyboard(lg).as_markup())


@router.message(SupplierOfferIntakeState.entering_cover_url)
async def intake_cover_url(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    url = message.text.strip()
    if not _URL_START_RE.search(url) or len(url) < 8:
        await message.answer(translate(lg, "supplier_offer_invalid_cover_url"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(cover_media_reference=url, cover_step="url")
    await state.set_state(SupplierOfferIntakeState.entering_vehicle_or_notes)
    await _prompt_for_state(message, state, language_code=lg, state_name="entering_vehicle_or_notes")


@router.message(SupplierOfferIntakeState.entering_vehicle_or_notes)
async def intake_vehicle_or_notes(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    vehicle_or_notes = message.text.strip()
    if len(vehicle_or_notes) < 2:
        await message.answer(translate(lg, "supplier_offer_invalid_short"), reply_markup=_reply_nav_keyboard(lg))
        return
    await state.update_data(vehicle_label=vehicle_or_notes, transport_notes=None)
    data = await state.get_data()
    with SessionLocal() as session:
        supplier = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=message.from_user.id)
        status_code = _supplier_access_status(supplier)
        if supplier is None or status_code != "approved":
            await state.clear()
            await message.answer(translate(lg, _gate_message_key(status_code)))
            return
        assert supplier is not None
        create_payload = _build_create_payload(supplier, {**data, "vehicle_label": vehicle_or_notes})
        svc = SupplierOfferService()
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
                        boarding_places_text=create_payload.boarding_places_text,
                        seats_total=create_payload.seats_total,
                        base_price=create_payload.base_price,
                        currency=create_payload.currency,
                        service_composition=create_payload.service_composition,
                        sales_mode=create_payload.sales_mode,
                        payment_mode=create_payload.payment_mode,
                        included_text=create_payload.included_text,
                        excluded_text=create_payload.excluded_text,
                        cover_media_reference=create_payload.cover_media_reference,
                        media_references=create_payload.media_references,
                        recurrence_type=create_payload.recurrence_type,
                        recurrence_rule=create_payload.recurrence_rule,
                        supplier_admin_notes=create_payload.supplier_admin_notes,
                        lifecycle_status=SupplierOfferLifecycle.DRAFT,
                    ),
                )
        except SupplierOfferReadinessError:
            await message.answer(translate(lg, "supplier_offer_submit_failed"))
            return
        session.commit()
    await state.update_data(draft_offer_id=saved.id)
    data2 = {**data, "vehicle_label": vehicle_or_notes, "draft_offer_id": saved.id}
    data2["schedule_note"] = _schedule_note(data2)
    data2["cover_media_display"] = _cover_display({**data2, "cover_step": data2.get("cover_step")})
    await state.set_state(SupplierOfferIntakeState.optional_short_hook)
    await message.answer(translate(lg, "supplier_offer_draft_saved", offer_id=str(saved.id)))
    await _prompt_for_state(message, state, language_code=lg, state_name="optional_short_hook")


@router.message(SupplierOfferIntakeState.optional_short_hook)
async def intake_optional_short_hook(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    if not _is_skip_text(message.text):
        await state.update_data(optional_short_hook=message.text.strip()[:512])
    await state.set_state(SupplierOfferIntakeState.optional_marketing_summary)
    await _prompt_for_state(message, state, language_code=lg, state_name="optional_marketing_summary")


@router.message(SupplierOfferIntakeState.optional_marketing_summary)
async def intake_optional_marketing(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    if not _is_skip_text(message.text):
        await state.update_data(optional_marketing=message.text.strip()[:4000])
    await state.set_state(SupplierOfferIntakeState.optional_discount_line)
    await _prompt_for_state(message, state, language_code=lg, state_name="optional_discount_line")


def _parse_iso_datetime_loose(s: str) -> datetime | None:
    t = s.strip()
    for cand in (t, t.replace("Z", "+00:00") if t.endswith("Z") else t, f"{t}T00:00:00+00:00" if len(t) == 10 and t[4] == "-" else ""):
        if not cand:
            continue
        try:
            d = datetime.fromisoformat(cand)
            if d.tzinfo is None:
                return d.replace(tzinfo=UTC)
            return d.astimezone(UTC)
        except ValueError:
            continue
    return _parse_dt(s)


def _parse_discount_line(raw: str) -> dict[str, object]:
    line = raw.strip()
    if _is_skip_text(line) or not line or line == "-":
        return {}
    parts = [p.strip() for p in line.split("|", maxsplit=3)]
    if len(parts) < 1:
        return {}
    out: dict[str, object] = {}
    if parts[0]:
        out["discount_code"] = parts[0][:64]
    if len(parts) > 1 and parts[1]:
        try:
            p = Decimal(parts[1].replace(",", "."))
            if 0 <= p <= 100:
                out["discount_percent"] = p
        except InvalidOperation:
            pass
    if len(parts) > 2 and parts[2]:
        try:
            out["discount_amount"] = Decimal(parts[2].replace(",", "."))
        except InvalidOperation:
            pass
    if len(parts) > 3 and parts[3]:
        dtp = _parse_iso_datetime_loose(parts[3])
        if dtp is not None:
            out["discount_valid_until"] = dtp
    return out


@router.message(SupplierOfferIntakeState.optional_discount_line)
async def intake_optional_discount_line(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    data = await state.get_data()
    offer_id = int(data.get("draft_offer_id") or 0)
    dextra = _parse_discount_line(message.text)
    with SessionLocal() as session:
        supplier = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=message.from_user.id)
        if supplier is None or _supplier_access_status(supplier) != "approved" or offer_id <= 0:
            await state.clear()
            return
        udict: dict[str, object] = {}
        if data.get("optional_short_hook"):
            udict["short_hook"] = str(data["optional_short_hook"])[:512]
        if data.get("optional_marketing"):
            udict["marketing_summary"] = str(data["optional_marketing"])[:10000]
        udict.update(dextra)
        udict = {k: v for k, v in udict.items() if v is not None}
        if udict:
            try:
                SupplierOfferService().update_offer(
                    session,
                    supplier_id=supplier.id,
                    offer_id=offer_id,
                    payload=SupplierOfferUpdate.model_validate(udict),
                )
            except (SupplierOfferReadinessError, SupplierOfferImmutableError, SupplierOfferLifecycleNotAllowedError, SupplierOfferNotFoundError, ValueError):
                await message.answer(translate(lg, "supplier_offer_submit_failed"), reply_markup=_reply_nav_keyboard(lg))
                return
        session.commit()
    sdata = await state.get_data()
    sdata["schedule_note"] = _schedule_note(sdata)
    sdata["cover_media_display"] = _cover_display(sdata)
    sdata["optional_short_hook"] = sdata.get("optional_short_hook") or "—"
    sdata["optional_marketing"] = sdata.get("optional_marketing") or "—"
    sdata["discount_line"] = message.text.strip() if not _is_skip_text(message.text) and message.text.strip() != "-" else "—"
    await state.set_state(SupplierOfferIntakeState.awaiting_submit_action)
    await message.answer(_review_summary(lg, data=sdata))
    await _prompt_for_state(message, state, language_code=lg, state_name="awaiting_submit_action")


@router.callback_query(
    SupplierOfferIntakeState.awaiting_submit_action,
    F.data.startswith(SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX),
)
async def submit_offer_to_moderation(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.message is None or query.data is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    if await _handle_nav_callback(query, state, lg):
        return
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
            if query.message is not None:
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
            if query.message is not None:
                await query.message.answer(translate(lg, "supplier_offer_submit_failed"))
            await query.answer()
            return
        session.commit()
    await state.clear()
    if query.message is not None:
        await query.message.answer(translate(lg, "supplier_offer_submitted", offer_id=str(offer_id)))
    await query.answer()


@router.message(SupplierOfferIntakeState.awaiting_submit_action)
async def submit_state_text_fallback(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    lg = await _resolve_language(message.from_user.id, message.from_user.language_code)
    if await _handle_nav_text(message, state, lg):
        return
    data = await state.get_data()
    offer_id = int(data.get("draft_offer_id") or 0)
    if offer_id <= 0:
        await message.answer(translate(lg, "supplier_offer_submit_failed"))
        return
    await message.answer(translate(lg, "supplier_offer_use_buttons_submit"), reply_markup=_submit_keyboard(lg, offer_id=offer_id).as_markup())


@router.callback_query(
    F.data.startswith(SUPPLIER_OFFER_NAV_CALLBACK_PREFIX),
)
async def supplier_offer_nav_callback(query: CallbackQuery, state: FSMContext) -> None:
    st = await state.get_state()
    if st is None or "SupplierOfferIntakeState" not in str(st):
        return
    if query.from_user is None:
        return
    lg = await _resolve_language(query.from_user.id, query.from_user.language_code)
    await _handle_nav_callback(query, state, lg)
