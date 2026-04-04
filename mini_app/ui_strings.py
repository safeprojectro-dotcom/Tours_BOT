"""
UI-shell copy for the Flet Mini App (navigation, buttons, common labels).

Tour titles/descriptions still come from the API and may use fallback translation there.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

# Keys: English + Romanian where provided; other language codes fall back to English.
_STR: dict[str, dict[str, str]] = {
    "en": {
        "catalog_title": "Tours catalog",
        "catalog_subtitle": "Main booking flow: browse here, then use My bookings for reservation and payment status. "
        "Optional filters below mirror the quick shortcuts in the bot chat.",
        "btn_my_bookings": "My bookings",
        "btn_language_settings": "Language & settings",
        "btn_help": "Help",
        "filters_heading": "Filters",
        "label_destination": "Destination",
        "hint_destination": "Belgrade",
        "label_departure_from": "Departure from",
        "label_departure_to": "Departure to",
        "label_max_price": "Max price",
        "hint_date": "YYYY-MM-DD",
        "hint_price": "150",
        "btn_apply_filters": "Apply filters",
        "btn_clear": "Clear",
        "loading_tours": "Loading tours...",
        "empty_catalog": "No tours match the current filters. Try clearing one or more filters.",
        "view_details": "View details",
        "catalog_card_no_description": "Open the detail screen to see the full tour description.",
        "badge_seats_available": "Seats available",
        "badge_sold_out": "Sold out",
        "loading_tour_details": "Loading tour details...",
        "back_to_catalog": "Back to catalog",
        "settings": "Settings",
        "prepare_reservation": "Prepare reservation",
        "fallback_translation_note": "No translation is available for your selected language for this tour; "
        "showing the next available language (see Language & settings).",
        "section_overview": "Overview",
        "section_program": "Program",
        "section_included": "Included",
        "section_excluded": "Not included",
        "section_boarding_points": "Boarding points",
        "boarding_no_details": "Boarding point details are not available for this tour yet.",
        "boarding_departure_time": "Departure time",
        "boarding_notes_fallback": "No extra notes for this boarding point.",
        "loading_reservation_options": "Loading reservation options...",
        "back_to_tour_details": "Back to tour details",
        "prep_note": "Pick seats and boarding, preview the summary, then confirm to create a temporary reservation "
        "(dev user {dev_id}). Payment entry follows on the next screen.",
        "label_seats": "Seats",
        "label_boarding": "Boarding point",
        "btn_preview_summary": "Preview summary",
        "btn_confirm_reservation": "Confirm reservation",
        "prep_summary_title": "Preparation summary",
        "prep_line_seats": "Seats: {n}",
        "prep_line_boarding": "Boarding point: {city}, {addr}",
        "prep_line_boarding_time": "Boarding time: {t}",
        "prep_line_estimated": "Estimated total: {amount} {currency}",
        "prep_hold_note": "Your seats are not held until you confirm. This creates a temporary hold; "
        "complete payment before the deadline on the next screens.",
        "loading_reservation": "Loading reservation...",
        "back_to_preparation": "Back to preparation",
        "reservation_confirmed_title": "Reservation confirmed",
        "reservation_hold_intro": "Temporary hold is active. Pay before the deadline or the seats may be released.",
        "continue_to_payment": "Continue to payment",
        "line_reservation_ref": "Reservation reference: #{id}",
        "line_amount_to_pay": "Amount to pay: {amount} {currency}",
        "line_payment_status": "Payment status: {status}",
        "starting_payment": "Starting payment entry...",
        "payment_title": "Payment",
        "payment_intro": "Reservation is temporary. Complete payment before the hold expires. "
        "Details below come from the server; payment is not marked successful until the backend confirms it.",
        "line_pay_before": "Pay before: {when}",
        "line_reservation_expiry_na": "Reservation expiry time is not available.",
        "line_amount_due": "Amount due: {amount} {currency}",
        "line_payment_session_ref": "Payment session reference: {ref}",
        "payment_stub_notice": "Provider checkout inside this app is not connected yet. "
        "Pay Now explains the next step; nothing is shown as paid until reconciliation confirms it.",
        "payment_success_title": "Payment confirmed",
        "payment_success_intro": "The server recorded your payment. Your seats are confirmed for this departure.",
        "payment_success_booking_status": "Booking status: confirmed.",
        "pay_now": "Pay now",
        "loading_bookings": "Loading bookings...",
        "my_bookings_title": "My bookings",
        "my_bookings_subtitle": "Temporary holds, confirmed trips, and released holds (not paid) are listed below.",
        "no_bookings": "No bookings yet. Browse the catalog to reserve a tour.",
        "booking_seats_amount": "{amount} · {n} seat(s)",
        "booking_open": "Open",
        "loading_booking_detail": "Loading booking...",
        "booking_details_title": "Booking details",
        "cta_pay_now": "Pay now",
        "cta_browse_tours": "Browse tours",
        "cta_back_to_bookings": "Back to bookings",
        "help_title": "Help",
        "help_return_note": "Close the Mini App or switch back to the bot chat in Telegram anytime — "
        "the bot is your guide; this app is where you book and pay.",
        "loading_help": "Loading help...",
        "settings_title": "Language & settings",
        "settings_intro": "Choose the language for tour content and booking summaries. "
        "If a translation is missing, the app falls back and tells you.",
        "label_display_language": "Display language",
        "btn_save": "Save",
        "back": "Back",
        "payment_status_awaiting": "Waiting for payment",
        "payment_status_unpaid": "Not paid yet",
        "payment_status_paid": "Paid",
        "hold_no_deadline": "No payment deadline is set for this hold.",
        "hold_expired": "This hold has expired. Return to the catalog to check availability.",
        "hold_time_left": "Time left to pay: about {hours}h {minutes}m (deadline {deadline}).",
        "days_hours": "{n} day(s)",
        "facade_active_booking": "Temporary reservation (hold)",
        "facade_active_payment": "Awaiting payment to confirm your seats.",
        "facade_expired_booking": "Hold expired",
        "facade_expired_payment": "Payment was not completed in time; seats were released back to the tour.",
        "facade_released_booking": "Hold released — not paid",
        "facade_released_payment": "No payment was received before the deadline.",
        "facade_confirmed_booking": "Confirmed",
        "facade_confirmed_payment": "Paid — your booking is confirmed.",
        "facade_trip_booking": "Booking status",
        "facade_trip_payment": "Your trip — see details below.",
        "facade_other_booking": "Booking update",
        "facade_other_payment": "See booking details below.",
    },
    "ro": {
        "catalog_title": "Catalog tururi",
        "catalog_subtitle": "Flux principal: navigheaza aici, apoi foloseste Rezervarile mele pentru status. "
        "Filtrele de mai jos sunt scurtaturi optionale ca in bot.",
        "btn_my_bookings": "Rezervarile mele",
        "btn_language_settings": "Limba si setari",
        "btn_help": "Ajutor",
        "filters_heading": "Filtre",
        "label_destination": "Destinatie",
        "label_departure_from": "Plecare de la",
        "label_departure_to": "Plecare pana la",
        "label_max_price": "Pret max",
        "btn_apply_filters": "Aplica filtre",
        "btn_clear": "Sterge",
        "loading_tours": "Se incarca tururile...",
        "empty_catalog": "Niciun tur nu se potriveste. Incearca sa modifici filtrele.",
        "view_details": "Vezi detalii",
        "catalog_card_no_description": "Deschide ecranul de detalii pentru descrierea completa.",
        "badge_seats_available": "Locuri disponibile",
        "badge_sold_out": "Epuizat",
        "loading_tour_details": "Se incarca detaliile...",
        "back_to_catalog": "Inapoi la catalog",
        "settings": "Setari",
        "prepare_reservation": "Pregateste rezervarea",
        "section_boarding_points": "Puncte de imbarcare",
        "loading_reservation_options": "Se incarca optiunile...",
        "back_to_tour_details": "Inapoi la detalii tur",
        "label_seats": "Locuri",
        "label_boarding": "Punct imbarcare",
        "btn_preview_summary": "Previzualizeaza sumar",
        "btn_confirm_reservation": "Confirma rezervarea",
        "prep_summary_title": "Sumar pregatire",
        "loading_reservation": "Se incarca rezervarea...",
        "back_to_preparation": "Inapoi la pregatire",
        "reservation_confirmed_title": "Rezervare confirmata",
        "reservation_hold_intro": "Rezervare temporara activa. Plateste inainte de termen sau locurile pot fi eliberate.",
        "continue_to_payment": "Continua la plata",
        "line_reservation_ref": "Referinta rezervare: #{id}",
        "line_amount_to_pay": "De plata: {amount} {currency}",
        "line_payment_status": "Status plata: {status}",
        "starting_payment": "Se porneste plata...",
        "payment_title": "Plata",
        "line_pay_before": "Plateste inainte de: {when}",
        "line_reservation_expiry_na": "Termenul rezervarii nu este disponibil.",
        "line_amount_due": "Suma datorata: {amount} {currency}",
        "line_payment_session_ref": "Referinta sesiune plata: {ref}",
        "payment_stub_notice": "Plata prin provider in aceasta aplicatie nu e conectata inca. "
        "Plateste acum explica pasul urmator; plata nu e confirmata pana nu o confirma serverul.",
        "payment_success_title": "Plata confirmata",
        "payment_success_intro": "Serverul a inregistrat plata. Locurile tale sunt confirmate pentru aceasta plecare.",
        "payment_success_booking_status": "Status rezervare: confirmata.",
        "pay_now": "Plateste acum",
        "loading_bookings": "Se incarca rezervarile...",
        "my_bookings_title": "Rezervarile mele",
        "my_bookings_subtitle": "Rezervari temporare, calatorii confirmate si rezervari eliberate (neplatite) mai jos.",
        "no_bookings": "Inca nu ai rezervari. Deschide catalogul.",
        "booking_seats_amount": "{amount} · {n} loc(uri)",
        "booking_open": "Deschide",
        "loading_booking_detail": "Se incarca rezervarea...",
        "booking_details_title": "Detalii rezervare",
        "cta_pay_now": "Plateste acum",
        "cta_browse_tours": "Vezi tururi",
        "cta_back_to_bookings": "Inapoi la rezervari",
        "help_title": "Ajutor",
        "help_return_note": "Poti inchide Mini App sau reveni la chat-ul botului in Telegram oricand — "
        "botul este ghidul; aici plasezi rezervarea si plata.",
        "loading_help": "Se incarca ajutorul...",
        "settings_title": "Limba si setari",
        "label_display_language": "Limba afisaj",
        "btn_save": "Salveaza",
        "back": "Inapoi",
        "payment_status_awaiting": "In asteptarea platii",
        "payment_status_unpaid": "Neplatit",
        "payment_status_paid": "Platit",
        "hold_no_deadline": "Nu exista termen de plata setat.",
        "hold_expired": "Rezervarea a expirat. Revino la catalog.",
        "hold_time_left": "Timp ramas pentru plata: ~{hours}h {minutes}m (limita {deadline}).",
        "days_hours": "{n} zi(le)",
        "facade_active_booking": "Rezervare temporara (hold)",
        "facade_active_payment": "In asteptarea platii pentru confirmare.",
        "facade_expired_booking": "Hold expirat",
        "facade_expired_payment": "Plata nu s-a finalizat la timp; locurile au fost eliberate.",
        "facade_released_booking": "Hold eliberat — neplatit",
        "facade_released_payment": "Nu s-a primit plata inainte de termen.",
        "facade_confirmed_booking": "Confirmat",
        "facade_confirmed_payment": "Platit — rezervare confirmata.",
        "facade_trip_booking": "Status rezervare",
        "facade_trip_payment": "Calatoria ta — vezi detaliile.",
        "facade_other_booking": "Actualizare rezervare",
        "facade_other_payment": "Vezi detaliile rezervarii.",
    },
}


# Maps MiniAppBookingFacadeState value -> (booking_line_key, payment_line_key) in _STR tables.
_BOOKING_FACADE_SHELL_KEYS: dict[str, tuple[str, str]] = {
    "active_temporary_reservation": ("facade_active_booking", "facade_active_payment"),
    "expired_temporary_reservation": ("facade_expired_booking", "facade_expired_payment"),
    "cancelled_no_payment": ("facade_released_booking", "facade_released_payment"),
    "confirmed": ("facade_confirmed_booking", "facade_confirmed_payment"),
    "in_trip_pipeline": ("facade_trip_booking", "facade_trip_payment"),
    "other": ("facade_other_booking", "facade_other_payment"),
}


def booking_facade_labels(lang: str | None, facade_state: str) -> tuple[str, str]:
    """Localized booking title + payment line for My bookings / detail (API also sends English labels)."""
    bk, pk = _BOOKING_FACADE_SHELL_KEYS.get(
        facade_state,
        ("facade_other_booking", "facade_other_payment"),
    )
    return shell(lang, bk), shell(lang, pk)


def shell(lang: str | None, key: str, **kwargs: str) -> str:
    """Resolve UI-shell string; unknown language falls back to English."""
    code = (lang or "en").lower().split("-")[0]
    table = _STR.get(code, _STR["en"])
    template = table.get(key) or _STR["en"][key]
    return template.format(**kwargs) if kwargs else template


def hold_timer_hint(
    expires_at: datetime | None,
    lang: str | None,
    *,
    format_dt: Callable[[datetime], str],
) -> str:
    if expires_at is None:
        return shell(lang, "hold_no_deadline")
    now = datetime.now(UTC)
    end = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
    if end <= now:
        return shell(lang, "hold_expired")
    total_minutes = max(0, int((end - now).total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    return shell(
        lang,
        "hold_time_left",
        hours=str(hours),
        minutes=str(minutes),
        deadline=format_dt(expires_at),
    )


def payment_status_label(lang: str | None, status: object) -> str:
    """Map payment status enum/value to localized short label."""
    v = getattr(status, "value", status)
    if not isinstance(v, str):
        v = str(v)
    mapping = {
        "awaiting_payment": "payment_status_awaiting",
        "unpaid": "payment_status_unpaid",
        "paid": "payment_status_paid",
    }
    sk = mapping.get(v)
    if sk:
        return shell(lang, sk)
    return v.replace("_", " ").title()
