"""Central-admin moderation + showcase publication for supplier offers (Track 3)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.enums import SupplierOfferLifecycle
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead, AdminSupplierOfferShowcasePreviewRead
from app.services.supplier_offer_deep_link import mini_app_supplier_offer_url, private_bot_deeplink
from app.services.supplier_offer_showcase_message import build_showcase_publication
from app.services.telegram_showcase_client import TelegramShowcaseSendError, delete_channel_message, send_showcase_publication


class SupplierOfferModerationNotFoundError(Exception):
    pass


class SupplierOfferModerationStateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOfferPublicationConfigError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOfferModerationService:
    def __init__(self) -> None:
        self._offers = SupplierOfferRepository()

    def _row(self, session: Session, offer_id: int) -> SupplierOffer:
        row = self._offers.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferModerationNotFoundError
        return row

    def _to_read(self, row: SupplierOffer) -> AdminSupplierOfferRead:
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def approve(self, session: Session, *, offer_id: int) -> AdminSupplierOfferRead:
        row = self._row(session, offer_id)
        if row.lifecycle_status != SupplierOfferLifecycle.READY_FOR_MODERATION:
            raise SupplierOfferModerationStateError(
                "Only offers in ready_for_moderation can be approved.",
            )
        row.lifecycle_status = SupplierOfferLifecycle.APPROVED
        row.moderation_rejection_reason = None
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)

    def reject(self, session: Session, *, offer_id: int, reason: str) -> AdminSupplierOfferRead:
        row = self._row(session, offer_id)
        if row.lifecycle_status != SupplierOfferLifecycle.READY_FOR_MODERATION:
            raise SupplierOfferModerationStateError(
                "Only offers in ready_for_moderation can be rejected.",
            )
        row.lifecycle_status = SupplierOfferLifecycle.REJECTED
        row.moderation_rejection_reason = reason.strip()
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)

    def showcase_preview(
        self,
        session: Session,
        *,
        offer_id: int,
        settings: Settings | None = None,
    ) -> AdminSupplierOfferShowcasePreviewRead:
        """Exact caption/CTA shape for channel publish; **does not** call Telegram (B12/B13.4)."""
        row = self._row(session, offer_id)
        cfg = settings or get_settings()
        pub = build_showcase_publication(row, cfg)
        photo = (pub.photo_url or "").strip()
        is_photo = bool(photo)
        detalii_href: str | None = None
        rezerva_href: str | None = None
        uname = (cfg.telegram_bot_username or "").strip().lstrip("@")
        mini_base = (cfg.telegram_mini_app_url or "").strip().rstrip("/")
        if uname:
            detalii_href = private_bot_deeplink(bot_username=uname, offer_id=offer_id)
        if mini_base:
            rezerva_href = mini_app_supplier_offer_url(mini_app_url=mini_base, offer_id=offer_id)
        disable_preview = not is_photo
        lc = row.lifecycle_status
        lifecycle_label = lc.value

        channel_ok = bool((cfg.telegram_offer_showcase_channel_id or "").strip())
        token_ok = bool((cfg.telegram_bot_token or "").strip())
        warnings: list[str] = []

        if lc == SupplierOfferLifecycle.PUBLISHED:
            warnings.append("Offer is already published.")
        elif lc != SupplierOfferLifecycle.APPROVED:
            warnings.append("Only approved offers can be published to the showcase.")

        if not uname:
            warnings.append(
                "telegram_bot_username is not set; bot (Detalii) link URL is omitted from preview CTAs.",
            )
        if not mini_base:
            warnings.append(
                "telegram_mini_app_url is not set; Mini App (Rezervă) link URL is omitted from preview CTAs.",
            )
        if lc == SupplierOfferLifecycle.APPROVED and not (channel_ok and token_ok):
            warnings.append(
                "TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID and TELEGRAM_BOT_TOKEN must both be configured for POST /publish.",
            )

        can_publish = (
            lc == SupplierOfferLifecycle.APPROVED and channel_ok and token_ok
        )

        return AdminSupplierOfferShowcasePreviewRead(
            supplier_offer_id=offer_id,
            lifecycle_status=lifecycle_label,
            caption_html=pub.caption_html,
            publication_mode="photo_with_caption" if is_photo else "text_only",
            showcase_photo_url=pub.photo_url,
            disable_web_page_preview=disable_preview,
            cta_detalii_href=detalii_href,
            cta_rezerva_href=rezerva_href,
            can_publish_now=can_publish,
            warnings=warnings,
        )

    def publish(
        self,
        session: Session,
        *,
        offer_id: int,
        settings: Settings | None = None,
    ) -> tuple[AdminSupplierOfferRead, int]:
        cfg = settings or get_settings()
        row = self._row(session, offer_id)
        if row.lifecycle_status == SupplierOfferLifecycle.PUBLISHED:
            raise SupplierOfferModerationStateError("Offer is already published.")
        if row.lifecycle_status != SupplierOfferLifecycle.APPROVED:
            raise SupplierOfferModerationStateError(
                "Only approved offers can be published to the showcase.",
            )
        channel_id = (cfg.telegram_offer_showcase_channel_id or "").strip()
        token = (cfg.telegram_bot_token or "").strip()
        if not channel_id or not token:
            raise SupplierOfferPublicationConfigError(
                "Set TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID and TELEGRAM_BOT_TOKEN to publish.",
            )
        pub = build_showcase_publication(row, cfg)
        try:
            message_id = send_showcase_publication(
                bot_token=token,
                chat_id=channel_id,
                caption_html=pub.caption_html,
                photo_url=pub.photo_url,
            )
        except TelegramShowcaseSendError as exc:
            raise SupplierOfferModerationStateError(f"Telegram publish failed: {exc}") from exc

        row.lifecycle_status = SupplierOfferLifecycle.PUBLISHED
        row.published_at = datetime.now(UTC)
        row.showcase_chat_id = channel_id
        row.showcase_message_id = message_id
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row), message_id

    def retract_published(
        self,
        session: Session,
        *,
        offer_id: int,
        settings: Settings | None = None,
    ) -> AdminSupplierOfferRead:
        cfg = settings or get_settings()
        row = self._row(session, offer_id)
        if row.lifecycle_status != SupplierOfferLifecycle.PUBLISHED:
            raise SupplierOfferModerationStateError(
                "Only published offers can be retracted.",
            )
        token = (cfg.telegram_bot_token or "").strip()
        chat_id = (row.showcase_chat_id or "").strip()
        message_id = row.showcase_message_id
        # Best-effort channel cleanup: retract must still work if Telegram deletion fails.
        if token and chat_id and message_id is not None:
            try:
                delete_channel_message(
                    bot_token=token,
                    chat_id=chat_id,
                    message_id=message_id,
                )
            except TelegramShowcaseSendError:
                pass
        row.lifecycle_status = SupplierOfferLifecycle.APPROVED
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)

    def list_offers(
        self,
        session: Session,
        *,
        lifecycle_status: SupplierOfferLifecycle | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdminSupplierOfferRead]:
        rows = self._offers.list_for_admin(
            session,
            lifecycle_status=lifecycle_status,
            limit=limit,
            offset=offset,
        )
        return [self._to_read(r) for r in rows]
