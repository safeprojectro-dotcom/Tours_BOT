from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal

from app.bot.constants import LANGUAGE_LABELS
from app.models.enums import TourStatus
from app.schemas.prepared import (
    CatalogTourCardRead,
    PaymentEntryRead,
    PreparedTourDetailRead,
    ReservationPreparationSummaryRead,
)

TemplateMap = dict[str, str]

TRANSLATIONS: dict[str, TemplateMap] = {
    "en": {
        "language_prompt": "I can continue in your preferred language. Please choose one:",
        "language_saved": "Language updated to {language_name}.",
        "welcome": "Welcome. The Mini App is the main place to browse tours, manage bookings, and complete payment.",
        "browse_cta": "In this chat you can use quick filters or the short tour list. For the full experience, open the Mini App.",
        "open_mini_app_bookings": "My bookings (Mini App)",
        "help_command_reply": "This chat is your guide.\n\n"
        "• Open Mini App — full catalog, booking, and payment\n"
        "• My bookings (Mini App) — reservation and payment status\n"
        "• Quick filters below — optional shortcuts in chat\n\n"
        "Commands: /tours (tour list here), /language, /bookings, /contact, /human. "
        "/contact or /human can log a support signal for the team (not a live operator chat). "
        "Tap Help inside the Mini App for detailed topics and “Log support request” on payment or booking screens.",
        "bookings_command_reply": "Reservation and payment status live in the Mini App.\n\n"
        "Use the buttons below to open the Mini App or go straight to My bookings.",
        "contact_command_reply": "Need help with a booking or payment? I can record a support request for the team and return a reference number.",
        "human_command_reply": "If you need human review, I can record a support request for the team and return a reference number.",
        "handoff_request_recorded": "Support request recorded. Reference: {ref}",
        "handoff_request_failed": "Could not record the support request right now. Please try again later.",
        "catalog_empty": "There are no open tours to show right now. Please try again later.",
        "catalog_intro": "Here are up to 3 open tours you can review now:",
        "tour_missing": "I could not find that tour in the current catalog.",
        "waitlist_private_hint": "This tour is currently sold out. You can record interest on the waitlist in the Mini App — that is not a confirmed booking.",
        "tour_cta": "Choose another tour or open the catalog for more options.",
        "open_catalog": "Browse tours",
        "change_language": "Change language",
        "open_mini_app": "Open Mini App",
        "back_to_catalog": "Back to tours",
        "details_title": "Tour details",
        "boarding_points": "Boarding points",
        "language_note": "Using fallback content because this tour is not translated in your selected language yet.",
        "browse_by_date": "Browse by date",
        "browse_by_destination": "Browse by destination",
        "browse_by_budget": "Browse by budget",
        "date_prompt": "What date preference should I use?",
        "date_weekend": "This weekend",
        "date_next_30_days": "Next 30 days",
        "date_any": "Any date",
        "destination_prompt": "Send a destination or tour name keyword, and I will show matching tours.",
        "destination_empty": "Please send a destination or tour name so I can search safely.",
        "destination_cancel": "Cancel",
        "budget_prompt": "Choose a budget range for browsing.",
        "budget_any": "Any budget",
        "budget_not_available": "Budget browsing is not available right now because the open catalog contains multiple currencies.",
        "filter_results_intro": "Here are up to 3 tours matching: {filter_summary}",
        "filter_results_empty": "I could not find open tours matching: {filter_summary}",
        "filter_results_cta": "You can try another filter or open the full tour list.",
        "filter_date_weekend_summary": "this weekend",
        "filter_date_next_30_days_summary": "next 30 days",
        "filter_date_any_summary": "any date",
        "filter_destination_summary": 'destination "{query}"',
        "filter_budget_summary": "budget up to {amount} {currency}",
        "filter_budget_any_summary": "any budget",
        "prepare_reservation": "Prepare reservation",
        "request_booking_assistance": "Request booking assistance",
        "assisted_booking_detail_note": "Automated per-seat reservation in this chat is not available for this tour. Use the button below or /contact so the team can help.",
        "catalog_card_assisted_hint": "(Booking via team assistance)",
        "private_self_service_reservation_blocked": "This tour cannot be reserved with the automated seat flow in chat. Use /contact or the assistance button on the tour details.",
        "seat_count_prompt": "How many seats should I prepare?",
        "boarding_point_prompt": "Which boarding point should I use for this preparation?",
        "preparation_unavailable": "This tour is not available for reservation preparation right now.",
        "preparation_summary_title": "Reservation preparation summary",
        "seat_count_label": "Seats",
        "estimated_total_label": "Estimated total",
        "preparation_only_note": "This is only a preparation preview. No reservation has been created yet.",
        "change_seat_count": "Change seats",
        "change_boarding_point": "Change boarding point",
        "create_temporary_reservation": "Create temporary reservation",
        "temporary_reservation_title": "Temporary reservation created",
        "reservation_expires_label": "Reservation expires",
        "reservation_reference_label": "Reservation reference",
        "temporary_reservation_note": "This reservation is temporary and payment is not started in this step.",
        "reservation_creation_failed": "I could not create the temporary reservation because availability changed or the tour is no longer open for sale.",
        "continue_to_payment": "Continue to payment",
        "payment_entry_title": "Payment step ready",
        "payment_session_label": "Payment session",
        "payment_amount_label": "Amount due",
        "payment_entry_note": "Your reservation is still temporary. Complete payment before the reservation expires.",
        "payment_verification_note": "Payment is not confirmed until the system verifies it.",
        "payment_entry_failed": "I could not start the payment step because this reservation is no longer valid for payment.",
        "start_grp_private_intro": "Thanks for opening this chat from the group. You can browse tours below or open the Mini App when you are ready.",
        "start_sup_offer_intro": "You opened this chat from a featured offer: {title}. Core tour catalog and booking stay in the Mini App and the shortcuts below.",
        "sup_offer_not_available": "That featured offer is not available anymore. Here is the current catalog.",
        "start_grp_followup_intro": "Thanks for continuing from the group. Use /contact or /human if the team should see extra details. Browse tours below.",
        "start_grp_followup_resolved_intro": "Your previous group follow-up is closed. Browse tours below. Use /contact or /human for a new request.",
        "start_grp_followup_readiness_pending": "This group follow-up is queued with the team. Use /contact or /human if something changed. Browse tours below.",
        "start_grp_followup_readiness_assigned": "This follow-up has a team member assigned. Use /contact or /human if you need to add more. Browse tours below.",
        "start_grp_followup_readiness_in_progress": "The team is working on this follow-up. Use /contact or /human if you need to add more. Browse tours below.",
    },
    "ro": {
        "language_prompt": "Pot continua in limba preferata. Alege o limba:",
        "language_saved": "Limba a fost schimbata in {language_name}.",
        "welcome": "Bun venit. Mini App este locul principal pentru catalog, rezervari si plata.",
        "browse_cta": "In acest chat poti folosi filtre rapide sau lista scurta de mai jos. Pentru experienta completa, deschide Mini App.",
        "open_mini_app_bookings": "Rezervarile mele (Mini App)",
        "help_command_reply": "Acest chat este ghidul tau.\n\n"
        "• Deschide Mini App — catalog complet, rezervare si plata\n"
        "• Rezervarile mele (Mini App) — status rezervare si plata\n"
        "• Filtre rapide mai jos — scurtaturi optionale in chat\n\n"
        "Comenzi: /tours (lista aici), /language, /bookings, /contact, /human. "
        "/contact sau /human pot inregistra un semnal de suport pentru echipa (nu chat live cu operator). "
        "Apasa Help in Mini App pentru detalii si „Inregistreaza cerere suport” la plata sau pe rezervare.",
        "bookings_command_reply": "Statusul rezervarii si al platii este in Mini App.\n\n"
        "Foloseste butoanele de mai jos pentru Mini App sau direct Rezervarile mele.",
        "contact_command_reply": "Ai nevoie de ajutor cu o rezervare sau o plată? Pot înregistra o cerere de suport pentru echipă și îți pot da un număr de referință.",
        "human_command_reply": "Dacă ai nevoie de analiză umană, pot înregistra o cerere de suport pentru echipă și îți pot da un număr de referință.",
        "handoff_request_recorded": "Cererea de suport a fost înregistrată. Referință: {ref}",
        "handoff_request_failed": "Cererea de suport nu a putut fi înregistrată acum. Încearcă din nou mai târziu.",
        "catalog_empty": "Momentan nu exista tururi deschise pentru vanzare. Te rog incearca mai tarziu.",
        "catalog_intro": "Iata pana la 3 tururi deschise pe care le poti vedea acum:",
        "tour_missing": "Nu am gasit acel tur in catalogul curent.",
        "waitlist_private_hint": "Acest tur este epuizat momentan. Poti inregistra interes pe lista de asteptare in Mini App — aceasta nu este o rezervare confirmata.",
        "tour_cta": "Alege alt tur sau deschide catalogul pentru mai multe optiuni.",
        "open_catalog": "Vezi tururi",
        "change_language": "Schimba limba",
        "open_mini_app": "Deschide Mini App",
        "back_to_catalog": "Inapoi la tururi",
        "details_title": "Detalii tur",
        "boarding_points": "Puncte de imbarcare",
        "language_note": "Folosesc continut fallback deoarece acest tur nu este tradus inca in limba aleasa.",
        "browse_by_date": "Cauta dupa data",
        "browse_by_destination": "Cauta dupa destinatie",
        "browse_by_budget": "Cauta dupa buget",
        "date_prompt": "Ce preferinta de data vrei sa folosesc?",
        "date_weekend": "Weekendul acesta",
        "date_next_30_days": "Urmatoarele 30 de zile",
        "date_any": "Orice data",
        "destination_prompt": "Trimite o destinatie sau un nume de tur si iti arat variantele potrivite.",
        "destination_empty": "Te rog trimite o destinatie sau un nume de tur ca sa caut sigur.",
        "destination_cancel": "Anuleaza",
        "budget_prompt": "Alege un interval de buget pentru cautare.",
        "budget_any": "Orice buget",
        "budget_not_available": "Filtrarea dupa buget nu este disponibila acum deoarece catalogul deschis contine mai multe monede.",
        "filter_results_intro": "Iata pana la 3 tururi care se potrivesc cu: {filter_summary}",
        "filter_results_empty": "Nu am gasit tururi deschise pentru: {filter_summary}",
        "filter_results_cta": "Poti incerca alt filtru sau poti deschide lista completa de tururi.",
        "filter_date_weekend_summary": "weekendul acesta",
        "filter_date_next_30_days_summary": "urmatoarele 30 de zile",
        "filter_date_any_summary": "orice data",
        "filter_destination_summary": 'destinatia "{query}"',
        "filter_budget_summary": "buget pana la {amount} {currency}",
        "filter_budget_any_summary": "orice buget",
        "prepare_reservation": "Pregateste rezervarea",
        "request_booking_assistance": "Asistenta pentru rezervare",
        "assisted_booking_detail_note": "Rezervarea automata pe locuri in acest chat nu este disponibila pentru acest tur. Foloseste butonul de mai jos sau /contact pentru ajutor din partea echipei.",
        "catalog_card_assisted_hint": "(Rezervare cu asistenta echipei)",
        "private_self_service_reservation_blocked": "Acest tur nu poate fi rezervat cu fluxul automat pe locuri in chat. Foloseste /contact sau butonul de asistenta din detaliile turului.",
        "seat_count_prompt": "Pentru cate locuri sa pregatesc rezervarea?",
        "boarding_point_prompt": "Ce punct de imbarcare sa folosesc pentru aceasta pregatire?",
        "preparation_unavailable": "Acest tur nu este disponibil acum pentru pregatirea rezervarii.",
        "preparation_summary_title": "Sumar pregatire rezervare",
        "seat_count_label": "Locuri",
        "estimated_total_label": "Total estimat",
        "preparation_only_note": "Acesta este doar un rezumat de pregatire. Nu a fost creata nicio rezervare inca.",
        "change_seat_count": "Schimba locurile",
        "change_boarding_point": "Schimba imbarcarea",
        "create_temporary_reservation": "Creeaza rezervare temporara",
        "temporary_reservation_title": "Rezervare temporara creata",
        "reservation_expires_label": "Rezervarea expira",
        "reservation_reference_label": "Referinta rezervare",
        "temporary_reservation_note": "Aceasta rezervare este temporara, iar plata nu este pornita in acest pas.",
        "reservation_creation_failed": "Nu am putut crea rezervarea temporara deoarece disponibilitatea s-a schimbat sau turul nu mai este deschis pentru vanzare.",
        "continue_to_payment": "Continua catre plata",
        "payment_entry_title": "Pasul de plata este pregatit",
        "payment_session_label": "Sesiune plata",
        "payment_amount_label": "Suma de plata",
        "payment_entry_note": "Rezervarea ta este inca temporara. Finalizeaza plata inainte sa expire rezervarea.",
        "payment_verification_note": "Plata nu este confirmata pana cand sistemul nu o verifica.",
        "payment_entry_failed": "Nu am putut porni pasul de plata deoarece aceasta rezervare nu mai este valida pentru plata.",
        "start_grp_private_intro": "Multumim ca ai deschis chatul din grup. Poti vedea tururi mai jos sau deschide Mini App cand esti gata.",
        "start_sup_offer_intro": "Ai deschis chatul din oferta promovata: {title}. Catalogul principal si rezervarile raman in Mini App si scurtaturile de mai jos.",
        "sup_offer_not_available": "Oferta promovata nu mai este disponibila. Iata catalogul curent.",
        "start_grp_followup_intro": "Multumim ca continui din grup. Foloseste /contact sau /human daca echipa trebuie sa vada detalii extra. Vezi tururi mai jos.",
        "start_grp_followup_resolved_intro": "Urmarirea anterioara din grup este inchisa. Vezi tururi mai jos. Cerere noua: /contact sau /human.",
        "start_grp_followup_readiness_pending": "Aceasta urmarire din grup este la coada la echipa. Foloseste /contact sau /human daca s-a schimbat ceva. Vezi tururi mai jos.",
        "start_grp_followup_readiness_assigned": "Acestei urmariri i s-a alocat un membru al echipei. Foloseste /contact sau /human pentru detalii suplimentare. Vezi tururi mai jos.",
        "start_grp_followup_readiness_in_progress": "Echipa lucreaza la aceasta urmarire. Foloseste /contact sau /human pentru detalii suplimentare. Vezi tururi mai jos.",
    },
    "ru": {
        "language_prompt": "Ya mogu prodolzhit na udobnom dlya vas yazyke. Vyberite yazyk:",
        "language_saved": "Yazyk obnovlen: {language_name}.",
        "welcome": "Dobro pozhalovat. Mini App — osnovnoy interfeys dlya kataloga, upravleniya bronyami i oplaty.",
        "browse_cta": "V etom chate dostupny bystrye filtry i korotkiy spisok. Polnyy funktsional — v Mini App.",
        "catalog_empty": "Seychas net otkrytykh turov dlya pokaza. Poprobuyte pozhe.",
        "catalog_intro": "Vot do 3 otkrytykh turov, kotorye mozhno posmotret seychas:",
        "tour_missing": "Ya ne nashel etot tur v tekushchem kataloge.",
        "tour_cta": "Vyberite drugoy tur ili otkroyte katalog dlya dopolnitelnykh variantov.",
        "open_catalog": "Smotret tury",
        "change_language": "Smenit yazyk",
        "open_mini_app": "Otkryt Mini App",
        "back_to_catalog": "Nazad k turam",
        "details_title": "Detal i tura",
        "boarding_points": "Mesta posadki",
        "language_note": "Ispolzuetsya rezervnyy tekst, potomu chto perevoda dlya vybrannogo yazyka poka net.",
        "browse_by_date": "Poisk po date",
        "browse_by_destination": "Poisk po napravleniyu",
        "browse_by_budget": "Poisk po byudzhetu",
        "date_prompt": "Kakoe predpochtenie po date ispolzovat?",
        "date_weekend": "Eti vykhodnye",
        "date_next_30_days": "Sleduyushchie 30 dney",
        "date_any": "Lyubaya data",
        "destination_prompt": "Otpravte napravlenie ili nazvanie tura, i ya pokazhu podkhodyashchie varianty.",
        "destination_empty": "Pozhaluysta, otpravte napravlenie ili nazvanie tura, chtoby ya bezopasno vypolnil poisk.",
        "destination_cancel": "Otmena",
        "budget_prompt": "Vyberite byudzhetnyy diapazon dlya poiska.",
        "budget_any": "Lyuboy byudzhet",
        "budget_not_available": "Poisk po byudzhetu seychas nedostupen, potomu chto v otkrytom kataloge neskolko valyut.",
        "filter_results_intro": "Vot do 3 turov po filtru: {filter_summary}",
        "filter_results_empty": "Ya ne nashel otkrytye tury po filtru: {filter_summary}",
        "filter_results_cta": "Mozhno poprobovat drugoy filtr ili otkryt polnyy spisok turov.",
        "filter_date_weekend_summary": "eti vykhodnye",
        "filter_date_next_30_days_summary": "sleduyushchie 30 dney",
        "filter_date_any_summary": "lyubaya data",
        "filter_destination_summary": 'napravlenie "{query}"',
        "filter_budget_summary": "byudzhet do {amount} {currency}",
        "filter_budget_any_summary": "lyuboy byudzhet",
        "prepare_reservation": "Podgotovit bronirovanie",
        "seat_count_prompt": "Skolko mest nuzhno podgotovit?",
        "boarding_point_prompt": "Kakuyu tochku posadki ispolzovat dlya etoy podgotovki?",
        "preparation_unavailable": "Etot tur seychas nedostupen dlya podgotovki bronirovaniya.",
        "preparation_summary_title": "Svodka podgotovki bronirovaniya",
        "seat_count_label": "Mesta",
        "estimated_total_label": "Predvaritelnaya summa",
        "preparation_only_note": "Eto tolko predvaritelnyy prosmotr. Bronirovanie eshche ne sozdano.",
        "change_seat_count": "Izmenit kolichestvo mest",
        "change_boarding_point": "Izmenit tochku posadki",
        "create_temporary_reservation": "Sozdat vremennoe bronirovanie",
        "temporary_reservation_title": "Vremennoe bronirovanie sozdano",
        "reservation_expires_label": "Bronirovanie istekaet",
        "reservation_reference_label": "Nomer bronirovaniya",
        "temporary_reservation_note": "Eto bronirovanie vremennoye, i oplata na etom shage ne zapushchena.",
        "reservation_creation_failed": "Ne udalos sozdat vremennoe bronirovanie, potomu chto dostupnost izmenilas ili tur bolshe ne otkryt dlya prodazhi.",
        "continue_to_payment": "Pereyti k oplate",
        "payment_entry_title": "Shag oplaty podgotovlen",
        "payment_session_label": "Sessiya oplaty",
        "payment_amount_label": "Summa k oplate",
        "payment_entry_note": "Vasha rezervatsiya vse eshche vremennaya. Zavershite oplatu do istecheniya broni.",
        "payment_verification_note": "Oplata ne schitaetsya podtverzhdennoy, poka sistema ee ne proverit.",
        "payment_entry_failed": "Ne udalos zapustit shag oplaty, potomu chto eta rezervatsiya bolshe ne validna dlya oplaty.",
        "contact_command_reply": "Нужна помощь с бронированием или оплатой? Я могу зарегистрировать запрос в поддержку для команды и вернуть вам номер обращения.",
        "human_command_reply": "Если вам нужна проверка человеком, я могу зарегистрировать запрос в поддержку для команды и вернуть номер обращения.",
        "handoff_request_recorded": "Запрос в поддержку зарегистрирован. Номер: {ref}",
        "handoff_request_failed": "Сейчас не удалось зарегистрировать запрос в поддержку. Попробуйте позже.",
        "start_grp_private_intro": "Спасибо, что открыли чат из группы. Туры ниже или Mini App, когда будете готовы.",
        "start_sup_offer_intro": "Вы открыли чат из предложения: {title}. Каталог и бронирование — в Mini App и кнопках ниже.",
        "sup_offer_not_available": "Это предложение больше недоступно. Ниже актуальный каталог.",
        "start_grp_followup_intro": "Спасибо, что перешли из группы. /contact или /human — если команде нужны доп. детали. Туры ниже.",
        "start_grp_followup_resolved_intro": "Предыдущий запрос из группы закрыт. Туры ниже. Новый запрос — /contact или /human.",
        "start_grp_followup_readiness_pending": "Этот запрос из группы в очереди у команды. /contact или /human — если что-то изменилось. Туры ниже.",
        "start_grp_followup_readiness_assigned": "На этот запрос назначен член команды. /contact или /human — если нужно добавить. Туры ниже.",
        "start_grp_followup_readiness_in_progress": "Команда обрабатывает этот запрос. /contact или /human — если нужно добавить. Туры ниже.",
    },
    "sr": {
        "language_prompt": "Mogu da nastavim na vasem jeziku. Izaberite jezik:",
        "language_saved": "Jezik je promenjen na {language_name}.",
        "welcome": "Dobro dosli. Mini App je glavno mesto za katalog, rezervacije i placanje.",
        "browse_cta": "U chatu mozete koristiti brze filtere ili kratak spisak. Kompletno iskustvo je u Mini App.",
        "catalog_empty": "Trenutno nema otvorenih tura za prikaz. Pokusajte kasnije.",
        "catalog_intro": "Evo do 3 otvorene ture koje sada mozete pogledati:",
        "tour_missing": "Nisam pronasao tu turu u trenutnom katalogu.",
        "tour_cta": "Izaberite drugu turu ili otvorite katalog za jos opcija.",
        "open_catalog": "Pregled tura",
        "change_language": "Promeni jezik",
        "open_mini_app": "Otvori Mini App",
        "back_to_catalog": "Nazad na ture",
        "details_title": "Detalji ture",
        "boarding_points": "Mesta ukrcavanja",
        "language_note": "Koristim rezervni sadrzaj jer ova tura jos nema prevod na izabrani jezik.",
        "browse_by_date": "Pretraga po datumu",
        "browse_by_destination": "Pretraga po destinaciji",
        "browse_by_budget": "Pretraga po budzetu",
        "date_prompt": "Koju preferenciju datuma da koristim?",
        "date_weekend": "Ovog vikenda",
        "date_next_30_days": "U narednih 30 dana",
        "date_any": "Bilo koji datum",
        "destination_prompt": "Posaljite destinaciju ili naziv ture i pokazacu odgovarajuce opcije.",
        "destination_empty": "Posaljite destinaciju ili naziv ture kako bih bezbedno pretrazio katalog.",
        "destination_cancel": "Otkazi",
        "budget_prompt": "Izaberite opseg budzeta za pregled.",
        "budget_any": "Bilo koji budzet",
        "budget_not_available": "Pretraga po budzetu trenutno nije dostupna jer otvoreni katalog sadrzi vise valuta.",
        "filter_results_intro": "Evo do 3 ture koje odgovaraju filteru: {filter_summary}",
        "filter_results_empty": "Nisam pronasao otvorene ture za filter: {filter_summary}",
        "filter_results_cta": "Mozete probati drugi filter ili otvoriti punu listu tura.",
        "filter_date_weekend_summary": "ovog vikenda",
        "filter_date_next_30_days_summary": "u narednih 30 dana",
        "filter_date_any_summary": "bilo koji datum",
        "filter_destination_summary": 'destinacija "{query}"',
        "filter_budget_summary": "budzet do {amount} {currency}",
        "filter_budget_any_summary": "bilo koji budzet",
        "prepare_reservation": "Pripremi rezervaciju",
        "seat_count_prompt": "Koliko mesta da pripremim?",
        "boarding_point_prompt": "Koje mesto ukrcavanja da koristim za ovu pripremu?",
        "preparation_unavailable": "Ova tura trenutno nije dostupna za pripremu rezervacije.",
        "preparation_summary_title": "Pregled pripreme rezervacije",
        "seat_count_label": "Mesta",
        "estimated_total_label": "Procenjeni ukupno",
        "preparation_only_note": "Ovo je samo pregled pripreme. Rezervacija jos nije kreirana.",
        "change_seat_count": "Promeni broj mesta",
        "change_boarding_point": "Promeni ukrcavanje",
        "create_temporary_reservation": "Kreiraj privremenu rezervaciju",
        "temporary_reservation_title": "Privremena rezervacija je kreirana",
        "reservation_expires_label": "Rezervacija istice",
        "reservation_reference_label": "Referenca rezervacije",
        "temporary_reservation_note": "Ova rezervacija je privremena i placanje nije pokrenuto u ovom koraku.",
        "reservation_creation_failed": "Nisam mogao da kreiram privremenu rezervaciju jer se dostupnost promenila ili tura vise nije otvorena za prodaju.",
        "continue_to_payment": "Nastavi na placanje",
        "payment_entry_title": "Korak placanja je spreman",
        "payment_session_label": "Sesija placanja",
        "payment_amount_label": "Iznos za uplatu",
        "payment_entry_note": "Vasa rezervacija je jos uvek privremena. Zavrsite placanje pre isteka rezervacije.",
        "payment_verification_note": "Placanje nije potvrdjeno dok ga sistem ne proveri.",
        "payment_entry_failed": "Nisam mogao da pokrenem korak placanja jer ova rezervacija vise nije validna za placanje.",
        "contact_command_reply": "Treba vam pomoć oko rezervacije ili plaćanja? Mogu evidentirati zahtev za podršku za tim i vratiti vam referentni broj.",
        "human_command_reply": "Ako vam je potrebna ljudska provera, mogu evidentirati zahtev za podršku za tim i vratiti referentni broj.",
        "handoff_request_recorded": "Zahtev za podršku je evidentiran. Referenca: {ref}",
        "handoff_request_failed": "Zahtev za podršku trenutno nije moguće evidentirati. Pokušajte ponovo kasnije.",
        "start_grp_private_intro": "Hvala sto ste otvorili chat iz grupe. Ture ispod ili Mini App kada budete spremni.",
        "start_sup_offer_intro": "Otvorili ste chat sa istaknute ponude: {title}. Katalog i rezervacije su u Mini App i ispod.",
        "sup_offer_not_available": "Ta ponuda vise nije dostupna. Evo trenutnog kataloga.",
        "start_grp_followup_intro": "Hvala sto nastavljate iz grupe. Koristite /contact ili /human ako tim treba vise detalja. Ture ispod.",
        "start_grp_followup_resolved_intro": "Prethodni nastavak iz grupe je zatvoren. Ture ispod. Novi zahtev: /contact ili /human.",
        "start_grp_followup_readiness_pending": "Ovaj nastavak iz grupe je u redu kod tima. Koristite /contact ili /human ako se nesto promenilo. Ture ispod.",
        "start_grp_followup_readiness_assigned": "Ovom nastavku dodeljen je clan tima. Koristite /contact ili /human za dodatke. Ture ispod.",
        "start_grp_followup_readiness_in_progress": "Tim radi na ovom nastavku. Koristite /contact ili /human za dodatke. Ture ispod.",
    },
    "hu": {
        "language_prompt": "Folytathatom az on altal valasztott nyelven. Valasszon nyelvet:",
        "language_saved": "A nyelv erre valtozott: {language_name}.",
        "welcome": "Udvozlunk. A Mini App a fo felulet a turakhoz, foglalasokhoz es fizeteshez.",
        "browse_cta": "A chatben gyors szurok es rovid lista erheto el. A teljes elmenyhez nyissa meg a Mini Appot.",
        "catalog_empty": "Jelenleg nincs nyitott tur, amit meg tudnek mutatni. Probalkozzon kesobb.",
        "catalog_intro": "Itt van legfeljebb 3 most nyitott tur:",
        "tour_missing": "Ezt a turat nem talaltam meg az aktualis katalogusban.",
        "tour_cta": "Valasszon masik turat, vagy nyissa meg a katalogust tovabbi lehetosegekert.",
        "open_catalog": "Turak megtekintese",
        "change_language": "Nyelv valtas",
        "open_mini_app": "Mini App megnyitasa",
        "back_to_catalog": "Vissza a turakhoz",
        "details_title": "Tura reszletei",
        "boarding_points": "Felszallo pontok",
        "language_note": "Tartalek nyelvi tartalmat hasznalok, mert ehhez a turahoz meg nincs forditas a valasztott nyelven.",
        "browse_by_date": "Kereses datum szerint",
        "browse_by_destination": "Kereses uticel szerint",
        "browse_by_budget": "Kereses koltsegkeret szerint",
        "date_prompt": "Milyen datumpreferenciat hasznaljak?",
        "date_weekend": "Ezen a hetvegen",
        "date_next_30_days": "A kovetkezo 30 napban",
        "date_any": "Barmilyen datum",
        "destination_prompt": "Kuljon egy uticelt vagy turanevet, es megmutatom a megfelelo lehetosegeket.",
        "destination_empty": "Kerlek kuldj egy uticelt vagy turanevet, hogy biztonsagosan tudjak keresni.",
        "destination_cancel": "Megse",
        "budget_prompt": "Valasszon koltsegkeretet a bongeszeshez.",
        "budget_any": "Barmilyen koltsegkeret",
        "budget_not_available": "A koltsegkeret szerinti kereses most nem erheto el, mert a nyitott katalogus tobb penznemet tartalmaz.",
        "filter_results_intro": "Itt van legfeljebb 3 tur a kovetkezo szurore: {filter_summary}",
        "filter_results_empty": "Nem talaltam nyitott turakat ehhez: {filter_summary}",
        "filter_results_cta": "Probalhat masik szurot vagy megnyithatja a teljes turalistat.",
        "filter_date_weekend_summary": "ezen a hetvegen",
        "filter_date_next_30_days_summary": "a kovetkezo 30 napban",
        "filter_date_any_summary": "barmilyen datum",
        "filter_destination_summary": 'uticel "{query}"',
        "filter_budget_summary": "koltsegkeret legfeljebb {amount} {currency}",
        "filter_budget_any_summary": "barmilyen koltsegkeret",
        "prepare_reservation": "Foglalasi elokeszites",
        "seat_count_prompt": "Hany helyet keszitsek elo?",
        "boarding_point_prompt": "Melyik felszallo pontot hasznaljam ehhez az elokesziteshez?",
        "preparation_unavailable": "Ez a tura jelenleg nem erheto el foglalasi elokesziteshez.",
        "preparation_summary_title": "Foglalasi elokeszitesi osszegzes",
        "seat_count_label": "Helyek",
        "estimated_total_label": "Becsult vegosszeg",
        "preparation_only_note": "Ez csak egy elokeszitesi attekintes. Foglalas meg nem jott letre.",
        "change_seat_count": "Helyek modositasa",
        "change_boarding_point": "Felszallas modositasa",
        "create_temporary_reservation": "Ideiglenes foglalas letrehozasa",
        "temporary_reservation_title": "Ideiglenes foglalas letrehozva",
        "reservation_expires_label": "A foglalas lejar",
        "reservation_reference_label": "Foglalasi azonosito",
        "temporary_reservation_note": "Ez a foglalas ideiglenes, es a fizetesi folyamat ebben a lepesben nem indul el.",
        "reservation_creation_failed": "Nem tudtam letrehozni az ideiglenes foglalast, mert a rendelkezesre allas megvaltozott vagy a tura mar nem elerheto ertekesitesre.",
        "continue_to_payment": "Tovabb a fizeteshez",
        "payment_entry_title": "A fizetesi lepes keszen all",
        "payment_session_label": "Fizetesi munkamenet",
        "payment_amount_label": "Fizetendo osszeg",
        "payment_entry_note": "A foglalas tovabbra is ideiglenes. Fejezze be a fizetest, mielott a foglalas lejar.",
        "payment_verification_note": "A fizetes csak akkor tekintheto megerositettnek, ha a rendszer ellenorizte.",
        "payment_entry_failed": "Nem tudtam elinditani a fizetesi lepest, mert ez a foglalas mar nem ervenyes fizetesre.",
        "contact_command_reply": "Segítségre van szüksége foglalással vagy fizetéssel kapcsolatban? Rögzíthetek egy támogatási kérelmet a csapat számára, és adok egy hivatkozási számot.",
        "human_command_reply": "Ha emberi felülvizsgálatra van szüksége, rögzíthetek egy támogatási kérelmet a csapat számára, és adok egy hivatkozási számot.",
        "handoff_request_recorded": "A támogatási kérelem rögzítve. Azonosító: {ref}",
        "handoff_request_failed": "A támogatási kérelmet most nem sikerült rögzíteni. Kérjük, próbálja újra később.",
        "start_grp_private_intro": "Köszönjük, hogy a csoportból megnyitotta a chatet. Túrák lent vagy Mini App, ha kész.",
        "start_sup_offer_intro": "A kiemelt ajánlatból nyitotta meg a chatet: {title}. A fő katalógus és foglalás a Mini Appban és lent.",
        "sup_offer_not_available": "Ez az ajánlat már nem elérhető. Itt a jelenlegi katalógus.",
        "start_grp_followup_intro": "Köszönjük, hogy a csoportból folytatja. /contact vagy /human, ha a csapatnak extra részlet kell. Túrák lent.",
        "start_grp_followup_resolved_intro": "Az előző csoportos követés lezárva. Túrák lent. Új kérés: /contact vagy /human.",
        "start_grp_followup_readiness_pending": "Ez a csoportos követés sorban van a csapatnál. /contact vagy /human, ha változott valami. Túrák lent.",
        "start_grp_followup_readiness_assigned": "Ehhez a követéshez csapattag van rendelve. /contact vagy /human további részletért. Túrák lent.",
        "start_grp_followup_readiness_in_progress": "A csapat ezen a követésen dolgozik. /contact vagy /human további részletért. Túrák lent.",
    },
    "it": {
        "language_prompt": "Posso continuare nella lingua che preferisci. Scegli una lingua:",
        "language_saved": "Lingua aggiornata in {language_name}.",
        "welcome": "Benvenuto. La Mini App e il punto principale per catalogo, prenotazioni e pagamento.",
        "browse_cta": "In chat puoi usare filtri rapidi o un elenco breve. Lesperienza completa e nella Mini App.",
        "catalog_empty": "Al momento non ci sono tour aperti da mostrare. Riprova piu tardi.",
        "catalog_intro": "Ecco fino a 3 tour aperti che puoi vedere adesso:",
        "tour_missing": "Non ho trovato quel tour nel catalogo attuale.",
        "tour_cta": "Scegli un altro tour oppure apri il catalogo per altre opzioni.",
        "open_catalog": "Vedi tour",
        "change_language": "Cambia lingua",
        "open_mini_app": "Apri Mini App",
        "back_to_catalog": "Torna ai tour",
        "details_title": "Dettagli tour",
        "boarding_points": "Punti di partenza",
        "language_note": "Uso contenuto di fallback perche questo tour non e ancora tradotto nella lingua selezionata.",
        "browse_by_date": "Cerca per data",
        "browse_by_destination": "Cerca per destinazione",
        "browse_by_budget": "Cerca per budget",
        "date_prompt": "Quale preferenza di data vuoi usare?",
        "date_weekend": "Questo weekend",
        "date_next_30_days": "Nei prossimi 30 giorni",
        "date_any": "Qualsiasi data",
        "destination_prompt": "Invia una destinazione o il nome del tour e ti mostro le opzioni corrispondenti.",
        "destination_empty": "Invia una destinazione o il nome di un tour per permettermi di cercare in modo sicuro.",
        "destination_cancel": "Annulla",
        "budget_prompt": "Scegli una fascia di budget per la ricerca.",
        "budget_any": "Qualsiasi budget",
        "budget_not_available": "La ricerca per budget non e disponibile ora perche il catalogo aperto contiene piu valute.",
        "filter_results_intro": "Ecco fino a 3 tour che corrispondono a: {filter_summary}",
        "filter_results_empty": "Non ho trovato tour aperti che corrispondono a: {filter_summary}",
        "filter_results_cta": "Puoi provare un altro filtro oppure aprire l'elenco completo dei tour.",
        "filter_date_weekend_summary": "questo weekend",
        "filter_date_next_30_days_summary": "i prossimi 30 giorni",
        "filter_date_any_summary": "qualsiasi data",
        "filter_destination_summary": 'destinazione "{query}"',
        "filter_budget_summary": "budget fino a {amount} {currency}",
        "filter_budget_any_summary": "qualsiasi budget",
        "prepare_reservation": "Prepara prenotazione",
        "seat_count_prompt": "Per quanti posti devo preparare la prenotazione?",
        "boarding_point_prompt": "Quale punto di partenza devo usare per questa preparazione?",
        "preparation_unavailable": "Questo tour non e disponibile ora per la preparazione della prenotazione.",
        "preparation_summary_title": "Riepilogo preparazione prenotazione",
        "seat_count_label": "Posti",
        "estimated_total_label": "Totale stimato",
        "preparation_only_note": "Questo e solo un riepilogo di preparazione. Nessuna prenotazione e stata ancora creata.",
        "change_seat_count": "Cambia posti",
        "change_boarding_point": "Cambia partenza",
        "create_temporary_reservation": "Crea prenotazione temporanea",
        "temporary_reservation_title": "Prenotazione temporanea creata",
        "reservation_expires_label": "La prenotazione scade",
        "reservation_reference_label": "Riferimento prenotazione",
        "temporary_reservation_note": "Questa prenotazione e temporanea e il pagamento non viene avviato in questo passaggio.",
        "reservation_creation_failed": "Non ho potuto creare la prenotazione temporanea perche la disponibilita e cambiata oppure il tour non e piu aperto alla vendita.",
        "continue_to_payment": "Continua al pagamento",
        "payment_entry_title": "Passaggio di pagamento pronto",
        "payment_session_label": "Sessione di pagamento",
        "payment_amount_label": "Importo da pagare",
        "payment_entry_note": "La tua prenotazione e ancora temporanea. Completa il pagamento prima della scadenza della prenotazione.",
        "payment_verification_note": "Il pagamento non e confermato finche il sistema non lo verifica.",
        "payment_entry_failed": "Non ho potuto avviare il passaggio di pagamento perche questa prenotazione non e piu valida per il pagamento.",
        "contact_command_reply": "Hai bisogno di aiuto con una prenotazione o un pagamento? Posso registrare una richiesta di supporto per il team e restituirti un numero di riferimento.",
        "human_command_reply": "Se ti serve una verifica umana, posso registrare una richiesta di supporto per il team e restituirti un numero di riferimento.",
        "handoff_request_recorded": "Richiesta di supporto registrata. Riferimento: {ref}",
        "handoff_request_failed": "Non è stato possibile registrare la richiesta di supporto in questo momento. Riprova più tardi.",
        "start_grp_private_intro": "Grazie per aver aperto la chat dal gruppo. Tour qui sotto o Mini App quando sei pronto.",
        "start_sup_offer_intro": "Hai aperto la chat da un'offerta in evidenza: {title}. Catalogo e prenotazioni nel Mini App e qui sotto.",
        "sup_offer_not_available": "Quell'offerta non è più disponibile. Ecco il catalogo attuale.",
        "start_grp_followup_intro": "Grazie per continuare dal gruppo. Usa /contact o /human se il team deve vedere altri dettagli. Tour qui sotto.",
        "start_grp_followup_resolved_intro": "Il precedente follow-up dal gruppo e' chiuso. Tour qui sotto. Nuova richiesta: /contact o /human.",
        "start_grp_followup_readiness_pending": "Questo follow-up dal gruppo e' in coda con il team. Usa /contact o /human se e' cambiato qualcosa. Tour qui sotto.",
        "start_grp_followup_readiness_assigned": "A questo follow-up e' assegnato un membro del team. Usa /contact o /human per aggiungere dettagli. Tour qui sotto.",
        "start_grp_followup_readiness_in_progress": "Il team sta lavorando su questo follow-up. Usa /contact o /human per aggiungere dettagli. Tour qui sotto.",
    },
    "de": {
        "language_prompt": "Ich kann in Ihrer bevorzugten Sprache weitermachen. Bitte waehlen Sie eine Sprache:",
        "language_saved": "Sprache aktualisiert: {language_name}.",
        "welcome": "Willkommen. Die Mini App ist die Hauptoberflaeche fuer Katalog, Buchungen und Zahlung.",
        "browse_cta": "In diesem Chat gibt es Schnellfilter und eine kurze Liste. Die volle Funktion bietet die Mini App.",
        "catalog_empty": "Zurzeit gibt es keine offenen Touren zum Anzeigen. Bitte spaeter erneut versuchen.",
        "catalog_intro": "Hier sind bis zu 3 offene Touren, die Sie jetzt ansehen koennen:",
        "tour_missing": "Ich konnte diese Tour im aktuellen Katalog nicht finden.",
        "tour_cta": "Waehlen Sie eine andere Tour oder oeffnen Sie den Katalog fuer weitere Optionen.",
        "open_catalog": "Touren ansehen",
        "change_language": "Sprache aendern",
        "open_mini_app": "Mini App oeffnen",
        "back_to_catalog": "Zurueck zu den Touren",
        "details_title": "Tourdetails",
        "boarding_points": "Einstiegsorte",
        "language_note": "Ich verwende Fallback-Inhalte, weil diese Tour noch nicht in Ihrer gewaelten Sprache uebersetzt ist.",
        "browse_by_date": "Nach Datum suchen",
        "browse_by_destination": "Nach Ziel suchen",
        "browse_by_budget": "Nach Budget suchen",
        "date_prompt": "Welche Datumpraeferenz soll ich verwenden?",
        "date_weekend": "Dieses Wochenende",
        "date_next_30_days": "Naechste 30 Tage",
        "date_any": "Beliebiges Datum",
        "destination_prompt": "Senden Sie ein Ziel oder einen Tournamen, dann zeige ich passende Optionen.",
        "destination_empty": "Bitte senden Sie ein Ziel oder einen Tournamen, damit ich sicher suchen kann.",
        "destination_cancel": "Abbrechen",
        "budget_prompt": "Waehlen Sie einen Budgetbereich fuer die Suche.",
        "budget_any": "Beliebiges Budget",
        "budget_not_available": "Budgetsuche ist derzeit nicht verfuegbar, weil der offene Katalog mehrere Waehrungen enthaelt.",
        "filter_results_intro": "Hier sind bis zu 3 Touren passend zu: {filter_summary}",
        "filter_results_empty": "Ich konnte keine offenen Touren passend zu folgendem Filter finden: {filter_summary}",
        "filter_results_cta": "Sie koennen einen anderen Filter versuchen oder die gesamte Tourliste oeffnen.",
        "filter_date_weekend_summary": "dieses Wochenende",
        "filter_date_next_30_days_summary": "naechste 30 Tage",
        "filter_date_any_summary": "beliebiges Datum",
        "filter_destination_summary": 'Ziel "{query}"',
        "filter_budget_summary": "Budget bis {amount} {currency}",
        "filter_budget_any_summary": "beliebiges Budget",
        "prepare_reservation": "Reservierung vorbereiten",
        "seat_count_prompt": "Wie viele Plaetze soll ich vorbereiten?",
        "boarding_point_prompt": "Welchen Einstiegsort soll ich fuer diese Vorbereitung verwenden?",
        "preparation_unavailable": "Diese Tour ist derzeit nicht fuer die Reservierungsvorbereitung verfuegbar.",
        "preparation_summary_title": "Zusammenfassung der Reservierungsvorbereitung",
        "seat_count_label": "Plaetze",
        "estimated_total_label": "Geschaetzte Summe",
        "preparation_only_note": "Dies ist nur eine Vorbereitungsvorschau. Es wurde noch keine Reservierung erstellt.",
        "change_seat_count": "Plaetze aendern",
        "change_boarding_point": "Einstiegsort aendern",
        "create_temporary_reservation": "Temporare Reservierung erstellen",
        "temporary_reservation_title": "Temporare Reservierung erstellt",
        "reservation_expires_label": "Reservierung laeuft ab",
        "reservation_reference_label": "Reservierungsreferenz",
        "temporary_reservation_note": "Diese Reservierung ist temporaer, und der Zahlungsschritt wird hier noch nicht gestartet.",
        "reservation_creation_failed": "Ich konnte die temporaere Reservierung nicht erstellen, weil sich die Verfuegbarkeit geaendert hat oder die Tour nicht mehr offen fuer den Verkauf ist.",
        "continue_to_payment": "Weiter zur Zahlung",
        "payment_entry_title": "Zahlungsschritt bereit",
        "payment_session_label": "Zahlungssitzung",
        "payment_amount_label": "Zu zahlender Betrag",
        "payment_entry_note": "Ihre Reservierung ist weiterhin temporaer. Bitte schliessen Sie die Zahlung ab, bevor die Reservierung ablaeuft.",
        "payment_verification_note": "Die Zahlung ist erst bestaetigt, wenn das System sie verifiziert.",
        "payment_entry_failed": "Ich konnte den Zahlungsschritt nicht starten, weil diese Reservierung nicht mehr fuer die Zahlung gueltig ist.",
        "contact_command_reply": "Brauchen Sie Hilfe bei einer Buchung oder Zahlung? Ich kann eine Support-Anfrage fuer das Team erfassen und Ihnen eine Referenznummer geben.",
        "human_command_reply": "Wenn Sie eine menschliche Pruefung brauchen, kann ich eine Support-Anfrage fuer das Team erfassen und Ihnen eine Referenznummer geben.",
        "handoff_request_recorded": "Support-Anfrage wurde erfasst. Referenz: {ref}",
        "handoff_request_failed": "Die Support-Anfrage konnte im Moment nicht erfasst werden. Bitte versuchen Sie es spaeter erneut.",
        "start_grp_private_intro": "Danke, dass Sie den Chat aus der Gruppe geoeffnet haben. Touren unten oder Mini App, wenn Sie soweit sind.",
        "start_sup_offer_intro": "Sie haben den Chat ueber ein Featured-Angebot geoeffnet: {title}. Katalog und Buchung im Mini App und unten.",
        "sup_offer_not_available": "Dieses Angebot ist nicht mehr verfuegbar. Hier der aktuelle Katalog.",
        "start_grp_followup_intro": "Danke, dass Sie aus der Gruppe weitermachen. /contact oder /human, falls das Team mehr Details sehen soll. Touren unten.",
        "start_grp_followup_resolved_intro": "Ihre vorherige Gruppen-Nachverfolgung ist geschlossen. Touren unten. Neue Anfrage: /contact oder /human.",
        "start_grp_followup_readiness_pending": "Diese Gruppen-Nachverfolgung ist beim Team eingereiht. /contact oder /human, falls sich etwas geaendert hat. Touren unten.",
        "start_grp_followup_readiness_assigned": "Dieser Nachverfolgung ist ein Teammitglied zugewiesen. /contact oder /human fuer Zusaetzliches. Touren unten.",
        "start_grp_followup_readiness_in_progress": "Das Team bearbeitet diese Nachverfolgung. /contact oder /human fuer Zusaetzliches. Touren unten.",
    },
}


