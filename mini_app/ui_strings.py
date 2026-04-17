"""
UI-shell copy for the Flet Mini App (navigation, buttons, common labels).

Tour titles/descriptions still come from the API and may use fallback translation there.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

# Keys per language; partial tables merge with English (see shell()).
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
        "catalog_card_assisted_notice": "Whole-bus / charter offer — open details. Seat-by-seat self-booking is not available here.",
        "detail_assisted_booking_title": "Assistance required",
        "detail_assisted_booking_body": "This tour is sold as a whole-bus / charter style offer. Tap the button below to send a structured assistance request to the team, or use Help in the header. "
        "The standard seat reservation flow is not available in this app for this departure.",
        "btn_request_full_bus_assistance": "Request full-bus assistance",
        "preparation_assisted_title": "Self-service reservation not available",
        "preparation_assisted_body": "This tour uses a whole-bus / charter style offer. Use Help to reach the team. "
        "You cannot complete a seat hold from this screen.",
        "waitlist_intro_sold_out": "This tour is sold out. You can join the waitlist to record interest — "
        "this is not a confirmed booking or a guaranteed seat.",
        "waitlist_join_cta": "Join waitlist",
        "waitlist_status_on": "You are on the waitlist for this tour. This is not a confirmed booking.",
        "waitlist_active_title": "You are on the waitlist",
        "waitlist_active_body": "Your interest is recorded for this tour. This is not a confirmed booking or a guaranteed seat.",
        "waitlist_in_review_title": "Your waitlist request is being reviewed",
        "waitlist_in_review_body": "We are processing your request. This is still not a confirmed booking or a guaranteed seat.",
        "waitlist_closed_body": "Your previous waitlist request for this tour is closed. You can join the waitlist again if you still want to show interest — still not a confirmed booking.",
        "waitlist_tour_not_eligible": "This tour is not open for booking or waitlist from here right now.",
        "waitlist_snackbar_created": "Your waitlist request was recorded. This is not a confirmed booking.",
        "waitlist_snackbar_already": "You are already on the waitlist for this tour.",
        "waitlist_snackbar_not_eligible": "Waitlist is not available for this tour right now.",
        "waitlist_snackbar_error": "Could not record your waitlist request. Please try again later.",
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
        "payment_intro_active_hold": "This hold is still active. Complete payment before the deadline below — after that, seats may be released back to the tour.",
        "payment_screen_unavailable_hold": "Payment cannot be started for this reservation. The hold may have expired or been released. Open My bookings for the current status, or start again from the catalog.",
        "payment_screen_load_error_generic": "We could not load the payment step. Go back to My bookings or try again.",
        "payment_mock_disabled_user_message": "Test payment completion is turned off on this server. Your booking stays unpaid until an operator or webhook confirms it. For staging tests, ask your team to enable mock payment on the API, or use the normal payment channel when available.",
        "payment_confirm_error_generic": "Payment could not be confirmed. Try again while the hold is still active, or check My bookings.",
        "booking_detail_note_active_hold": "You can still pay while the deadline above applies. After payment is confirmed, this booking moves to Confirmed bookings.",
        "booking_detail_note_confirmed": "This trip is paid and confirmed. Use My bookings if you need to review details.",
        "booking_detail_note_released": "This hold is no longer active (expired or released without payment). To travel on this tour, start a new reservation from the catalog if seats are available.",
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
        "my_bookings_subtitle": "Confirmed trips appear first, then holds you can pay, then past holds that were released or expired.",
        "bookings_section_confirmed_title": "Confirmed bookings",
        "bookings_section_confirmed_hint": "Paid and confirmed for departure.",
        "bookings_section_active_title": "Active holds",
        "bookings_section_active_hint": "Temporary reservations — pay before the deadline to keep your seats.",
        "bookings_section_history_title": "History",
        "bookings_section_history_hint": "Released or expired holds without completed payment.",
        "bookings_history_truncated_note": "{n} older past holds are hidden here to keep this list manageable. "
        "They are not deleted — open a booking by reference from your records if needed.",
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
        "support_banner_title": "Need help?",
        "support_banner_body": "Need help with a booking or payment? Log a support request and, if needed, describe the issue in the bot chat.",
        "support_cta_log_request": "Log support request",
        "booking_support_body": "Need help with this booking? Log a support request and, if needed, describe your case in the bot chat.",
        "payment_support_body": "Payment or checkout problem? Log a support request — the team may review it later. This is not a live chat.",
        "support_request_success": "Support request recorded. Reference: {ref}",
        "support_request_error": "Could not record the support request right now. Please try again later.",
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
        "catalog_card_assisted_notice": "Oferta autocar complet — vezi detalii. Rezervare loc cu loc nu e disponibila aici.",
        "detail_assisted_booking_title": "Este nevoie de asistenta",
        "detail_assisted_booking_body": "Acest tur este oferit ca inchiriere autocar / grup complet. Apasa butonul de mai jos pentru o cerere structurata catre echipa sau foloseste Ajutor din antet. "
        "Fluxul standard de rezervare loc cu loc nu e disponibil in aplicatie pentru aceasta plecare.",
        "btn_request_full_bus_assistance": "Solicita asistenta autocar complet",
        "preparation_assisted_title": "Rezervare self-service indisponibila",
        "preparation_assisted_body": "Acest tur foloseste o oferta tip autocar complet. Foloseste Ajutor pentru echipa. "
        "Nu poti finaliza un hold de locuri din acest ecran.",
        "waitlist_intro_sold_out": "Acest tur este epuizat. Poti intra pe lista de asteptare pentru a inregistra interesul — "
        "aceasta nu este o rezervare confirmata sau un loc garantat.",
        "waitlist_join_cta": "Intră pe lista de așteptare",
        "waitlist_status_on": "Ești pe lista de așteptare pentru acest tur. Aceasta nu este o rezervare confirmată.",
        "waitlist_active_title": "Ești pe lista de așteptare",
        "waitlist_active_body": "Interesul tău este înregistrat pentru acest tur. Aceasta nu este o rezervare confirmată sau un loc garantat.",
        "waitlist_in_review_title": "Cererea ta pe lista de așteptare este în revizie",
        "waitlist_in_review_body": "Procesăm cererea ta. În continuare nu este o rezervare confirmată sau un loc garantat.",
        "waitlist_closed_body": "Cererea ta anterioară pe lista de așteptare pentru acest tur este închisă. Poți intra din nou pe listă dacă vrei să înregistrezi interes — tot nu este o rezervare confirmată.",
        "waitlist_tour_not_eligible": "Acest tur nu este deschis pentru rezervare sau lista de așteptare aici, acum.",
        "waitlist_snackbar_created": "Cererea pentru lista de așteptare a fost înregistrată. Aceasta nu este o rezervare confirmată.",
        "waitlist_snackbar_already": "Ești deja pe lista de așteptare pentru acest tur.",
        "waitlist_snackbar_not_eligible": "Lista de așteptare nu este disponibilă pentru acest tur acum.",
        "waitlist_snackbar_error": "Nu am putut înregistra cererea pentru lista de așteptare. Încearcă din nou mai târziu.",
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
        "payment_intro_active_hold": "Acest hold este inca activ. Finalizeaza plata inainte de termenul de mai jos — dupa aceea, locurile pot fi eliberate inapoi la tur.",
        "payment_screen_unavailable_hold": "Nu se poate porni plata pentru aceasta rezervare. Hold-ul poate fi expirat sau eliberat. Deschide Rezervarile mele pentru status, sau reincepe din catalog.",
        "payment_screen_load_error_generic": "Nu am putut incarca pasul de plata. Revino la Rezervarile mele sau incearca din nou.",
        "payment_mock_disabled_user_message": "Finalizarea de test a platii este oprita pe acest server. Rezervarea ramane neplatita pana confirma un operator sau webhook-ul. Pentru staging, echipa poate activa mock payment pe API, sau folositi canalul normal de plata cand e disponibil.",
        "payment_confirm_error_generic": "Plata nu a putut fi confirmata. Incearca din nou cat timp hold-ul e activ, sau verifica Rezervarile mele.",
        "booking_detail_note_active_hold": "Poti plati cat timp se aplica termenul de mai sus. Dupa confirmarea platii, rezervarea apare la Rezervari confirmate.",
        "booking_detail_note_confirmed": "Calatoria este platita si confirmata. Foloseste Rezervarile mele pentru detalii.",
        "booking_detail_note_released": "Acest hold nu mai este activ (expirat sau eliberat fara plata). Pentru acest tur, fa o rezervare noua din catalog daca sunt locuri.",
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
        "my_bookings_subtitle": "Mai intai calatoriile confirmate, apoi hold-urile de plata, apoi istoricul (eliberate sau expirate).",
        "bookings_section_confirmed_title": "Rezervari confirmate",
        "bookings_section_confirmed_hint": "Platite si confirmate pentru plecare.",
        "bookings_section_active_title": "Hold-uri active",
        "bookings_section_active_hint": "Rezervari temporare — plateste inainte de termen pentru locuri.",
        "bookings_section_history_title": "Istoric",
        "bookings_section_history_hint": "Hold-uri eliberate sau expirate fara plata finalizata.",
        "bookings_history_truncated_note": "{n} rezervari vechi din istoric sunt ascunse aici pentru o lista mai clara. "
        "Nu sunt sterse — poti deschide o rezervare dupa referinta daca ai nevoie.",
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
        "support_banner_title": "Ai nevoie de ajutor?",
        "support_banner_body": "Ai nevoie de ajutor cu o rezervare sau o plată? Trimite o cerere de suport și, dacă este nevoie, descrie problema și în chatul botului.",
        "support_cta_log_request": "Trimite cerere de suport",
        "booking_support_body": "Ai nevoie de ajutor cu această rezervare? Trimite o cerere de suport și, dacă este nevoie, descrie cazul și în chatul botului.",
        "payment_support_body": "Problemă la plată sau la checkout? Trimite o cerere de suport — echipa o poate analiza ulterior. Acesta nu este un chat live.",
        "support_request_success": "Cererea de suport a fost înregistrată. Referință: {ref}",
        "support_request_error": "Cererea de suport nu a putut fi înregistrată acum. Încearcă din nou mai târziu.",
    },
    "ru": {
        "support_banner_title": "Нужна помощь?",
        "support_banner_body": "Нужна помощь с бронированием или оплатой? Отправьте запрос в поддержку и, при необходимости, опишите проблему в чате бота.",
        "support_cta_log_request": "Отправить запрос в поддержку",
        "booking_support_body": "Нужна помощь по этому бронированию? Отправьте запрос в поддержку и, при необходимости, опишите ситуацию в чате бота.",
        "payment_support_body": "Проблема с оплатой или checkout? Отправьте запрос в поддержку — команда сможет проверить его позже. Это не онлайн-чат.",
        "support_request_success": "Запрос в поддержку зарегистрирован. Номер: {ref}",
        "support_request_error": "Сейчас не удалось зарегистрировать запрос в поддержку. Попробуйте позже.",
    },
    "sr": {
        "support_banner_title": "Treba vam pomoć?",
        "support_banner_body": "Treba vam pomoć oko rezervacije ili plaćanja? Pošaljite zahtev za podršku i, ako je potrebno, opišite problem i u četu bota.",
        "support_cta_log_request": "Pošalji zahtev za podršku",
        "booking_support_body": "Treba vam pomoć oko ove rezervacije? Pošaljite zahtev za podršku i, ako je potrebno, opišite slučaj i u četu bota.",
        "payment_support_body": "Imate problem sa plaćanjem ili checkout-om? Pošaljite zahtev za podršku — tim ga može pregledati kasnije. Ovo nije live chat.",
        "support_request_success": "Zahtev za podršku je evidentiran. Referenca: {ref}",
        "support_request_error": "Zahtev za podršku trenutno nije moguće evidentirati. Pokušajte ponovo kasnije.",
    },
    "hu": {
        "support_banner_title": "Segítségre van szüksége?",
        "support_banner_body": "Segítségre van szüksége foglalással vagy fizetéssel kapcsolatban? Küldjön támogatási kérelmet, és ha szükséges, írja le a problémát a bot chatben is.",
        "support_cta_log_request": "Támogatási kérelem küldése",
        "booking_support_body": "Segítségre van szüksége ezzel a foglalással kapcsolatban? Küldjön támogatási kérelmet, és ha szükséges, írja le az esetet a bot chatben is.",
        "payment_support_body": "Fizetési vagy checkout probléma van? Küldjön támogatási kérelmet — a csapat később átnézheti. Ez nem élő chat.",
        "support_request_success": "A támogatási kérelem rögzítve. Azonosító: {ref}",
        "support_request_error": "A támogatási kérelmet most nem sikerült rögzíteni. Kérjük, próbálja újra később.",
    },
    "it": {
        "support_banner_title": "Hai bisogno di aiuto?",
        "support_banner_body": "Hai bisogno di aiuto con una prenotazione o un pagamento? Invia una richiesta di supporto e, se necessario, descrivi il problema anche nella chat del bot.",
        "support_cta_log_request": "Invia richiesta di supporto",
        "booking_support_body": "Hai bisogno di aiuto per questa prenotazione? Invia una richiesta di supporto e, se necessario, descrivi il caso anche nella chat del bot.",
        "payment_support_body": "Hai un problema con il pagamento o il checkout? Invia una richiesta di supporto — il team potrà esaminarla in seguito. Questa non è una chat live.",
        "support_request_success": "Richiesta di supporto registrata. Riferimento: {ref}",
        "support_request_error": "Non è stato possibile registrare la richiesta di supporto in questo momento. Riprova più tardi.",
    },
    "de": {
        "support_banner_title": "Brauchen Sie Hilfe?",
        "support_banner_body": "Brauchen Sie Hilfe bei einer Buchung oder Zahlung? Senden Sie eine Support-Anfrage und beschreiben Sie das Problem bei Bedarf auch im Bot-Chat.",
        "support_cta_log_request": "Support-Anfrage senden",
        "booking_support_body": "Brauchen Sie Hilfe bei dieser Buchung? Senden Sie eine Support-Anfrage und beschreiben Sie Ihren Fall bei Bedarf auch im Bot-Chat.",
        "payment_support_body": "Gibt es ein Problem mit der Zahlung oder dem Checkout? Senden Sie eine Support-Anfrage — das Team kann sie später prüfen. Dies ist kein Live-Chat.",
        "support_request_success": "Support-Anfrage wurde erfasst. Referenz: {ref}",
        "support_request_error": "Die Support-Anfrage konnte im Moment nicht erfasst werden. Bitte versuchen Sie es später erneut.",
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
