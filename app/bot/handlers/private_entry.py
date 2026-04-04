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
)
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.order_summary import OrderSummaryService
from app.services.payment_entry import PaymentEntryService
from app.services.reservation_creation import TemporaryReservationService

router = Router(name="private-entry")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")


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

        if user.preferred_language is None:
            await state.set_state(PrivateEntryState.choosing_language)
            await answer_and_register_language_prompt(
                message,
                translate(settings.telegram_default_language, "language_prompt"),
                reply_markup=build_language_keyboard(settings.telegram_supported_language_codes),
            )
            return

        await state.clear()
        detail = browse_service.get_tour_detail_from_start_arg(
            session,
            start_arg=command.args if command is not None else None,
            language_code=user.preferred_language,
        )
        if detail is not None:
            await message.answer(
                format_tour_detail_message(user.preferred_language, detail),
                reply_markup=build_tour_detail_keyboard(
                    language_code=user.preferred_language,
                    tour_id=detail.tour.id,
                    mini_app_url=settings.telegram_mini_app_url,
                ),
            )
            return

    await _send_catalog_overview(
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
    await _send_catalog_overview(
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
    await message.answer(
        translate(effective, "contact_command_reply"),
        reply_markup=build_mini_app_entry_keyboard(
            language_code=effective,
            mini_app_url=settings.telegram_mini_app_url,
        ),
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

    language_code = updated_user.preferred_language if updated_user is not None else settings.telegram_default_language
    await state.clear()
    await callback.message.answer(
        translate(language_code, "language_saved", language_name=language_name(language_code)),
        reply_markup=build_private_home_keyboard(
            language_code=language_code,
            mini_app_url=settings.telegram_mini_app_url,
        ),
    )
    await _send_catalog_overview(callback.message, language_code=language_code)


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
    with SessionLocal() as session:
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
