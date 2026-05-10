"""B13D: repository for showcase publish attempt audit rows."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferShowcasePublishActorSurface, SupplierOfferShowcasePublishAttemptStatus
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt


class SupplierOfferShowcasePublishAttemptRepository:
    def get_by_id(self, session: Session, attempt_id: int) -> SupplierOfferShowcasePublishAttempt | None:
        return session.get(SupplierOfferShowcasePublishAttempt, attempt_id)

    def list_for_offer(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        limit: int = 50,
    ) -> list[SupplierOfferShowcasePublishAttempt]:
        stmt = (
            select(SupplierOfferShowcasePublishAttempt)
            .where(SupplierOfferShowcasePublishAttempt.supplier_offer_id == supplier_offer_id)
            .order_by(SupplierOfferShowcasePublishAttempt.id.desc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def create(
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
        status: SupplierOfferShowcasePublishAttemptStatus = SupplierOfferShowcasePublishAttemptStatus.REQUESTED,
    ) -> SupplierOfferShowcasePublishAttempt:
        row = SupplierOfferShowcasePublishAttempt(
            supplier_offer_id=supplier_offer_id,
            provider=provider,
            channel_ref=channel_ref,
            actor_surface=actor_surface,
            requested_by=requested_by,
            idempotency_key=idempotency_key,
            payload_fingerprint=payload_fingerprint,
            status=status,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row

    def update(
        self,
        session: Session,
        *,
        instance: SupplierOfferShowcasePublishAttempt,
        data: dict[str, object],
    ) -> SupplierOfferShowcasePublishAttempt:
        for key, value in data.items():
            setattr(instance, key, value)
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance
