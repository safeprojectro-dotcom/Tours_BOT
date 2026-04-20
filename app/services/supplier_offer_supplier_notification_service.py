"""Supplier-facing Telegram notifications for moderation/publication lifecycle changes."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.repositories.user import UserRepository
from app.services.telegram_showcase_client import TelegramShowcaseSendError, send_private_text_message

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "approved_title": "Offer approved",
        "approved_body": "Offer #{offer_id} \"{title}\" was approved. Publication is a separate admin action.",
        "rejected_title": "Offer rejected",
        "rejected_body": "Offer #{offer_id} \"{title}\" was rejected.\nReason: {reason}",
        "published_title": "Offer published",
        "published_body": "Offer #{offer_id} \"{title}\" is now published in the showcase channel.",
        "retracted_title": "Offer retracted",
        "retracted_body": "Offer #{offer_id} \"{title}\" was retracted from active publication visibility.",
    },
    "ro": {
        "approved_title": "Oferta a fost aprobată",
        "approved_body": "Oferta #{offer_id} \"{title}\" a fost aprobată. Publicarea este un pas admin separat.",
        "rejected_title": "Oferta a fost respinsă",
        "rejected_body": "Oferta #{offer_id} \"{title}\" a fost respinsă.\nMotiv: {reason}",
        "published_title": "Oferta a fost publicată",
        "published_body": "Oferta #{offer_id} \"{title}\" este acum publicată în canalul de vitrină.",
        "retracted_title": "Oferta a fost retrasă",
        "retracted_body": "Oferta #{offer_id} \"{title}\" a fost retrasă din vizibilitatea activă de publicare.",
    },
}


class SupplierOfferSupplierNotificationService:
    def __init__(self) -> None:
        self._offers = SupplierOfferRepository()
        self._users = UserRepository()

    def notify_approved(self, session: Session, *, offer_id: int) -> bool:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            return False
        return self._notify(
            session,
            offer=offer,
            title_key="approved_title",
            body_key="approved_body",
        )

    def notify_rejected(self, session: Session, *, offer_id: int, reason: str) -> bool:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            return False
        return self._notify(
            session,
            offer=offer,
            title_key="rejected_title",
            body_key="rejected_body",
            reason=reason,
        )

    def notify_published(self, session: Session, *, offer_id: int) -> bool:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            return False
        return self._notify(
            session,
            offer=offer,
            title_key="published_title",
            body_key="published_body",
        )

    def notify_retracted(self, session: Session, *, offer_id: int) -> bool:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            return False
        return self._notify(
            session,
            offer=offer,
            title_key="retracted_title",
            body_key="retracted_body",
        )

    def _notify(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
        title_key: str,
        body_key: str,
        reason: str | None = None,
    ) -> bool:
        telegram_user_id = offer.supplier.primary_telegram_user_id if offer.supplier is not None else None
        if telegram_user_id is None:
            return False
        settings = get_settings()
        token = (settings.telegram_bot_token or "").strip()
        if not token:
            return False
        user = self._users.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        language = ((user.preferred_language if user is not None else None) or "ro").lower()
        if language not in _TEXTS:
            language = "en"
        t = _TEXTS[language]
        text = (
            f"{t[title_key]}\n\n"
            + t[body_key].format(
                offer_id=offer.id,
                title=offer.title,
                reason=(reason or "").strip() or "-",
            )
        )
        try:
            send_private_text_message(
                bot_token=token,
                telegram_user_id=telegram_user_id,
                text=text,
            )
        except TelegramShowcaseSendError:
            return False
        return True