def translate(language_code: str | None, key: str, **kwargs: str) -> str:
    resolved_language = language_code if language_code in TRANSLATIONS else "en"
    template = TRANSLATIONS[resolved_language].get(key, TRANSLATIONS["en"][key])
    return template.format(**kwargs)


def format_welcome(language_code: str | None) -> str:
    return "\n\n".join(
        [
            translate(language_code, "welcome"),
            translate(language_code, "browse_cta"),
        ]
    )


def format_catalog_message(language_code: str | None, cards: Iterable[CatalogTourCardRead]) -> str:
    card_lines = [
        _format_catalog_card(language_code, index=index, card=card)
        for index, card in enumerate(cards, start=1)
    ]
    if not card_lines:
        return translate(language_code, "catalog_empty")

    return "\n\n".join([translate(language_code, "catalog_intro"), *card_lines])


def format_filtered_catalog_message(
    language_code: str | None,
    cards: Iterable[CatalogTourCardRead],
    *,
    filter_summary: str,
) -> str:
    card_lines = [
        _format_catalog_card(language_code, index=index, card=card)
        for index, card in enumerate(cards, start=1)
    ]
    if not card_lines:
        return "\n\n".join(
            [
                translate(language_code, "filter_results_empty", filter_summary=filter_summary),
                translate(language_code, "filter_results_cta"),
            ]
        )

    return "\n\n".join(
        [
            translate(language_code, "filter_results_intro", filter_summary=filter_summary),
            *card_lines,
            translate(language_code, "filter_results_cta"),
        ]
    )


