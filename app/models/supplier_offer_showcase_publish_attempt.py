"""B13D: audit rows for showcase channel publish attempts (persistence foundation; live publish unwired)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    SupplierOfferShowcasePublishActorSurface,
    SupplierOfferShowcasePublishAttemptStatus,
    sqlalchemy_enum,
)
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.supplier import SupplierOffer


class SupplierOfferShowcasePublishAttempt(TimestampMixin, Base):
    """One logical attempt to publish an offer to a showcase channel (e.g. Telegram).

    Retention: FK to ``supplier_offers`` uses ``ON DELETE RESTRICT`` — deleting an offer
    that still has attempt rows fails at the DB unless attempts are removed or archived first
    (audit history is not silently cascade-deleted).
    """

    __tablename__ = "supplier_offer_showcase_publish_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_offer_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_offers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    channel_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[SupplierOfferShowcasePublishAttemptStatus] = mapped_column(
        sqlalchemy_enum(
            SupplierOfferShowcasePublishAttemptStatus,
            name="supplier_offer_showcase_publish_attempt_status",
        ),
        nullable=False,
        default=SupplierOfferShowcasePublishAttemptStatus.REQUESTED,
    )
    actor_surface: Mapped[SupplierOfferShowcasePublishActorSurface] = mapped_column(
        sqlalchemy_enum(
            SupplierOfferShowcasePublishActorSurface,
            name="supplier_offer_showcase_publish_actor_surface",
        ),
        nullable=False,
    )
    requested_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payload_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    showcase_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    showcase_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retryable_failure: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    supplier_offer: Mapped["SupplierOffer"] = relationship(
        "SupplierOffer",
        back_populates="showcase_publish_attempts",
    )
