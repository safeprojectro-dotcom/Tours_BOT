from __future__ import annotations

from decimal import Decimal

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    BUDGET_OPTION_ANY,
    BROWSE_TOURS_CALLBACK,
    CANCEL_DESTINATION_INPUT_CALLBACK,
    CHANGE_PREPARED_BOARDING_CALLBACK,
    CHANGE_PREPARED_SEATS_CALLBACK,
    CHANGE_LANGUAGE_CALLBACK,
    CREATE_TEMPORARY_RESERVATION_CALLBACK,
    DATE_OPTION_ANY,
    DATE_OPTION_NEXT_30_DAYS,
    DATE_OPTION_WEEKEND,
    FILTER_BUDGET_CALLBACK_PREFIX,
    FILTER_BY_BUDGET_CALLBACK,
    FILTER_BY_DATE_CALLBACK,
    FILTER_BY_DESTINATION_CALLBACK,
    FILTER_DATE_CALLBACK_PREFIX,
    LANGUAGE_CALLBACK_PREFIX,
    LANGUAGE_LABELS,
    PREPARE_BOARDING_POINT_CALLBACK_PREFIX,
    PREPARE_RESERVATION_CALLBACK_PREFIX,
    PREPARE_SEAT_COUNT_CALLBACK_PREFIX,
    REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX,
    START_PAYMENT_ENTRY_CALLBACK_PREFIX,
    TOUR_CALLBACK_PREFIX,
)
from app.bot.messages import format_budget_filter_summary, translate
from app.schemas.prepared import CatalogTourCardRead, PreparedTourDetailRead


def build_language_keyboard(language_codes: tuple[str, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for language_code in language_codes:
        builder.button(
            text=LANGUAGE_LABELS.get(language_code, language_code.upper()),
            callback_data=f"{LANGUAGE_CALLBACK_PREFIX}{language_code}",
        )
    builder.adjust(2)
    return builder.as_markup()


def _mini_app_bookings_url(mini_app_url: str | None) -> str | None:
    if not mini_app_url:
        return None
    return f"{mini_app_url.rstrip('/')}/bookings"


def _mini_app_web_app_button(*, text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))


def append_mini_app_url_buttons(
    builder: InlineKeyboardBuilder,
    *,
    language_code: str | None,
    mini_app_url: str | None,
) -> None:
    """Primary + secondary Mini App entry (catalog root and /bookings)."""
    if not mini_app_url:
        return
    builder.row(_mini_app_web_app_button(text=translate(language_code, "open_mini_app"), url=mini_app_url))
    bookings_url = _mini_app_bookings_url(mini_app_url)
    if bookings_url:
        builder.row(
            _mini_app_web_app_button(
                text=translate(language_code, "open_mini_app_bookings"),
                url=bookings_url,
            )
        )


def build_mini_app_entry_keyboard(
    *,
    language_code: str | None,
    mini_app_url: str | None,
) -> InlineKeyboardMarkup | None:
    """Compact CTA: open Mini App + My bookings (e.g. /bookings, /help)."""
    if not mini_app_url:
        return None
    builder = InlineKeyboardBuilder()
    append_mini_app_url_buttons(builder, language_code=language_code, mini_app_url=mini_app_url)
    return builder.as_markup()


def build_private_home_keyboard(
    *,
    language_code: str | None,
    mini_app_url: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    append_mini_app_url_buttons(builder, language_code=language_code, mini_app_url=mini_app_url)
    # Secondary: lightweight filters in chat (MVP fallback).
    builder.button(
        text=translate(language_code, "browse_by_date"),
        callback_data=FILTER_BY_DATE_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "browse_by_destination"),
        callback_data=FILTER_BY_DESTINATION_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "browse_by_budget"),
        callback_data=FILTER_BY_BUDGET_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "open_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "change_language"),
        callback_data=CHANGE_LANGUAGE_CALLBACK,
    )
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()


def build_catalog_keyboard(
    cards: list[CatalogTourCardRead],
    *,
    language_code: str | None,
    mini_app_url: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for card in cards:
        builder.button(text=card.title, callback_data=f"{TOUR_CALLBACK_PREFIX}{card.id}")
    builder.button(
        text=translate(language_code, "change_language"),
        callback_data=CHANGE_LANGUAGE_CALLBACK,
    )
    if mini_app_url:
        builder.row(
            _mini_app_web_app_button(text=translate(language_code, "open_mini_app"), url=mini_app_url)
        )
    builder.adjust(1)
    return builder.as_markup()


def build_tour_detail_keyboard(
    *,
    language_code: str | None,
    tour_id: int | None = None,
    mini_app_url: str | None = None,
    per_seat_self_service_allowed: bool = True,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if tour_id is not None and per_seat_self_service_allowed:
        builder.button(
            text=translate(language_code, "prepare_reservation"),
            callback_data=f"{PREPARE_RESERVATION_CALLBACK_PREFIX}{tour_id}",
        )
    elif tour_id is not None and not per_seat_self_service_allowed:
        builder.button(
            text=translate(language_code, "request_booking_assistance"),
            callback_data=f"{REQUEST_BOOKING_ASSISTANCE_CALLBACK_PREFIX}:{tour_id}",
        )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "change_language"),
        callback_data=CHANGE_LANGUAGE_CALLBACK,
    )
    if mini_app_url:
        builder.row(
            _mini_app_web_app_button(text=translate(language_code, "open_mini_app"), url=mini_app_url)
        )
    builder.adjust(1)
    return builder.as_markup()


def build_date_filter_keyboard(language_code: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translate(language_code, "date_weekend"),
        callback_data=f"{FILTER_DATE_CALLBACK_PREFIX}{DATE_OPTION_WEEKEND}",
    )
    builder.button(
        text=translate(language_code, "date_next_30_days"),
        callback_data=f"{FILTER_DATE_CALLBACK_PREFIX}{DATE_OPTION_NEXT_30_DAYS}",
    )
    builder.button(
        text=translate(language_code, "date_any"),
        callback_data=f"{FILTER_DATE_CALLBACK_PREFIX}{DATE_OPTION_ANY}",
    )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.adjust(1)
    return builder.as_markup()


def build_budget_filter_keyboard(
    *,
    language_code: str | None,
    currency: str,
    presets: tuple[Decimal, ...],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in presets:
        label = format_budget_filter_summary(language_code, amount=amount, currency=currency)
        builder.button(
            text=label,
            callback_data=f"{FILTER_BUDGET_CALLBACK_PREFIX}{amount}",
        )
    builder.button(
        text=translate(language_code, "budget_any"),
        callback_data=f"{FILTER_BUDGET_CALLBACK_PREFIX}{BUDGET_OPTION_ANY}",
    )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.adjust(1)
    return builder.as_markup()


def build_destination_prompt_keyboard(language_code: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translate(language_code, "destination_cancel"),
        callback_data=CANCEL_DESTINATION_INPUT_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.adjust(1)
    return builder.as_markup()


def build_seat_count_keyboard(
    language_code: str | None,
    *,
    seat_options: tuple[int, ...],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for seat_count in seat_options:
        builder.button(
            text=str(seat_count),
            callback_data=f"{PREPARE_SEAT_COUNT_CALLBACK_PREFIX}{seat_count}",
        )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.adjust(3)
    return builder.as_markup()


def build_boarding_point_keyboard(
    language_code: str | None,
    *,
    detail: PreparedTourDetailRead,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for point in detail.boarding_points:
        builder.button(
            text=f"{point.city} | {point.time:%H:%M}",
            callback_data=f"{PREPARE_BOARDING_POINT_CALLBACK_PREFIX}{point.id}",
        )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.adjust(1)
    return builder.as_markup()


def build_preparation_summary_keyboard(
    language_code: str | None,
    *,
    mini_app_url: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translate(language_code, "create_temporary_reservation"),
        callback_data=CREATE_TEMPORARY_RESERVATION_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "change_seat_count"),
        callback_data=CHANGE_PREPARED_SEATS_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "change_boarding_point"),
        callback_data=CHANGE_PREPARED_BOARDING_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "back_to_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    if mini_app_url:
        builder.row(
            _mini_app_web_app_button(text=translate(language_code, "open_mini_app"), url=mini_app_url)
        )
    builder.adjust(1)
    return builder.as_markup()


def build_temporary_reservation_keyboard(
    language_code: str | None,
    *,
    order_id: int,
    mini_app_url: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translate(language_code, "continue_to_payment"),
        callback_data=f"{START_PAYMENT_ENTRY_CALLBACK_PREFIX}{order_id}",
    )
    builder.button(
        text=translate(language_code, "open_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "change_language"),
        callback_data=CHANGE_LANGUAGE_CALLBACK,
    )
    if mini_app_url:
        builder.row(
            _mini_app_web_app_button(text=translate(language_code, "open_mini_app"), url=mini_app_url)
        )
    builder.adjust(1)
    return builder.as_markup()


def build_payment_entry_keyboard(
    language_code: str | None,
    *,
    mini_app_url: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translate(language_code, "open_catalog"),
        callback_data=BROWSE_TOURS_CALLBACK,
    )
    builder.button(
        text=translate(language_code, "change_language"),
        callback_data=CHANGE_LANGUAGE_CALLBACK,
    )
    if mini_app_url:
        builder.row(
            _mini_app_web_app_button(text=translate(language_code, "open_mini_app"), url=mini_app_url)
        )
    builder.adjust(1)
    return builder.as_markup()
