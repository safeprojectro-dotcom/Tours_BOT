"""Private chat handlers — catalog, reservations, payments (Phase 7 / Step 6: ``/start grp_*`` intros; Step 7: ``grp_followup`` handoff persistence)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import NotSlashCommandFilter
from app.bot.constants import (
    BROWSE_TOURS_CALLBACK,
    CANCEL_DESTINATION_INPUT_CALLBACK,
    CHANGE_PREPARED_BOARDING_CALLBACK,
    CHANGE_PREPARED_SEATS_CALLBACK,
    CHANGE_LANGUAGE_CALLBACK,
    CREATE_TEMPORARY_RESERVATION_CALLBACK,
    REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX,
    FILTER_BUDGET_CALLBACK_PREFIX,
    FILTER_BY_BUDGET_CALLBACK,
    FILTER_BY_DATE_CALLBACK,
    FILTER_BY_DESTINATION_CALLBACK,
    FILTER_DATE_CALLBACK_PREFIX,
    LANGUAGE_CALLBACK_PREFIX,
    PRIVATE_SOURCE_CHANNEL,
    PREPARE_BOARDING_POINT_CALLBACK_PREFIX,
    PREPARE_RESERVATION_CALLBACK_PREFIX,
    PREPARE_SEAT_COUNT_CALLBACK_PREFIX,
    START_PAYMENT_ENTRY_CALLBACK_PREFIX,
    TOUR_CALLBACK_PREFIX,
)
from app.bot.keyboards import (
    build_boarding_point_keyboard,
    build_catalog_keyboard,
    build_budget_filter_keyboard,
    build_date_filter_keyboard,
    build_destination_prompt_keyboard,
    build_language_keyboard,
    build_mini_app_entry_keyboard,
    build_private_home_keyboard,
    build_private_sup_offer_start_keyboard,
    build_preparation_summary_keyboard,
    build_payment_entry_keyboard,
    build_seat_count_keyboard,
    build_temporary_reservation_keyboard,
    build_tour_detail_keyboard,
)
from app.bot.messages import (
    format_budget_filter_summary,
    format_catalog_message,
    format_date_filter_summary,
    format_destination_filter_summary,
    format_filtered_catalog_message,
    format_payment_entry_message,
    format_reservation_preparation_summary,
    format_temporary_reservation_confirmation,
    format_tour_detail_message,
    format_welcome,
    language_name,
    translate,
)
from app.bot.services import (
    PrivateReservationPreparationService,
    PrivateTourBrowseService,
    TelegramUserContextService,
)
from app.bot.state import PrivateEntryState
from app.bot.transient_messages import (
    answer_and_register_filter_step,
    answer_and_register_language_prompt,
    register_catalog_bundle,
    send_or_edit_home_catalog_pair,
    send_or_edit_router_home,
)
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.tour import Tour
from app.repositories.tour import TourRepository
from app.services.handoff_entry import HandoffEntryService
from app.models.enums import SupplierOfferLifecycle
from app.models.supplier import SupplierOffer
from app.services.group_private_cta import (
    START_PAYLOAD_GRP_FOLLOWUP,
    START_PAYLOAD_GRP_PRIVATE,
    match_group_cta_start_payload,
)
from app.services.supplier_offer_bot_start_routing import resolve_sup_offer_start_mini_app_routing
from app.services.supplier_offer_deep_link import parse_supplier_offer_start_arg
from app.services.order_summary import OrderSummaryService
from app.services.payment_entry import PaymentEntryService
from app.services.reservation_creation import TemporaryReservationService
from app.services.tour_sales_mode_policy import TourSalesModePolicyService

router = Router(name="private-entry")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

# Deep-link /start args are stashed here when the user has no preferred_language yet (channel link first open).
PENDING_PRIVATE_START_ARGS_KEY = "pending_private_start_args"


@router.message(CommandStart())
async def handle_start(
    message: Message,
    state: FSMContext,
    command: CommandObject | None = None,
) -> None:
    if message.from_user is None:
        return

    settings = get_settings()
    user_service = _user_service()
    browse_service = PrivateTourBrowseService()

    with SessionLocal() as session:
        user = user_service.sync_private_user(
            session,
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            telegram_language_code=message.from_user.language_code,
        )
        session.commit()

        raw_start = (command.args.strip() if command is not None and command.args else None) or None

        if user.preferred_language is None:
            if raw_start:
                await state.update_data({PENDING_PRIVATE_START_ARGS_KEY: raw_start})
            await state.set_state(PrivateEntryState.choosing_language)
            await answer_and_register_language_prompt(
                message,
                translate(settings.telegram_default_language, "language_prompt"),
                reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
            )
            return

        await state.clear()
        grp_payload = match_group_cta_start_payload(raw_start)
        if grp_payload is not None:
            if grp_payload == START_PAYLOAD_GRP_PRIVATE:
                intro_key = "start_grp_private_intro"
            else:
                entry_svc = HandoffEntryService()
                intro_key = entry_svc.group_followup_private_intro_key(
                    session,
                    user_id=user.id,
                )
            await message.answer(translate(user.preferred_language, intro_key))
            if grp_payload == START_PAYLOAD_GRP_FOLLOWUP:
                await _persist_group_followup_handoff(
                    message,
                    telegram_language_code=message.from_user.language_code,
                )
            await _send_catalog_overview(
                message,
                language_code=user.preferred_language,
                prefer_edit=True,
            )
            return

        showcase_offer_id = parse_supplier_offer_start_arg(raw_start)
        if showcase_offer_id is not None:
            sup_offer = session.get(SupplierOffer, showcase_offer_id)
            if sup_offer is None or sup_offer.lifecycle_status != SupplierOfferLifecycle.PUBLISHED:
                await message.answer(translate(user.preferred_language, "sup_offer_not_available"))
                await _send_catalog_overview(
                    message,
                    language_code=user.preferred_language,
                    prefer_edit=True,
                )
                return

            display_title = (sup_offer.title or "").strip()
            if not display_title:
                display_title = translate(user.preferred_language, "sup_offer_intro_title_fallback")
            nav = resolve_sup_offer_start_mini_app_routing(
                session,
                offer=sup_offer,
                mini_app_base_url=settings.telegram_mini_app_url or "",
            )
            lg = user.preferred_language
            if nav.exact_tour_mini_app_url and nav.linked_tour_code:
                intro = translate(
                    lg,
                    "start_sup_offer_intro_exact_tour",
                    title=display_title,
                    tour_code=nav.linked_tour_code,
                )
            else:
                intro = translate(
                    lg,
                    "start_sup_offer_intro",
                    title=display_title,
                )
            await message.answer(
                intro,
                reply_markup=build_private_sup_offer_start_keyboard(
                    language_code=lg,
                    mini_app_url=settings.telegram_mini_app_url,
                    supplier_offer_id=sup_offer.id,
                    exact_tour_mini_app_url=nav.exact_tour_mini_app_url,
                ),
            )
            # B11: exact Tour Mini App router — do not duplicate generic chat catalog below.
            if nav.exact_tour_mini_app_url and nav.linked_tour_code:
                return
            await _send_catalog_overview(
                message,
                language_code=user.preferred_language,
                prefer_edit=True,
            )
            return

        detail = browse_service.get_tour_detail_from_start_arg(
            session,
            start_arg=raw_start,
            language_code=user.preferred_language,
        )
        if detail is not None:
            await message.answer(
                format_tour_detail_message(user.preferred_language, detail),
                reply_markup=build_tour_detail_keyboard(
                    language_code=user.preferred_language,
                    tour_id=detail.tour.id,
                    mini_app_url=settings.telegram_mini_app_url,
                    tour_code=detail.tour.code,
                    per_seat_self_service_allowed=detail.sales_mode_policy.per_seat_self_service_allowed,
                ),
            )
            return

    await _send_router_home(
        message,
        language_code=user.preferred_language,
        prefer_edit=True,
    )


@router.message(Command("language"))
async def handle_language_command(message: Message, state: FSMContext) -> None:
    settings = get_settings()
    await state.set_state(PrivateEntryState.choosing_language)
    await answer_and_register_language_prompt(
        message,
        translate(settings.telegram_default_language, "language_prompt"),
        reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
    )


@router.message(Command("tours"))
async def handle_tours_command(message: Message, state: FSMContext) -> None:
    language_code = await _resolve_message_language(message)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    await state.clear()
    await _send_router_home(
        message,
        language_code=language_code,
        prefer_edit=True,
    )


@router.message(Command("help"))
async def handle_help_command(message: Message) -> None:
    settings = get_settings()
    language_code = await _resolve_message_language(message)
    effective = language_code or settings.telegram_default_language
    await message.answer(
        translate(effective, "help_command_reply"),
        reply_markup=build_mini_app_entry_keyboard(
            language_code=effective,
            mini_app_url=settings.telegram_mini_app_url,
        ),
    )


@router.message(Command("bookings"))
async def handle_bookings_command(message: Message) -> None:
    settings = get_settings()
    language_code = await _resolve_message_language(message)
    effective = language_code or settings.telegram_default_language
    await message.answer(
        translate(effective, "bookings_command_reply"),
        reply_markup=build_mini_app_entry_keyboard(
            language_code=effective,
            mini_app_url=settings.telegram_mini_app_url,
        ),
    )


@router.message(Command("contact"))
async def handle_contact_command(message: Message) -> None:
    settings = get_settings()
    language_code = await _resolve_message_language(message)
    effective = language_code or settings.telegram_default_language
    markup = build_mini_app_entry_keyboard(
        language_code=effective,
        mini_app_url=settings.telegram_mini_app_url,
    )
    await message.answer(translate(effective, "contact_command_reply"), reply_markup=markup)
    await _send_handoff_follow_up(
        message,
        language_code=effective,
        reason=HandoffEntryService.REASON_PRIVATE_CONTACT,
    )


@router.message(Command("human"))
async def handle_human_command(message: Message) -> None:
    settings = get_settings()
    language_code = await _resolve_message_language(message)
    effective = language_code or settings.telegram_default_language
    markup = build_mini_app_entry_keyboard(
        language_code=effective,
        mini_app_url=settings.telegram_mini_app_url,
    )
    await message.answer(translate(effective, "human_command_reply"), reply_markup=markup)
    await _send_handoff_follow_up(
        message,
        language_code=effective,
        reason=HandoffEntryService.REASON_PRIVATE_HUMAN,
    )


@router.callback_query(F.data == CHANGE_LANGUAGE_CALLBACK)
async def handle_change_language(callback: CallbackQuery, state: FSMContext) -> None:
    settings = get_settings()
    await state.set_state(PrivateEntryState.choosing_language)
    await callback.answer()
    if callback.message is None:
        return

    await answer_and_register_language_prompt(
        callback.message,
        translate(settings.telegram_default_language, "language_prompt"),
        reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
    )


@router.callback_query(F.data == BROWSE_TOURS_CALLBACK)
async def handle_browse_tours(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    await state.clear()
    await _send_catalog_overview(callback.message, language_code=language_code)


@router.callback_query(F.data == FILTER_BY_DATE_CALLBACK)
async def handle_filter_by_date(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    await state.clear()
    await answer_and_register_filter_step(
        callback.message,
        translate(language_code, "date_prompt"),
        reply_markup=build_date_filter_keyboard(language_code),
    )


@router.callback_query(F.data == FILTER_BY_DESTINATION_CALLBACK)
async def handle_filter_by_destination(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    await state.set_state(PrivateEntryState.entering_destination_preference)
    await answer_and_register_filter_step(
        callback.message,
        translate(language_code, "destination_prompt"),
        reply_markup=build_destination_prompt_keyboard(language_code),
    )


@router.callback_query(F.data == FILTER_BY_BUDGET_CALLBACK)
async def handle_filter_by_budget(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    browse_service = PrivateTourBrowseService()
    with SessionLocal() as session:
        currency = browse_service.get_budget_filter_currency(
            session,
            language_code=language_code,
        )

    await state.clear()
    if currency is None:
        await answer_and_register_filter_step(
            callback.message,
            translate(language_code, "budget_not_available"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await answer_and_register_filter_step(
        callback.message,
        translate(language_code, "budget_prompt"),
        reply_markup=build_budget_filter_keyboard(
            language_code=language_code,
            currency=currency,
            presets=browse_service.get_budget_presets(),
        ),
    )


@router.callback_query(F.data == CANCEL_DESTINATION_INPUT_CALLBACK)
async def handle_cancel_destination_input(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    await state.clear()
    await _send_catalog_overview(callback.message, language_code=language_code)


@router.callback_query(F.data.startswith(FILTER_DATE_CALLBACK_PREFIX))
async def handle_date_filter_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await callback.answer()
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    selected_option = callback.data.removeprefix(FILTER_DATE_CALLBACK_PREFIX)
    browse_service = PrivateTourBrowseService()
    filters = browse_service.build_date_filters(selected_option)

    await callback.answer()
    if filters is None:
        return

    await state.clear()
    await _send_filtered_catalog_overview(
        callback.message,
        language_code=language_code,
        filters=filters,
        filter_summary=format_date_filter_summary(language_code, selected_option),
    )


@router.callback_query(F.data.startswith(FILTER_BUDGET_CALLBACK_PREFIX))
async def handle_budget_filter_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await callback.answer()
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    selected_option = callback.data.removeprefix(FILTER_BUDGET_CALLBACK_PREFIX)
    browse_service = PrivateTourBrowseService()
    filters = browse_service.build_budget_filters(selected_option)

    await callback.answer()
    if filters is None:
        return

    with SessionLocal() as session:
        currency = browse_service.get_budget_filter_currency(
            session,
            language_code=language_code,
        )

    if currency is None:
        await state.clear()
        await answer_and_register_filter_step(
            callback.message,
            translate(language_code, "budget_not_available"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await state.clear()
    await _send_filtered_catalog_overview(
        callback.message,
        language_code=language_code,
        filters=filters,
        filter_summary=format_budget_filter_summary(
            language_code,
            amount=filters.max_price,
            currency=currency,
        ),
    )


@router.callback_query(F.data.startswith(LANGUAGE_CALLBACK_PREFIX))
async def handle_language_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    selected_language = callback.data.removeprefix(LANGUAGE_CALLBACK_PREFIX) if callback.data else ""
    settings = get_settings()
    user_service = _user_service()

    with SessionLocal() as session:
        user_service.sync_private_user(
            session,
            telegram_user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            telegram_language_code=callback.from_user.language_code,
        )
        updated_user = user_service.set_preferred_language(
            session,
            telegram_user_id=callback.from_user.id,
            language_code=selected_language,
        )
        session.commit()

    await callback.answer()
    if callback.message is None:
        return

    data = await state.get_data()
    raw_pending = data.get(PENDING_PRIVATE_START_ARGS_KEY)
    pending_start: str | None
    if isinstance(raw_pending, str):
        p = raw_pending.strip()
        pending_start = p if p else None
    else:
        pending_start = None

    language_code = updated_user.preferred_language if updated_user is not None else settings.telegram_default_language
    await state.clear()
    await callback.message.answer(
        translate(language_code, "language_saved", language_name=language_name(language_code)),
        reply_markup=build_private_home_keyboard(
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
    )
    if pending_start is not None:
        cmd = CommandObject(prefix="/", command="start", mention=None, args=pending_start)
        await handle_start(callback.message, state, cmd)
        return

    await _send_router_home(callback.message, language_code=language_code, prefer_edit=True)


@router.callback_query(F.data.startswith(f"{REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX}:"))
async def handle_request_booking_assistance(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    await state.clear()
    settings = get_settings()
    markup = build_mini_app_entry_keyboard(
        language_code=language_code,
        mini_app_url=settings.telegram_mini_app_url,
    )
    await callback.message.answer(
        translate(language_code, "contact_command_reply"),
        reply_markup=markup,
    )
    handoff_reason = HandoffEntryService.REASON_PRIVATE_CONTACT
    raw_id = (
        callback.data.removeprefix(f"{REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX}:")
        if callback.data
        else ""
    )
    try:
        assistance_tour_id = int(raw_id)
    except ValueError:
        assistance_tour_id = 0
    if assistance_tour_id > 0:
        with SessionLocal() as session:
            tour = session.get(Tour, assistance_tour_id)
            if tour is not None and not TourSalesModePolicyService.policy_for_sales_mode(
                tour.sales_mode
            ).per_seat_self_service_allowed:
                handoff_reason = HandoffEntryService.build_full_bus_sales_assistance_reason(
                    tour_code=tour.code,
                    sales_mode=tour.sales_mode.value,
                    channel="private",
                )
    await _send_handoff_follow_up(
        callback.message,
        language_code=language_code,
        reason=handoff_reason,
    )


@router.callback_query(F.data.startswith(PREPARE_RESERVATION_CALLBACK_PREFIX))
async def handle_prepare_reservation(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await callback.answer()
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    try:
        tour_id = int(callback.data.removeprefix(PREPARE_RESERVATION_CALLBACK_PREFIX))
    except ValueError:
        await callback.answer()
        return

    await callback.answer()
    await _send_seat_count_prompt(
        callback.message,
        state=state,
        language_code=language_code,
        tour_id=tour_id,
    )


@router.callback_query(F.data.startswith(PREPARE_SEAT_COUNT_CALLBACK_PREFIX))
async def handle_preparation_seat_count(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await callback.answer()
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    state_data = await state.get_data()
    tour_id = state_data.get("prepared_tour_id")
    if not isinstance(tour_id, int):
        await callback.answer()
        await _send_catalog_overview(callback.message, language_code=language_code)
        return

    try:
        seats_count = int(callback.data.removeprefix(PREPARE_SEAT_COUNT_CALLBACK_PREFIX))
    except ValueError:
        await callback.answer()
        return

    await callback.answer()
    await _send_boarding_point_prompt(
        callback.message,
        state=state,
        language_code=language_code,
        tour_id=tour_id,
        seats_count=seats_count,
    )


@router.callback_query(F.data.startswith(PREPARE_BOARDING_POINT_CALLBACK_PREFIX))
async def handle_preparation_boarding_point(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await callback.answer()
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    state_data = await state.get_data()
    tour_id = state_data.get("prepared_tour_id")
    seats_count = state_data.get("prepared_seats_count")
    if not isinstance(tour_id, int) or not isinstance(seats_count, int):
        await callback.answer()
        await _send_catalog_overview(callback.message, language_code=language_code)
        return

    try:
        boarding_point_id = int(callback.data.removeprefix(PREPARE_BOARDING_POINT_CALLBACK_PREFIX))
    except ValueError:
        await callback.answer()
        return

    await callback.answer()
    await _send_preparation_summary(
        callback.message,
        state=state,
        language_code=language_code,
        tour_id=tour_id,
        seats_count=seats_count,
        boarding_point_id=boarding_point_id,
    )


@router.callback_query(F.data == CHANGE_PREPARED_SEATS_CALLBACK)
async def handle_change_prepared_seats(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None or language_code is None:
        return

    state_data = await state.get_data()
    tour_id = state_data.get("prepared_tour_id")
    if not isinstance(tour_id, int):
        await _send_catalog_overview(callback.message, language_code=language_code)
        return

    await _send_seat_count_prompt(
        callback.message,
        state=state,
        language_code=language_code,
        tour_id=tour_id,
    )


@router.callback_query(F.data == CHANGE_PREPARED_BOARDING_CALLBACK)
async def handle_change_prepared_boarding(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None or language_code is None:
        return

    state_data = await state.get_data()
    tour_id = state_data.get("prepared_tour_id")
    seats_count = state_data.get("prepared_seats_count")
    if not isinstance(tour_id, int) or not isinstance(seats_count, int):
        await _send_catalog_overview(callback.message, language_code=language_code)
        return

    await _send_boarding_point_prompt(
        callback.message,
        state=state,
        language_code=language_code,
        tour_id=tour_id,
        seats_count=seats_count,
    )


@router.callback_query(F.data == CREATE_TEMPORARY_RESERVATION_CALLBACK)
async def handle_create_temporary_reservation(callback: CallbackQuery, state: FSMContext) -> None:
    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if callback.message is None:
        return

    if language_code is None or callback.from_user is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    state_data = await state.get_data()
    tour_id = state_data.get("prepared_tour_id")
    seats_count = state_data.get("prepared_seats_count")
    boarding_point_id = state_data.get("prepared_boarding_point_id")
    if not all(isinstance(value, int) for value in (tour_id, seats_count, boarding_point_id)):
        await state.clear()
        await _send_catalog_overview(callback.message, language_code=language_code)
        return

    user_service = _user_service()
    reservation_service = TemporaryReservationService()
    order_summary_service = OrderSummaryService()
    tour_repository = TourRepository()
    with SessionLocal() as session:
        tour = tour_repository.get(session, tour_id)
        if tour is None or not TourSalesModePolicyService.policy_for_sales_mode(
            tour.sales_mode
        ).per_seat_self_service_allowed:
            await callback.message.answer(
                translate(language_code, "private_self_service_reservation_blocked"),
                reply_markup=build_private_home_keyboard(
                    language_code=language_code,
                    mini_app_url=get_settings().telegram_mini_app_url,
                ),
            )
            return

        user = user_service.sync_private_user(
            session,
            telegram_user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            telegram_language_code=callback.from_user.language_code,
        )
        order = reservation_service.create_temporary_reservation(
            session,
            user_id=user.id,
            tour_id=tour_id,
            boarding_point_id=boarding_point_id,
            seats_count=seats_count,
            source_channel=PRIVATE_SOURCE_CHANNEL,
        )
        if order is None:
            session.rollback()
        else:
            session.commit()
            order = order_summary_service.get_order_summary(
                session,
                order_id=order.id,
                language_code=language_code,
            )

    if order is None:
        await callback.message.answer(
            translate(language_code, "reservation_creation_failed"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await state.clear()
    await callback.message.answer(
        format_temporary_reservation_confirmation(language_code, order),
        reply_markup=build_temporary_reservation_keyboard(
            language_code,
            order_id=order.order.id,
            mini_app_url=get_settings().telegram_mini_app_url,
        ),
    )


@router.callback_query(F.data.startswith(START_PAYMENT_ENTRY_CALLBACK_PREFIX))
async def handle_start_payment_entry(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    await callback.answer()
    if language_code is None or callback.from_user is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    try:
        order_id = int(callback.data.removeprefix(START_PAYMENT_ENTRY_CALLBACK_PREFIX))
    except ValueError:
        return

    user_service = _user_service()
    payment_entry_service = PaymentEntryService()
    with SessionLocal() as session:
        user = user_service.sync_private_user(
            session,
            telegram_user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            telegram_language_code=callback.from_user.language_code,
        )
        payment_entry = payment_entry_service.start_payment_entry(
            session,
            order_id=order_id,
            user_id=user.id,
        )
        if payment_entry is None:
            session.rollback()
        else:
            session.commit()

    if payment_entry is None:
        await callback.message.answer(
            translate(language_code, "payment_entry_failed"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await state.clear()
    await callback.message.answer(
        format_payment_entry_message(language_code, payment_entry),
        reply_markup=build_payment_entry_keyboard(
            language_code,
            mini_app_url=get_settings().telegram_mini_app_url,
        ),
    )


@router.callback_query(F.data.startswith(TOUR_CALLBACK_PREFIX))
async def handle_tour_detail(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    language_code = await _resolve_callback_language(callback)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await callback.answer()
        await answer_and_register_language_prompt(
            callback.message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    try:
        tour_id = int(callback.data.removeprefix(TOUR_CALLBACK_PREFIX))
    except ValueError:
        await callback.answer()
        await callback.message.answer(
            translate(language_code, "tour_missing"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    detail_service = PrivateTourBrowseService()
    settings = get_settings()
    with SessionLocal() as session:
        detail = detail_service.get_tour_detail(
            session,
            tour_id=tour_id,
            language_code=language_code,
        )

    await callback.answer()
    await state.clear()
    if detail is None:
        await callback.message.answer(
            translate(language_code, "tour_missing"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=settings.telegram_mini_app_url,
            ),
        )
        return

    await callback.message.answer(
        format_tour_detail_message(language_code, detail),
        reply_markup=build_tour_detail_keyboard(
            language_code=language_code,
            tour_id=detail.tour.id,
            mini_app_url=settings.telegram_mini_app_url,
            tour_code=detail.tour.code,
            per_seat_self_service_allowed=detail.sales_mode_policy.per_seat_self_service_allowed,
        ),
    )


@router.message(PrivateEntryState.choosing_language, NotSlashCommandFilter())
async def handle_language_state_message(message: Message) -> None:
    settings = get_settings()
    await answer_and_register_language_prompt(
        message,
        translate(settings.telegram_default_language, "language_prompt"),
        reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
    )


@router.message(PrivateEntryState.entering_destination_preference, NotSlashCommandFilter())
async def handle_destination_preference_message(message: Message, state: FSMContext) -> None:
    language_code = await _resolve_message_language(message)
    if language_code is None:
        settings = get_settings()
        await state.set_state(PrivateEntryState.choosing_language)
        await answer_and_register_language_prompt(
            message,
            translate(settings.telegram_default_language, "language_prompt"),
            reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
        )
        return

    query = (message.text or "").strip()
    browse_service = PrivateTourBrowseService()
    filters = browse_service.build_destination_filters(query)
    if filters is None:
        await answer_and_register_filter_step(
            message,
            translate(language_code, "destination_empty"),
            reply_markup=build_destination_prompt_keyboard(language_code),
        )
        return

    await state.clear()
    await _send_filtered_catalog_overview(
        message,
        language_code=language_code,
        filters=filters,
        filter_summary=format_destination_filter_summary(language_code, query),
    )


async def _send_router_home(
    message: Message,
    *,
    language_code: str,
    prefer_edit: bool = False,
) -> None:
    """B10.6B: generic entry — Mini App CTAs + optional chat filters; no automatic in-chat tour cards."""
    settings = get_settings()
    await send_or_edit_router_home(
        message,
        text=translate(language_code, "router_home_body"),
        reply_markup=build_private_home_keyboard(
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
        prefer_edit=prefer_edit,
    )


async def _send_catalog_overview(
    message: Message,
    *,
    language_code: str,
    prefer_edit: bool = False,
) -> None:
    settings = get_settings()
    browse_service = PrivateTourBrowseService()
    with SessionLocal() as session:
        cards = browse_service.list_entry_tours(
            session,
            language_code=language_code,
        )

    await send_or_edit_home_catalog_pair(
        message,
        welcome_text=format_welcome(language_code),
        welcome_markup=build_private_home_keyboard(
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
        catalog_text=format_catalog_message(language_code, cards),
        catalog_markup=build_catalog_keyboard(
            cards,
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
        prefer_edit=prefer_edit,
    )


async def _send_filtered_catalog_overview(
    message: Message,
    *,
    language_code: str,
    filters,
    filter_summary: str,
) -> None:
    settings = get_settings()
    browse_service = PrivateTourBrowseService()
    with SessionLocal() as session:
        cards = browse_service.list_entry_tours_filtered(
            session,
            language_code=language_code,
            filters=filters,
        )

    sent_w = await message.answer(
        format_welcome(language_code),
        reply_markup=build_private_home_keyboard(
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
    )
    sent_c = await message.answer(
        format_filtered_catalog_message(
            language_code,
            cards,
            filter_summary=filter_summary,
        ),
        reply_markup=build_catalog_keyboard(
            cards,
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
    )
    await register_catalog_bundle(message.bot, message.chat.id, sent_w.message_id, sent_c.message_id)


async def _send_seat_count_prompt(
    message: Message,
    *,
    state: FSMContext,
    language_code: str,
    tour_id: int,
) -> None:
    preparation_service = PrivateReservationPreparationService()
    with SessionLocal() as session:
        detail = preparation_service.get_preparable_tour(
            session,
            tour_id=tour_id,
            language_code=language_code,
        )

    if detail is None:
        await state.clear()
        await message.answer(
            translate(language_code, "preparation_unavailable"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    seat_options = preparation_service.list_seat_count_options(detail)
    if not seat_options:
        await state.clear()
        await message.answer(
            translate(language_code, "private_self_service_reservation_blocked"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await state.set_state(PrivateEntryState.choosing_preparation_seat_count)
    await state.update_data(prepared_tour_id=tour_id, prepared_boarding_point_id=None, prepared_seats_count=None)
    await message.answer(
        translate(language_code, "seat_count_prompt"),
        reply_markup=build_seat_count_keyboard(
            language_code,
            seat_options=seat_options,
        ),
    )


async def _send_boarding_point_prompt(
    message: Message,
    *,
    state: FSMContext,
    language_code: str,
    tour_id: int,
    seats_count: int,
) -> None:
    preparation_service = PrivateReservationPreparationService()
    with SessionLocal() as session:
        detail = preparation_service.get_preparable_tour(
            session,
            tour_id=tour_id,
            language_code=language_code,
        )

    if detail is None or seats_count not in preparation_service.list_seat_count_options(detail):
        await state.clear()
        await message.answer(
            translate(language_code, "preparation_unavailable"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await state.set_state(PrivateEntryState.choosing_preparation_boarding_point)
    await state.update_data(
        prepared_tour_id=tour_id,
        prepared_seats_count=seats_count,
        prepared_boarding_point_id=None,
    )
    await message.answer(
        translate(language_code, "boarding_point_prompt"),
        reply_markup=build_boarding_point_keyboard(
            language_code,
            detail=detail,
        ),
    )


async def _send_preparation_summary(
    message: Message,
    *,
    state: FSMContext,
    language_code: str,
    tour_id: int,
    seats_count: int,
    boarding_point_id: int,
) -> None:
    preparation_service = PrivateReservationPreparationService()
    with SessionLocal() as session:
        summary = preparation_service.build_preparation_summary(
            session,
            tour_id=tour_id,
            seats_count=seats_count,
            boarding_point_id=boarding_point_id,
            language_code=language_code,
        )

    if summary is None:
        await state.clear()
        await message.answer(
            translate(language_code, "preparation_unavailable"),
            reply_markup=build_private_home_keyboard(
                language_code=language_code,
                mini_app_url=get_settings().telegram_mini_app_url,
            ),
        )
        return

    await state.update_data(
        prepared_tour_id=tour_id,
        prepared_seats_count=seats_count,
        prepared_boarding_point_id=boarding_point_id,
    )
    await state.set_state(PrivateEntryState.reviewing_reservation_preparation)
    await message.answer(
        format_reservation_preparation_summary(language_code, summary),
        reply_markup=build_preparation_summary_keyboard(
            language_code,
            mini_app_url=get_settings().telegram_mini_app_url,
        ),
    )


async def _send_handoff_follow_up(message: Message, *, language_code: str, reason: str) -> None:
    if message.from_user is None:
        return
    settings = get_settings()
    markup = build_mini_app_entry_keyboard(
        language_code=language_code,
        mini_app_url=settings.telegram_mini_app_url,
    )
    hid: int | None = None
    with SessionLocal() as session:
        svc = HandoffEntryService()
        hid = svc.create_for_telegram_user(
            session,
            telegram_user_id=message.from_user.id,
            reason=reason,
            telegram_language_code=message.from_user.language_code,
        )
        if hid is None:
            session.rollback()
        else:
            session.commit()
    if hid is None:
        await message.answer(translate(language_code, "handoff_request_failed"), reply_markup=markup)
        return
    await message.answer(
        translate(language_code, "handoff_request_recorded", ref=str(hid)),
        reply_markup=markup,
    )


async def _persist_group_followup_handoff(
    message: Message,
    *,
    telegram_language_code: str | None,
) -> None:
    """Phase 7 / Step 7 — narrow handoff row for ``/start grp_followup`` only; no user-visible extra step."""
    if message.from_user is None:
        return
    with SessionLocal() as session:
        svc = HandoffEntryService()
        hid = svc.create_for_group_followup_start(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=telegram_language_code,
        )
        if hid is None:
            session.rollback()
            return
        session.commit()


async def _resolve_message_language(message: Message) -> str | None:
    if message.from_user is None:
        return None

    with SessionLocal() as session:
        return _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )


async def _resolve_callback_language(callback: CallbackQuery) -> str | None:
    if callback.from_user is None:
        return None

    with SessionLocal() as session:
        return _user_service().resolve_language(
            session,
            telegram_user_id=callback.from_user.id,
            telegram_language_code=callback.from_user.language_code,
        )


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(
        supported_language_codes=settings.telegram_supported_language_codes,
    )
