from __future__ import annotations

from sqlalchemy.orm import Session

from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.schemas.mini_app import (
    MiniAppHelpCategoryRead,
    MiniAppHelpRead,
    MiniAppSettingsRead,
)
from app.services.user_profile import UserProfileService


def _normalize_help_language(language_code: str | None) -> str:
    if not language_code:
        return "en"
    low = language_code.strip().lower()
    if low.startswith("ro"):
        return "ro"
    return "en"


def _build_help_en() -> MiniAppHelpRead:
    return MiniAppHelpRead(
        title="Help",
        intro=(
            "This Mini App helps you browse tours, place a time-limited hold, and start payment. "
            "Information here is general guidance only."
        ),
        categories=[
            MiniAppHelpCategoryRead(
                title="Reservations & payment",
                bullets=[
                    "A temporary reservation has a deadline; pay before it ends or the hold may be released.",
                    "Payment is only confirmed after the backend reconciliation marks it paid — not when you tap Pay.",
                    "If checkout opens in an external browser, complete the flow there and return here to refresh status later.",
                ],
            ),
            MiniAppHelpCategoryRead(
                title="Language & content",
                bullets=[
                    "Tour text may fall back to another language if a translation is missing — the app will say so.",
                    "You can change the display language in Settings when available.",
                ],
            ),
            MiniAppHelpCategoryRead(
                title="Scripted help vs human help",
                bullets=[
                    "This screen explains how the app works — it is not a live chat with an operator.",
                    "For payment problems, discounts, custom pickup, complaints, or anything risky, a human may need to review your case.",
                    "On Payment, Booking detail, or My bookings, tap Log support request when you see it — this stores a request for the team to review later (same idea as the Need help? banner on My bookings).",
                ],
            ),
        ],
        operator_notice=(
            "Live operator chat from this Mini App is not implemented. "
            "Log support request only adds an internal queue record; it does not connect you to someone in real time. "
            "Use the Telegram bot chat for follow-up and /contact or /human when you need help."
        ),
        when_to_contact_support=(
            "Use Log support request from a booking or payment screen, or the Need help? section on My bookings, when something is wrong; "
            "or write in the Telegram bot with /contact or /human for complex cases. "
            "The team may respond through normal channels when available."
        ),
    )


def _build_help_ro() -> MiniAppHelpRead:
    return MiniAppHelpRead(
        title="Ajutor",
        intro=(
            "Mini App te ajuta sa vezi tururi, sa obtii o rezervare temporara cu termen, si sa pornesti plata. "
            "Informatiile de aici sunt orientative."
        ),
        categories=[
            MiniAppHelpCategoryRead(
                title="Rezervari si plata",
                bullets=[
                    "Rezervarea temporara are deadline; plateste inainte sa expire, altfel hold-ul poate fi eliberat.",
                    "Plata este confirmata doar dupa ce backend-ul o marcheaza platita — nu in momentul cand apesi Plateste.",
                    "Daca plata se deschide intr-un browser extern, finalizeaza acolo si revino aici pentru status.",
                ],
            ),
            MiniAppHelpCategoryRead(
                title="Limba si continut",
                bullets=[
                    "Textul unui tur poate folosi limba de rezerva daca lipseste traducerea — aplicatia o va indica.",
                    "Poti schimba limba afisata din Setari cand este disponibil.",
                ],
            ),
            MiniAppHelpCategoryRead(
                title="Ajutor in aplicatie vs om",
                bullets=[
                    "Acest ecran explica cum functioneaza aplicatia — nu este chat live cu operator.",
                    "Pentru probleme de plata, reduceri, imbarcare speciala, reclamatii sau cazuri riscante, poate fi nevoie de om.",
                    "La Plata, Detalii rezervare sau Rezervarile mele, apasa „Trimite cerere de suport” cand apare — la fel ca si bannerul Ai nevoie de ajutor?; creeaza o cerere pentru echipa, fara chat live.",
                ],
            ),
        ],
        operator_notice=(
            "Chat live cu operator din Mini App nu este implementat. "
            "„Trimite cerere de suport” adauga doar o inregistrare interna; nu te conecteaza la cineva in timp real. "
            "Foloseste chat-ul cu botul Telegram pentru mesaje si comenzile /contact sau /human."
        ),
        when_to_contact_support=(
            "Foloseste Trimite cerere de suport de pe ecranul de plata sau rezervare, sau sectiunea Ai nevoie de ajutor? la Rezervarile mele; "
            "sau scrie in botul Telegram cu /contact sau /human pentru cazuri complexe. "
            "Echipa poate raspunde prin canale obisnuite cand este posibil."
        ),
    )


class MiniAppHelpSettingsService:
    def __init__(self, user_profile_service: UserProfileService | None = None) -> None:
        self.user_profile_service = user_profile_service or UserProfileService()

    @staticmethod
    def get_help_read(language_code: str | None = None) -> MiniAppHelpRead:
        return _build_help_ro() if _normalize_help_language(language_code) == "ro" else _build_help_en()

    def get_settings_read(
        self,
        session: Session,
        *,
        telegram_user_id: int | None,
    ) -> MiniAppSettingsRead:
        settings = get_settings()
        supported = list(settings.telegram_supported_language_codes)
        default_ui = settings.mini_app_default_language.strip().lower()
        if default_ui not in supported and supported:
            default_ui = supported[0]

        active: str | None = None
        if telegram_user_id is not None:
            user = self.user_profile_service.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
            if user is not None and user.preferred_language in supported:
                active = user.preferred_language

        resolved = active if active is not None else default_ui
        if resolved not in supported and supported:
            resolved = supported[0]

        return MiniAppSettingsRead(
            supported_languages=supported,
            mini_app_default_language=default_ui,
            active_language=active,
            resolved_language=resolved,
            mock_payment_completion_enabled=settings.enable_mock_payment_completion,
        )

    def set_language_preference(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        language_code: str,
    ) -> str | None:
        settings = get_settings()
        supported = set(settings.telegram_supported_language_codes)
        normalized = language_code.strip().lower()
        if normalized not in supported:
            return None

        sync = TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)
        existing = sync.user_repository.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if existing is None:
            sync.sync_private_user(
                session,
                telegram_user_id=telegram_user_id,
                username=None,
                first_name=None,
                last_name=None,
                telegram_language_code=normalized,
            )
            return normalized

        updated = sync.set_preferred_language(
            session,
            telegram_user_id=telegram_user_id,
            language_code=normalized,
        )
        return None if updated is None else normalized
