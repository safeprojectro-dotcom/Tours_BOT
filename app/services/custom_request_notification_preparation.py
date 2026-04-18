"""W1: fact-bound message preparation for Mode 3 custom request lifecycle (no dispatch)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.enums import CustomMarketplaceRequestStatus
from app.repositories.custom_marketplace import CustomMarketplaceRequestRepository
from app.schemas.custom_request_notification import (
    CustomRequestNotificationEventType,
    CustomRequestNotificationPayloadRead,
)
from app.services.user_profile import UserProfileService

_TERMINAL: frozenset[CustomMarketplaceRequestStatus] = frozenset(
    {
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        CustomMarketplaceRequestStatus.CANCELLED,
        CustomMarketplaceRequestStatus.FULFILLED,
    },
)

# en + ro; other languages fall back to en (same pattern as notification_preparation).
_CUSTOM_REQUEST_NOTIFICATION_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "custom_request_recorded_title": "Custom trip request received",
        "custom_request_recorded_body": (
            "We received your custom trip request (reference #{request_id}). "
            "This is not a booking, reservation, or payment.\n\n"
            "Check **My requests** in the Mini App for updates. We do not message you for every change."
        ),
        "custom_request_under_review_title": "Your request is being reviewed",
        "custom_request_under_review_body": (
            "Your custom trip request #{request_id} is under review with our team or suppliers. "
            "This is still not a confirmed booking or payment.\n\n"
            "Open **My requests** in the Mini App for the latest status."
        ),
        "custom_request_app_followup_may_exist_title": "Update on your custom request",
        "custom_request_app_followup_may_exist_body": (
            "Your custom trip request #{request_id} may have a next step in the Mini App when the system allows it.\n\n"
            "{followup_paragraph}"
            "This message does not mean payment is due or a booking is confirmed — only the app can show what applies."
        ),
        "custom_request_app_followup_paragraph_when_hinted": (
            "Open **My requests**, then your request detail: if a button appears, it reflects what the app can offer right "
            "now.\n\n"
        ),
        "custom_request_closed_title": "Custom request closed",
        "custom_request_closed_body": (
            "Your custom trip request #{request_id} is closed in the app. "
            "This is not a payment receipt or a trip confirmation.\n\n"
            "You can still open **My requests** for reference. No further in-app steps are expected for this request."
        ),
        "custom_request_selection_recorded_title": "Selection recorded",
        "custom_request_selection_recorded_body": (
            "For custom trip request #{request_id}, a proposal was marked as the selected option on our side. "
            "That is still not a confirmed booking, hold, or payment.\n\n"
            "Open **My requests** for full details. If the app can show a next step for this request, it will appear here."
        ),
        "custom_request_in_app_preview_disclaimer": (
            "This wording is shown in the Mini App only. It is not proof that a separate Telegram or other message was sent."
        ),
        "admin_custom_request_prepared_internal_disclaimer": (
            "Internal reference only. This text is generated from the current request state for manual use. "
            "It has not been sent to the customer on Telegram or elsewhere, is not queued in the Layer A order "
            "notification outbox, and does not prove delivery, read, or receipt."
        ),
    },
    "ro": {
        "custom_request_recorded_title": "Cerere de tur personalizat primită",
        "custom_request_recorded_body": (
            "Am primit cererea ta personalizată (referință #{request_id}). "
            "Nu este o rezervare sau o plată.\n\n"
            "Verifică **Cererile mele** în Mini App pentru actualizări. Nu trimitem un mesaj la fiecare modificare."
        ),
        "custom_request_under_review_title": "Cererea ta este în analiză",
        "custom_request_under_review_body": (
            "Cererea ta #{request_id} este în analiză la echipă sau furnizori. "
            "Încă nu este o rezervare confirmată sau o plată.\n\n"
            "Deschide **Cererile mele** în Mini App pentru statusul curent."
        ),
        "custom_request_app_followup_may_exist_title": "Actualizare despre cererea ta",
        "custom_request_app_followup_may_exist_body": (
            "Cererea ta #{request_id} poate avea un pas următor în Mini App când sistemul permite.\n\n"
            "{followup_paragraph}"
            "Acest mesaj nu înseamnă că plata e datorată sau că rezervarea e confirmată — doar aplicația arată ce se aplică."
        ),
        "custom_request_app_followup_paragraph_when_hinted": (
            "Deschide **Cererile mele**, apoi detaliul cererii: dacă apare un buton, reflectă ce poate oferi aplicația acum.\n\n"
        ),
        "custom_request_closed_title": "Cerere închisă",
        "custom_request_closed_body": (
            "Cererea ta #{request_id} este închisă în aplicație. "
            "Nu este o confirmare de plată sau de excursie.\n\n"
            "Poți deschide în continuare **Cererile mele** ca referință. Nu sunt așteptați pași suplimentari în app."
        ),
        "custom_request_selection_recorded_title": "Selecție înregistrată",
        "custom_request_selection_recorded_body": (
            "Pentru cererea #{request_id}, o ofertă a fost marcată ca opțiune selectată în fluxul nostru. "
            "Asta nu înseamnă încă rezervare confirmată, loc reținut sau plată.\n\n"
            "Deschide **Cererile mele** pentru detalii. Dacă aplicația poate arăta un pas următor, va apărea aici."
        ),
        "custom_request_in_app_preview_disclaimer": (
            "Acest text este afișat doar în Mini App. Nu dovedește că ți s-a trimis un mesaj separat pe Telegram sau altundeva."
        ),
        "admin_custom_request_prepared_internal_disclaimer": (
            "Doar pentru uz intern. Textul este generat din starea curentă a cererii, pentru folosire manuală. "
            "Nu a fost trimis clientului pe Telegram sau altundeva, nu este pus la coadă în outbox-ul de notificări "
            "al comenzilor (Layer A) și nu dovedește livrare, citire sau confirmare de primire."
        ),
    },
}


class CustomRequestNotificationPreparationService:
    """Prepares customer-safe copy; does not enqueue Layer A notification_outbox rows."""

    def __init__(
        self,
        *,
        request_repository: CustomMarketplaceRequestRepository | None = None,
        user_profile_service: UserProfileService | None = None,
    ) -> None:
        self._requests = request_repository or CustomMarketplaceRequestRepository()
        self._users = user_profile_service or UserProfileService()

    def prepare(
        self,
        session: Session,
        *,
        request_id: int,
        event_type: CustomRequestNotificationEventType,
        language_code: str | None = None,
        app_next_step_maybe_available: bool | None = None,
    ) -> CustomRequestNotificationPayloadRead | None:
        row = self._requests.get(session, request_id=request_id)
        if row is None:
            return None
        user = self._users.get_user(session, user_id=row.user_id)
        if user is None:
            return None

        if not self._event_allowed_for_row(
            row=row,
            event_type=event_type,
            app_next_step_maybe_available=app_next_step_maybe_available,
        ):
            return None

        resolved_lang = self._resolve_language(language_code, user.preferred_language)
        title_key = f"{event_type.value}_title"
        body_key = f"{event_type.value}_body"
        meta: dict[str, Any] = {
            "request_id": row.id,
            "request_status": row.status.value,
            "domain": "custom_request_lifecycle",
        }

        followup_paragraph = ""
        if event_type == CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST:
            followup_paragraph = self._translate(
                resolved_lang,
                "custom_request_app_followup_paragraph_when_hinted",
            )
            meta["app_next_step_maybe_available"] = True
        title = self._translate(resolved_lang, title_key)
        if event_type == CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST:
            message = self._translate(
                resolved_lang,
                body_key,
                request_id=str(row.id),
                followup_paragraph=followup_paragraph,
            )
        else:
            message = self._translate(resolved_lang, body_key, request_id=str(row.id))

        return CustomRequestNotificationPayloadRead(
            event_type=event_type,
            request_id=row.id,
            user_id=user.id,
            telegram_user_id=user.telegram_user_id,
            language_code=resolved_lang,
            title=title,
            message=message,
            metadata=meta,
        )

    def preview_disclaimer_text(
        self,
        *,
        language_code: str | None,
        user_preferred_language: str | None,
    ) -> str:
        """W2: single disclaimer line for in-app lifecycle preview (not delivery proof)."""
        lang = self._resolve_language(language_code, user_preferred_language)
        return self._translate(lang, "custom_request_in_app_preview_disclaimer")

    def admin_prepared_internal_disclaimer_text(
        self,
        *,
        language_code: str | None,
        user_preferred_language: str | None,
    ) -> str:
        """W3: ops/admin disclaimer — prepared only, not sent, not Layer A outbox, not receipt proof."""
        lang = self._resolve_language(language_code, user_preferred_language)
        return self._translate(lang, "admin_custom_request_prepared_internal_disclaimer")

    def _event_allowed_for_row(
        self,
        *,
        row: CustomMarketplaceRequest,
        event_type: CustomRequestNotificationEventType,
        app_next_step_maybe_available: bool | None,
    ) -> bool:
        st = row.status
        if event_type == CustomRequestNotificationEventType.REQUEST_RECORDED:
            return st == CustomMarketplaceRequestStatus.OPEN
        if event_type == CustomRequestNotificationEventType.REQUEST_UNDER_REVIEW:
            return st == CustomMarketplaceRequestStatus.UNDER_REVIEW
        if event_type == CustomRequestNotificationEventType.REQUEST_CLOSED:
            return st in _TERMINAL
        if event_type == CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST:
            return (
                st == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED
                and app_next_step_maybe_available is True
            )
        if event_type == CustomRequestNotificationEventType.REQUEST_SELECTION_RECORDED:
            return st == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED
        return False

    @staticmethod
    def _resolve_language(requested: str | None, user_preferred: str | None) -> str:
        code = (requested or user_preferred or "en").lower().split("-")[0]
        if code in _CUSTOM_REQUEST_NOTIFICATION_TEMPLATES:
            return code
        return "en"

    @staticmethod
    def _translate(lang: str, key: str, **kwargs: str) -> str:
        table = _CUSTOM_REQUEST_NOTIFICATION_TEMPLATES.get(lang, _CUSTOM_REQUEST_NOTIFICATION_TEMPLATES["en"])
        template = table.get(key) or _CUSTOM_REQUEST_NOTIFICATION_TEMPLATES["en"][key]
        return template.format(**kwargs) if kwargs else template
