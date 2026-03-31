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


def build_mini_app_help_read() -> MiniAppHelpRead:
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
                title="Need a person?",
                bullets=[
                    "For disputes, changes, or complex cases, human support may be required.",
                    "Use your usual Telegram bot chat for the operator when that workflow is available.",
                ],
            ),
        ],
        operator_notice=(
            "Live operator handoff from this Mini App is not implemented yet. "
            "No request is sent to a human from this screen; this is information only."
        ),
        when_to_contact_support=(
            "Contact support through the main sales bot in Telegram when you need changes, refunds, "
            "or help that this app cannot complete."
        ),
    )


class MiniAppHelpSettingsService:
    def __init__(self, user_profile_service: UserProfileService | None = None) -> None:
        self.user_profile_service = user_profile_service or UserProfileService()

    @staticmethod
    def get_help_read() -> MiniAppHelpRead:
        return build_mini_app_help_read()

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