def format_tour_detail_message(language_code: str | None, detail: PreparedTourDetailRead) -> str:
    localized = detail.localized_content
    parts = [
        f"{translate(language_code, 'details_title')}: {localized.title}",
        _format_date_range(detail.tour.departure_datetime, detail.tour.return_datetime),
        f"{detail.tour.base_price} {detail.tour.currency}",
    ]

    if localized.short_description:
        parts.append(localized.short_description)

    if detail.boarding_points:
        points = ", ".join(point.city for point in detail.boarding_points)
        parts.append(f"{translate(language_code, 'boarding_points')}: {points}")

    if localized.used_fallback:
        parts.append(translate(language_code, "language_note"))

    if detail.tour.status == TourStatus.OPEN_FOR_SALE and detail.tour.seats_available <= 0:
        parts.append(translate(language_code, "waitlist_private_hint"))

    if not detail.sales_mode_policy.per_seat_self_service_allowed:
        parts.append(translate(language_code, "assisted_booking_detail_note"))

    parts.append(translate(language_code, "tour_cta"))
    return "\n".join(parts)


def format_reservation_preparation_summary(
    language_code: str | None,
    summary: ReservationPreparationSummaryRead,
) -> str:
    return "\n".join(
        [
            f"{translate(language_code, 'preparation_summary_title')}: {summary.tour.localized_content.title}",
            _format_date_range(summary.tour.departure_datetime, summary.tour.return_datetime),
            f"{translate(language_code, 'seat_count_label')}: {summary.seats_count}",
            f"{translate(language_code, 'boarding_points')}: {summary.boarding_point.city}, {summary.boarding_point.address}",
            f"{translate(language_code, 'estimated_total_label')}: {summary.estimated_total_amount} {summary.tour.currency}",
            translate(language_code, "preparation_only_note"),
        ]
    )


