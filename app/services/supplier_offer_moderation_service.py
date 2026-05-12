"""Central-admin moderation + showcase publication for supplier offers (Track 3)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.enums import SupplierOfferLifecycle, SupplierOfferShowcasePublishActorSurface
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import (
    AdminShowcasePublicationPayloadRead,
    AdminSupplierOfferRead,
    AdminSupplierOfferShowcaseChannelPayloadRead,
    AdminSupplierOfferShowcasePreviewRead,
)
from app.services.supplier_offer_deep_link import (
    mini_app_supplier_offer_url,
    mini_app_tour_channel_startapp_url,
    mini_app_tour_detail_url,
    normalize_telegram_mini_app_short_name_for_url,
    private_bot_deeplink,
)
from app.services.supplier_offer_channel_publish_gate import (
    channel_publish_exact_tour_ready,
    tour_code_for_active_execution_link,
)
from app.services.showcase_channel_adapter import (
    TELEGRAM_SHOWCASE_PROVIDER,
    ShowcaseChannelPublishRequest,
    TelegramShowcaseChannelAdapter,
    telegram_showcase_channel_publish_request_preview,
)
from app.services.supplier_offer_showcase_cover_sendability import (
    is_raw_cover_reference_sendable_for_telegram_sendphoto,
)
from app.services.supplier_offer_showcase_message import (
    ShowcasePublication,
    build_showcase_publication,
    showcase_photo_send_argument_from_offer,
)
from app.services.supplier_offer_showcase_publish_attempt_service import SupplierOfferShowcasePublishAttemptService
from app.services.telegram_showcase_client import TelegramShowcaseSendError, delete_channel_message


def _showcase_publish_payload_fingerprint(publication: ShowcasePublication) -> str:
    raw = ((publication.caption_html or "") + "\0" + (publication.photo_url or "")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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
        self._showcase_publish_attempts = SupplierOfferShowcasePublishAttemptService()

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

    def _showcase_publication_and_rezerva_tour_code(
        self,
        session: Session,
        *,
        offer_id: int,
        row: SupplierOffer,
        cfg: Settings,
    ) -> tuple[ShowcasePublication, str | None, bool, list[str]]:
        """B15C: for approved/published offers, Rezervă uses exact tour when execution + catalog gates pass."""
        lc = row.lifecycle_status
        if lc in (SupplierOfferLifecycle.APPROVED, SupplierOfferLifecycle.PUBLISHED):
            tc = tour_code_for_active_execution_link(session, offer_id=offer_id)
            exact_ok, exact_reasons = channel_publish_exact_tour_ready(session, offer_id=offer_id)
            display_code = tc if exact_ok else None
            pub = build_showcase_publication(
                row,
                cfg,
                rezerva_tour_code=display_code,
                channel_rezerva_requires_exact_tour=True,
            )
            return pub, display_code, exact_ok, exact_reasons
        pub = build_showcase_publication(row, cfg)
        return pub, None, False, []

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
        pub, display_code, exact_ok, exact_reasons = self._showcase_publication_and_rezerva_tour_code(
            session,
            offer_id=offer_id,
            row=row,
            cfg=cfg,
        )
        photo = (pub.photo_url or "").strip()
        is_photo = bool(photo)
        detalii_href: str | None = None
        rezerva_href: str | None = None
        uname = (cfg.telegram_bot_username or "").strip().lstrip("@")
        mini_base = (cfg.telegram_mini_app_url or "").strip().rstrip("/")
        if uname:
            detalii_href = private_bot_deeplink(bot_username=uname, offer_id=offer_id)
        if display_code:
            rezerva_href = None
            if uname:
                try:
                    rezerva_href = mini_app_tour_channel_startapp_url(
                        bot_username=uname,
                        tour_code=display_code,
                        mini_app_short_name=normalize_telegram_mini_app_short_name_for_url(
                            getattr(cfg, "telegram_mini_app_short_name", None)
                        ),
                    )
                except ValueError:
                    rezerva_href = None
            if rezerva_href is None and mini_base:
                rezerva_href = mini_app_tour_detail_url(
                    mini_app_url=mini_base,
                    tour_code=display_code,
                )
        elif mini_base:
            if row.lifecycle_status is SupplierOfferLifecycle.APPROVED:
                rezerva_href = None
            else:
                rezerva_href = mini_app_supplier_offer_url(mini_app_url=mini_base, offer_id=offer_id)
        else:
            rezerva_href = None
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

        if lc is SupplierOfferLifecycle.APPROVED and not exact_ok:
            warnings.extend(exact_reasons)

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
            lc == SupplierOfferLifecycle.APPROVED and channel_ok and token_ok and exact_ok
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

    def showcase_channel_payload_preview(
        self,
        session: Session,
        *,
        offer_id: int,
        settings: Settings | None = None,
    ) -> AdminSupplierOfferShowcaseChannelPayloadRead:
        """B13D-alt: ``ShowcaseChannelPublishRequest`` shape for Telegram channel; **does not** call Telegram."""
        row = self._row(session, offer_id=offer_id)
        cfg = settings or get_settings()
        pub, _, _, _ = self._showcase_publication_and_rezerva_tour_code(
            session,
            offer_id=offer_id,
            row=row,
            cfg=cfg,
        )
        req = telegram_showcase_channel_publish_request_preview(offer_id, pub, settings=cfg)
        photo = (pub.photo_url or "").strip()
        is_photo = bool(photo)
        disable_preview = not is_photo
        return AdminSupplierOfferShowcaseChannelPayloadRead(
            supplier_offer_id=offer_id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            channel_ref=req.channel_ref,
            publication=AdminShowcasePublicationPayloadRead(
                caption_html=req.publication.caption_html,
                photo_url=req.publication.photo_url,
            ),
            idempotency_key=req.idempotency_key,
            disable_web_page_preview=disable_preview,
        )

    def publish(
        self,
        session: Session,
        *,
        offer_id: int,
        settings: Settings | None = None,
        actor_surface: SupplierOfferShowcasePublishActorSurface | None = None,
        requested_by: str | None = None,
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
        exact_ok, gate_reasons = channel_publish_exact_tour_ready(session, offer_id=offer_id)
        if not exact_ok:
            raise SupplierOfferModerationStateError("; ".join(gate_reasons[:5]))
        tc = tour_code_for_active_execution_link(session, offer_id=offer_id)
        if not tc:
            raise SupplierOfferModerationStateError(
                "Active execution link must provide tour_code for channel Rezervă URL.",
            )
        pub = build_showcase_publication(
            row,
            cfg,
            rezerva_tour_code=tc,
            channel_rezerva_requires_exact_tour=False,
        )
        surface = actor_surface or SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN
        attempt = self._showcase_publish_attempts.create_requested_attempt(
            session,
            supplier_offer_id=offer_id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=surface,
            channel_ref=channel_id,
            requested_by=requested_by,
            payload_fingerprint=_showcase_publish_payload_fingerprint(pub),
        )
        if pub.photo_url is not None:
            cover_ref = (row.cover_media_reference or "").strip()
            if not is_raw_cover_reference_sendable_for_telegram_sendphoto(cover_ref):
                raise SupplierOfferModerationStateError(
                    "Cannot publish: showcase photo would not be sendable to Telegram sendPhoto "
                    "(replace cover_media_reference, POST …/media/clear-cover-for-text-only, or fix media review).",
                )
            if showcase_photo_send_argument_from_offer(row) != pub.photo_url:
                raise SupplierOfferModerationStateError(
                    "Cannot publish: showcase publication photo is inconsistent with offer cover state.",
                )
        adapter = TelegramShowcaseChannelAdapter(settings=cfg)
        try:
            result = adapter.publish(
                ShowcaseChannelPublishRequest(
                    offer_id=offer_id,
                    publication=pub,
                    channel_ref=channel_id,
                ),
            )
        except TelegramShowcaseSendError as exc:
            self._showcase_publish_attempts.mark_failed(
                session,
                attempt_id=attempt.id,
                error_code="telegram_showcase_send",
                error_message=str(exc)[:4096],
                retryable_failure=None,
            )
            raise SupplierOfferModerationStateError(f"Telegram publish failed: {exc}") from exc
        message_id = int(result.message_id) if result.message_id is not None else None
        if message_id is None:
            self._showcase_publish_attempts.mark_failed(
                session,
                attempt_id=attempt.id,
                error_code="missing_message_id",
                error_message="Telegram adapter returned no message_id.",
                retryable_failure=False,
            )
            raise SupplierOfferModerationStateError("Telegram publish returned no message_id.")

        self._showcase_publish_attempts.mark_provider_sent(session, attempt_id=attempt.id)
        row.lifecycle_status = SupplierOfferLifecycle.PUBLISHED
        row.published_at = datetime.now(UTC)
        row.showcase_chat_id = channel_id
        row.showcase_message_id = message_id
        session.add(row)
        session.flush()
        self._showcase_publish_attempts.mark_persisted(
            session,
            attempt_id=attempt.id,
            showcase_chat_id=channel_id,
            showcase_message_id=message_id,
        )
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
