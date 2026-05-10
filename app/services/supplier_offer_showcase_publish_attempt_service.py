"""B13D: service skeleton for showcase publish attempts (persistence only — not called from live publish)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferShowcasePublishActorSurface, SupplierOfferShowcasePublishAttemptStatus
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt
from app.repositories.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttemptRepository


class SupplierOfferShowcasePublishAttemptService:
    """Create and transition attempt rows for future orchestration; no Telegram I/O here."""

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
