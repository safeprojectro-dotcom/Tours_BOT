from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.schemas.notification import NotificationEventType, NotificationPayloadRead
from app.services.order_summary import OrderSummaryService
from app.services.payment_summary import PaymentSummaryService
from app.services.user_profile import UserProfileService

TemplateMap = dict[str, str]

NOTIFICATION_TRANSLATIONS: dict[str, TemplateMap] = {
    "en": {
        "temporary_reservation_created_title": "Temporary reservation created",
        "temporary_reservation_created_body": (
            "Your temporary reservation for {tour_title} is ready.\n"
            "Reference: #{order_id}\n"
            "Amount: {amount} {currency}\n"
            "Reservation expires: {reservation_expires_at}"
        ),
        "payment_pending_title": "Payment pending",
        "payment_pending_body": (
            "Payment is still pending for {tour_title}.\n"
            "Reference: #{order_id}\n"
            "Amount: {amount} {currency}\n"
            "Reservation expires: {reservation_expires_at}\n"
            "Payment session: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Payment confirmed",
        "payment_confirmed_body": (
            "Your payment for {tour_title} has been confirmed.\n"
            "Reference: #{order_id}\n"
            "Amount: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Departure reminder",
        "predeparture_reminder_body": (
            "Your trip {tour_title} is coming up soon.\n"
            "Reference: #{order_id}\n"
            "Departure: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Departure today",
        "departure_day_reminder_body": (
            "Your trip {tour_title} departs today.\n"
            "Reference: #{order_id}\n"
            "Departure: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Trip completed",
        "post_trip_reminder_body": (
            "Your trip {tour_title} has been completed.\n"
            "Reference: #{order_id}\n"
            "Return: {return_datetime}"
        ),
        "reservation_expired_title": "Reservation expired",
        "reservation_expired_body": (
            "Your temporary reservation for {tour_title} has expired.\n"
            "Reference: #{order_id}\n"
            "The seats were released because payment was not completed in time."
        ),
    },
    "ro": {
        "temporary_reservation_created_title": "Rezervare temporara creata",
        "temporary_reservation_created_body": (
            "Rezervarea ta temporara pentru {tour_title} este pregatita.\n"
            "Referinta: #{order_id}\n"
            "Suma: {amount} {currency}\n"
            "Rezervarea expira: {reservation_expires_at}"
        ),
        "payment_pending_title": "Plata este in asteptare",
        "payment_pending_body": (
            "Plata este inca in asteptare pentru {tour_title}.\n"
            "Referinta: #{order_id}\n"
            "Suma: {amount} {currency}\n"
            "Rezervarea expira: {reservation_expires_at}\n"
            "Sesiune plata: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Plata confirmata",
        "payment_confirmed_body": (
            "Plata pentru {tour_title} a fost confirmata.\n"
            "Referinta: #{order_id}\n"
            "Suma: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Reminder de plecare",
        "predeparture_reminder_body": (
            "Calatoria ta {tour_title} urmeaza in curand.\n"
            "Referinta: #{order_id}\n"
            "Plecare: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Plecare astazi",
        "departure_day_reminder_body": (
            "Calatoria ta {tour_title} pleaca astazi.\n"
            "Referinta: #{order_id}\n"
            "Plecare: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Calatorie finalizata",
        "post_trip_reminder_body": (
            "Calatoria ta {tour_title} a fost finalizata.\n"
            "Referinta: #{order_id}\n"
            "Intoarcere: {return_datetime}"
        ),
        "reservation_expired_title": "Rezervarea a expirat",
        "reservation_expired_body": (
            "Rezervarea ta temporara pentru {tour_title} a expirat.\n"
            "Referinta: #{order_id}\n"
            "Locurile au fost eliberate deoarece plata nu a fost finalizata la timp."
        ),
    },
    "ru": {
        "temporary_reservation_created_title": "Vremennoe bronirovanie sozdano",
        "temporary_reservation_created_body": (
            "Vashe vremennoe bronirovanie dlya {tour_title} gotovo.\n"
            "Nomer: #{order_id}\n"
            "Summa: {amount} {currency}\n"
            "Bronirovanie istekaet: {reservation_expires_at}"
        ),
        "payment_pending_title": "Ozhidaetsya oplata",
        "payment_pending_body": (
            "Oplata po ture {tour_title} vse eshche ozhidaetsya.\n"
            "Nomer: #{order_id}\n"
            "Summa: {amount} {currency}\n"
            "Bronirovanie istekaet: {reservation_expires_at}\n"
            "Sessiya oplaty: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Oplata podtverzhdena",
        "payment_confirmed_body": (
            "Oplata za {tour_title} podtverzhdena.\n"
            "Nomer: #{order_id}\n"
            "Summa: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Napominanie o vyezde",
        "predeparture_reminder_body": (
            "Vasha poezdka {tour_title} skoro nachnetsya.\n"
            "Nomer: #{order_id}\n"
            "Vyezd: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Vyyezd segodnya",
        "departure_day_reminder_body": (
            "Vasha poezdka {tour_title} otpravlyaetsya segodnya.\n"
            "Nomer: #{order_id}\n"
            "Vyezd: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Poezdka zavershena",
        "post_trip_reminder_body": (
            "Vasha poezdka {tour_title} zavershena.\n"
            "Nomer: #{order_id}\n"
            "Vozvrashchenie: {return_datetime}"
        ),
        "reservation_expired_title": "Bronirovanie isteklo",
        "reservation_expired_body": (
            "Vashe vremennoe bronirovanie dlya {tour_title} isteklo.\n"
            "Nomer: #{order_id}\n"
            "Mesta byli osvobozhdeny, potomu chto oplata ne byla zavershena vovremya."
        ),
    },
    "sr": {
        "temporary_reservation_created_title": "Privremena rezervacija je kreirana",
        "temporary_reservation_created_body": (
            "Vasa privremena rezervacija za {tour_title} je spremna.\n"
            "Referenca: #{order_id}\n"
            "Iznos: {amount} {currency}\n"
            "Rezervacija istice: {reservation_expires_at}"
        ),
        "payment_pending_title": "Placanje je na cekanju",
        "payment_pending_body": (
            "Placanje za {tour_title} je jos uvek na cekanju.\n"
            "Referenca: #{order_id}\n"
            "Iznos: {amount} {currency}\n"
            "Rezervacija istice: {reservation_expires_at}\n"
            "Sesija placanja: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Placanje potvrdjeno",
        "payment_confirmed_body": (
            "Placanje za {tour_title} je potvrdjeno.\n"
            "Referenca: #{order_id}\n"
            "Iznos: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Podsetnik za polazak",
        "predeparture_reminder_body": (
            "Tvoje putovanje {tour_title} uskoro pocinje.\n"
            "Referenca: #{order_id}\n"
            "Polazak: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Polazak danas",
        "departure_day_reminder_body": (
            "Tvoje putovanje {tour_title} polazi danas.\n"
            "Referenca: #{order_id}\n"
            "Polazak: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Putovanje zavrseno",
        "post_trip_reminder_body": (
            "Tvoje putovanje {tour_title} je zavrseno.\n"
            "Referenca: #{order_id}\n"
            "Povratak: {return_datetime}"
        ),
        "reservation_expired_title": "Rezervacija je istekla",
        "reservation_expired_body": (
            "Vasa privremena rezervacija za {tour_title} je istekla.\n"
            "Referenca: #{order_id}\n"
            "Mesta su oslobodjena jer placanje nije zavrseno na vreme."
        ),
    },
    "hu": {
        "temporary_reservation_created_title": "Ideiglenes foglalas letrehozva",
        "temporary_reservation_created_body": (
            "Az ideiglenes foglalasa keszen all ehhez: {tour_title}.\n"
            "Azonosito: #{order_id}\n"
            "Osszeg: {amount} {currency}\n"
            "A foglalas lejar: {reservation_expires_at}"
        ),
        "payment_pending_title": "Fizetes folyamatban",
        "payment_pending_body": (
            "A fizetes tovabbra is folyamatban van ehhez: {tour_title}.\n"
            "Azonosito: #{order_id}\n"
            "Osszeg: {amount} {currency}\n"
            "A foglalas lejar: {reservation_expires_at}\n"
            "Fizetesi munkamenet: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Fizetes megerositve",
        "payment_confirmed_body": (
            "A fizetes megerositve lett ehhez: {tour_title}.\n"
            "Azonosito: #{order_id}\n"
            "Osszeg: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Indulasi emlekezteto",
        "predeparture_reminder_body": (
            "A(z) {tour_title} utazas hamarosan indul.\n"
            "Azonosito: #{order_id}\n"
            "Indulas: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Indulas ma",
        "departure_day_reminder_body": (
            "A(z) {tour_title} utazas ma indul.\n"
            "Azonosito: #{order_id}\n"
            "Indulas: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Utazas befejezve",
        "post_trip_reminder_body": (
            "A(z) {tour_title} utazas befejezodott.\n"
            "Azonosito: #{order_id}\n"
            "Erkezes: {return_datetime}"
        ),
        "reservation_expired_title": "A foglalas lejart",
        "reservation_expired_body": (
            "Az ideiglenes foglalasa lejart ehhez: {tour_title}.\n"
            "Azonosito: #{order_id}\n"
            "A helyek felszabadultak, mert a fizetes nem keszult el idoben."
        ),
    },
    "it": {
        "temporary_reservation_created_title": "Prenotazione temporanea creata",
        "temporary_reservation_created_body": (
            "La tua prenotazione temporanea per {tour_title} e pronta.\n"
            "Riferimento: #{order_id}\n"
            "Importo: {amount} {currency}\n"
            "La prenotazione scade: {reservation_expires_at}"
        ),
        "payment_pending_title": "Pagamento in attesa",
        "payment_pending_body": (
            "Il pagamento per {tour_title} e ancora in attesa.\n"
            "Riferimento: #{order_id}\n"
            "Importo: {amount} {currency}\n"
            "La prenotazione scade: {reservation_expires_at}\n"
            "Sessione di pagamento: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Pagamento confermato",
        "payment_confirmed_body": (
            "Il pagamento per {tour_title} e stato confermato.\n"
            "Riferimento: #{order_id}\n"
            "Importo: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Promemoria di partenza",
        "predeparture_reminder_body": (
            "Il tuo viaggio {tour_title} partira presto.\n"
            "Riferimento: #{order_id}\n"
            "Partenza: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Partenza oggi",
        "departure_day_reminder_body": (
            "Il tuo viaggio {tour_title} parte oggi.\n"
            "Riferimento: #{order_id}\n"
            "Partenza: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Viaggio completato",
        "post_trip_reminder_body": (
            "Il tuo viaggio {tour_title} e stato completato.\n"
            "Riferimento: #{order_id}\n"
            "Rientro: {return_datetime}"
        ),
        "reservation_expired_title": "Prenotazione scaduta",
        "reservation_expired_body": (
            "La tua prenotazione temporanea per {tour_title} e scaduta.\n"
            "Riferimento: #{order_id}\n"
            "I posti sono stati rilasciati perche il pagamento non e stato completato in tempo."
        ),
    },
    "de": {
        "temporary_reservation_created_title": "Temporare Reservierung erstellt",
        "temporary_reservation_created_body": (
            "Ihre temporaere Reservierung fuer {tour_title} ist bereit.\n"
            "Referenz: #{order_id}\n"
            "Betrag: {amount} {currency}\n"
            "Reservierung laeuft ab: {reservation_expires_at}"
        ),
        "payment_pending_title": "Zahlung ausstehend",
        "payment_pending_body": (
            "Die Zahlung fuer {tour_title} ist noch ausstehend.\n"
            "Referenz: #{order_id}\n"
            "Betrag: {amount} {currency}\n"
            "Reservierung laeuft ab: {reservation_expires_at}\n"
            "Zahlungssitzung: {payment_session_reference}"
        ),
        "payment_confirmed_title": "Zahlung bestaetigt",
        "payment_confirmed_body": (
            "Die Zahlung fuer {tour_title} wurde bestaetigt.\n"
            "Referenz: #{order_id}\n"
            "Betrag: {amount} {currency}"
        ),
        "predeparture_reminder_title": "Abfahrts-Erinnerung",
        "predeparture_reminder_body": (
            "Ihre Reise {tour_title} beginnt bald.\n"
            "Referenz: #{order_id}\n"
            "Abfahrt: {departure_datetime}"
        ),
        "departure_day_reminder_title": "Abfahrt heute",
        "departure_day_reminder_body": (
            "Ihre Reise {tour_title} faehrt heute ab.\n"
            "Referenz: #{order_id}\n"
            "Abfahrt: {departure_datetime}"
        ),
        "post_trip_reminder_title": "Reise abgeschlossen",
        "post_trip_reminder_body": (
            "Ihre Reise {tour_title} wurde abgeschlossen.\n"
            "Referenz: #{order_id}\n"
            "Rueckkehr: {return_datetime}"
        ),
        "reservation_expired_title": "Reservierung abgelaufen",
        "reservation_expired_body": (
            "Ihre temporaere Reservierung fuer {tour_title} ist abgelaufen.\n"
            "Referenz: #{order_id}\n"
            "Die Plaetze wurden wieder freigegeben, weil die Zahlung nicht rechtzeitig abgeschlossen wurde."
        ),
    },
}


class NotificationPreparationService:
    def __init__(
        self,
        *,
        order_summary_service: OrderSummaryService | None = None,
        payment_summary_service: PaymentSummaryService | None = None,
        user_profile_service: UserProfileService | None = None,
    ) -> None:
        self.order_summary_service = order_summary_service or OrderSummaryService()
        self.payment_summary_service = payment_summary_service or PaymentSummaryService()
        self.user_profile_service = user_profile_service or UserProfileService()

    def list_available_event_types(self, session: Session, *, order_id: int) -> list[NotificationEventType]:
        order_summary = self.order_summary_service.get_order_summary(session, order_id=order_id)
        if order_summary is None:
            return []

        events: list[NotificationEventType] = []
        if self._is_temporary_reservation_active(order_summary):
            events.extend(
                [
                    NotificationEventType.TEMPORARY_RESERVATION_CREATED,
                    NotificationEventType.PAYMENT_PENDING,
                ]
            )
        if self._is_payment_confirmed(order_summary):
            events.append(NotificationEventType.PAYMENT_CONFIRMED)
            events.append(NotificationEventType.PREDEPARTURE_REMINDER)
            events.append(NotificationEventType.DEPARTURE_DAY_REMINDER)
            events.append(NotificationEventType.POST_TRIP_REMINDER)
        if self._is_reservation_expired(order_summary):
            events.append(NotificationEventType.RESERVATION_EXPIRED)
        return events

    def prepare_notification(
        self,
        session: Session,
        *,
        order_id: int,
        event_type: NotificationEventType,
        language_code: str | None = None,
    ) -> NotificationPayloadRead | None:
        user = self._get_user_for_order(session, order_id=order_id)
        if user is None:
            return None

        resolved_language = self._resolve_language(language_code, user.preferred_language)
        order_summary = self.order_summary_service.get_order_summary(
            session,
            order_id=order_id,
            language_code=resolved_language,
        )
        if order_summary is None:
            return None

        if event_type not in self._list_available_for_summary(order_summary):
            return None

        payment_summary = self.payment_summary_service.get_order_payment_summary(session, order_id=order_id)
        latest_payment = payment_summary.latest_payment if payment_summary is not None else None
        metadata = self._build_metadata(order_summary, latest_payment)
        title = self._translate(resolved_language, f"{event_type.value}_title")
        message = self._translate(
            resolved_language,
            f"{event_type.value}_body",
            **metadata,
        )
        return NotificationPayloadRead(
            event_type=event_type,
            order_id=order_summary.order.id,
            user_id=user.id,
            telegram_user_id=user.telegram_user_id,
            language_code=resolved_language,
            title=title,
            message=message,
            metadata=metadata,
        )

    def _get_user_for_order(self, session: Session, *, order_id: int):
        order_summary = self.order_summary_service.get_order_summary(session, order_id=order_id)
        if order_summary is None:
            return None
        return self.user_profile_service.get_user(session, user_id=order_summary.order.user_id)

    def _list_available_for_summary(self, order_summary) -> list[NotificationEventType]:
        events: list[NotificationEventType] = []
        if self._is_temporary_reservation_active(order_summary):
            events.extend(
                [
                    NotificationEventType.TEMPORARY_RESERVATION_CREATED,
                    NotificationEventType.PAYMENT_PENDING,
                ]
            )
        if self._is_payment_confirmed(order_summary):
            events.append(NotificationEventType.PAYMENT_CONFIRMED)
            events.append(NotificationEventType.PREDEPARTURE_REMINDER)
            events.append(NotificationEventType.DEPARTURE_DAY_REMINDER)
            events.append(NotificationEventType.POST_TRIP_REMINDER)
        if self._is_reservation_expired(order_summary):
            events.append(NotificationEventType.RESERVATION_EXPIRED)
        return events

    @staticmethod
    def _is_temporary_reservation_active(order_summary) -> bool:
        order = order_summary.order
        return (
            order.booking_status == BookingStatus.RESERVED
            and order.payment_status == PaymentStatus.AWAITING_PAYMENT
            and order.cancellation_status == CancellationStatus.ACTIVE
            and order.reservation_expires_at is not None
        )

    @staticmethod
    def _is_payment_confirmed(order_summary) -> bool:
        order = order_summary.order
        return (
            order.booking_status == BookingStatus.CONFIRMED
            and order.payment_status == PaymentStatus.PAID
            and order.cancellation_status == CancellationStatus.ACTIVE
        )

    @staticmethod
    def _is_reservation_expired(order_summary) -> bool:
        order = order_summary.order
        return (
            order.booking_status == BookingStatus.RESERVED
            and order.payment_status == PaymentStatus.UNPAID
            and order.cancellation_status == CancellationStatus.CANCELLED_NO_PAYMENT
            and order.reservation_expires_at is None
        )

    @staticmethod
    def _resolve_language(explicit_language: str | None, user_language: str | None) -> str:
        candidate = explicit_language or user_language or "en"
        return candidate if candidate in NOTIFICATION_TRANSLATIONS else "en"

    @staticmethod
    def _build_metadata(order_summary, latest_payment) -> dict[str, Any]:
        order = order_summary.order
        return {
            "tour_title": order_summary.tour.localized_content.title,
            "order_id": order.id,
            "amount": order.total_amount,
            "currency": order.currency,
            "departure_datetime": f"{order_summary.tour.departure_datetime:%Y-%m-%d %H:%M}",
            "return_datetime": f"{order_summary.tour.return_datetime:%Y-%m-%d %H:%M}",
            "reservation_expires_at": (
                f"{order.reservation_expires_at:%Y-%m-%d %H:%M}" if order.reservation_expires_at is not None else "-"
            ),
            "payment_session_reference": (
                latest_payment.external_payment_id
                if latest_payment is not None and latest_payment.external_payment_id is not None
                else "-"
            ),
        }

    @staticmethod
    def _translate(language_code: str, key: str, **kwargs: Any) -> str:
        template = NOTIFICATION_TRANSLATIONS.get(language_code, NOTIFICATION_TRANSLATIONS["en"]).get(
            key,
            NOTIFICATION_TRANSLATIONS["en"][key],
        )
        normalized = {name: str(value) for name, value in kwargs.items()}
        return template.format(**normalized)