def format_temporary_reservation_confirmation(language_code: str | None, summary) -> str:
    boarding_point_text = (
        f"{summary.boarding_point.city}, {summary.boarding_point.address}"
        if summary.boarding_point is not None
        else "-"
    )
    return "\n".join(
        [
            f"{translate(language_code, 'temporary_reservation_title')}: {summary.tour.localized_content.title}",
            f"{translate(language_code, 'reservation_reference_label')}: #{summary.order.id}",
            _format_date_range(summary.tour.departure_datetime, summary.tour.return_datetime),
            f"{translate(language_code, 'seat_count_label')}: {summary.order.seats_count}",
            f"{translate(language_code, 'boarding_points')}: {boarding_point_text}",
            f"{translate(language_code, 'estimated_total_label')}: {summary.order.total_amount} {summary.order.currency}",
            f"{translate(language_code, 'reservation_expires_label')}: {summary.order.reservation_expires_at:%Y-%m-%d %H:%M}",
            translate(language_code, "temporary_reservation_note"),
        ]
    )


def format_payment_entry_message(language_code: str | None, entry: PaymentEntryRead, *, tour_title: str | None = None) -> str:
    title = tour_title or f"#{entry.order.id}"
    return "\n".join(
        [
            f"{translate(language_code, 'payment_entry_title')}: {title}",
            f"{translate(language_code, 'reservation_reference_label')}: #{entry.order.id}",
            f"{translate(language_code, 'payment_session_label')}: {entry.payment_session_reference}",
            f"{translate(language_code, 'payment_amount_label')}: {entry.payment.amount} {entry.payment.currency}",
            f"{translate(language_code, 'reservation_expires_label')}: {entry.order.reservation_expires_at:%Y-%m-%d %H:%M}",
            translate(language_code, "payment_entry_note"),
            translate(language_code, "payment_verification_note"),
        ]
    )


def language_name(language_code: str) -> str:
    return LANGUAGE_LABELS.get(language_code, language_code.upper())


def format_date_filter_summary(language_code: str | None, option: str) -> str:
    summary_key_by_option = {
        "weekend": "filter_date_weekend_summary",
        "next30": "filter_date_next_30_days_summary",
        "any": "filter_date_any_summary",
    }
    return translate(
        language_code,
        summary_key_by_option.get(option, "filter_date_any_summary"),
    )


def format_destination_filter_summary(language_code: str | None, query: str) -> str:
    return translate(language_code, "filter_destination_summary", query=query)


def format_budget_filter_summary(
    language_code: str | None,
    *,
    amount: Decimal | None,
    currency: str,
) -> str:
    if amount is None:
        return translate(language_code, "filter_budget_any_summary")
    normalized_amount = amount.normalize()
    return translate(
        language_code,
        "filter_budget_summary",
        amount=f"{normalized_amount:f}".rstrip("0").rstrip("."),
        currency=currency,
    )


def _format_catalog_card(language_code: str | None, *, index: int, card: CatalogTourCardRead) -> str:
    availability = "OK" if card.is_available else "WAIT"
    base = (
        f"{index}. {card.title}\n"
        f"{card.departure_datetime:%Y-%m-%d} -> {card.return_datetime:%Y-%m-%d}\n"
        f"{card.base_price} {card.currency} | {availability}"
    )
    if not card.sales_mode_policy.per_seat_self_service_allowed:
        return f"{base}\n{translate(language_code, 'catalog_card_assisted_hint')}"
    return base


def _format_date_range(start: datetime, end: datetime) -> str:
    return f"{start:%Y-%m-%d %H:%M} -> {end:%Y-%m-%d %H:%M}"
