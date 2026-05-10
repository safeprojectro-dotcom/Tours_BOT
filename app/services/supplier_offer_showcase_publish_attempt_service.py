"""Showcase publish attempt audit rows (B13D/B13E)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferShowcasePublishActorSurface, SupplierOfferShowcasePublishAttemptStatus
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt
from app.repositories.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttemptRepository
from app.schemas.supplier_admin import (
    AdminSupplierOfferShowcasePublishAttemptRead,
    AdminSupplierOfferShowcasePublishAttemptsReviewRead,
)


class SupplierOfferShowcasePublishAttemptService:
    """Persist attempt lifecycle for showcase channel publish (B13E: wired from ``ModerationService.publish``)."""

    def __init__(self, repository: SupplierOfferShowcasePublishAttemptRepository | None = None) -> None:
        self._repo = repository or SupplierOfferShowcasePublishAttemptRepository()

    def create_requested_attempt(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        provider: str,
        actor_surface: SupplierOfferShowcasePublishActorSurface,
        channel_ref: str | None = None,
        requested_by: str | None = None,
        idempotency_key: str | None = None,
        payload_fingerprint: str | None = None,
    ) -> SupplierOfferShowcasePublishAttempt:
        return self._repo.create(
            session,
            supplier_offer_id=supplier_offer_id,
            provider=provider,
            actor_surface=actor_surface,
            channel_ref=channel_ref,
            requested_by=requested_by,
            idempotency_key=idempotency_key,
            payload_fingerprint=payload_fingerprint,
            status=SupplierOfferShowcasePublishAttemptStatus.REQUESTED,
        )

    def mark_provider_sent(
        self,
        session: Session,
        *,
        attempt_id: int,
    ) -> SupplierOfferShowcasePublishAttempt | None:
        row = self._repo.get_by_id(session, attempt_id)
        if row is None:
            return None
        return self._repo.update(
            session,
            instance=row,
            data={"status": SupplierOfferShowcasePublishAttemptStatus.PROVIDER_SENT},
        )

    def mark_persisted(
        self,
        session: Session,
        *,
        attempt_id: int,
        showcase_chat_id: str,
        showcase_message_id: int,
    ) -> SupplierOfferShowcasePublishAttempt | None:
        row = self._repo.get_by_id(session, attempt_id)
        if row is None:
            return None
        return self._repo.update(
            session,
            instance=row,
            data={
                "status": SupplierOfferShowcasePublishAttemptStatus.PERSISTED,
                "showcase_chat_id": showcase_chat_id,
                "showcase_message_id": showcase_message_id,
                "error_code": None,
                "error_message": None,
                "retryable_failure": None,
            },
        )

    def mark_failed(
        self,
        session: Session,
        *,
        attempt_id: int,
        error_code: str | None = None,
        error_message: str | None = None,
        retryable_failure: bool | None = None,
    ) -> SupplierOfferShowcasePublishAttempt | None:
        row = self._repo.get_by_id(session, attempt_id)
        if row is None:
            return None
        return self._repo.update(
            session,
            instance=row,
            data={
                "status": SupplierOfferShowcasePublishAttemptStatus.FAILED,
                "error_code": error_code,
                "error_message": error_message,
                "retryable_failure": retryable_failure,
            },
        )

    def list_attempts_review_read(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        limit: int = 50,
    ) -> AdminSupplierOfferShowcasePublishAttemptsReviewRead:
        """B13F: newest-first audit rows for admin review-package / Telegram ops (read-only)."""
        rows = self._repo.list_for_offer(session, supplier_offer_id=supplier_offer_id, limit=limit)
        items = [
            AdminSupplierOfferShowcasePublishAttemptRead(
                id=r.id,
                supplier_offer_id=r.supplier_offer_id,
                provider=r.provider,
                channel_ref=r.channel_ref,
                status=r.status.value,
                actor_surface=r.actor_surface.value,
                requested_by=r.requested_by,
                idempotency_key=r.idempotency_key,
                payload_fingerprint=r.payload_fingerprint,
                showcase_chat_id=r.showcase_chat_id,
                showcase_message_id=r.showcase_message_id,
                error_code=r.error_code,
                error_message=r.error_message,
                retryable_failure=r.retryable_failure,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rows
        ]
        return AdminSupplierOfferShowcasePublishAttemptsReviewRead(
            total_returned=len(items),
            items=items,
        )
