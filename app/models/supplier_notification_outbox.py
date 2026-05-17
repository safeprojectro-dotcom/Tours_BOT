"""S1C-1 / S1C-2: persisted supplier Telegram notification intents plus delivery audit columns."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class SupplierNotificationOutbox(TimestampMixin, Base):
    """Governed supplier-facing notification queue — distinct from customer ``notification_outbox``."""

    __tablename__ = "supplier_notification_outbox"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_supplier_notification_outbox_idempotency_key"),
        CheckConstraint(
            "event_type IN ('supplier_offer_published', 'supplier_order_created')",
            name="ck_supplier_notification_outbox_event_type",
        ),
        CheckConstraint(
            "contact_resolution_status IN ("
            "'resolved_with_contact', 'resolved_missing_contact', 'missing_relationship', "
            "'ambiguous_suppliers'"
            ")",
            name="ck_supplier_notification_outbox_contact_resolution_status",
        ),
        CheckConstraint(
            "dispatch_status IN ("
            "'pending_dispatch', 'skipped_no_target', 'delivery_in_progress', "
            "'delivered', 'send_failed'"
            ")",
            name="ck_supplier_notification_outbox_dispatch_status",
        ),
        CheckConstraint("char_length(btrim(idempotency_key)) > 0", name="ck_supplier_notification_outbox_idem_nonempty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="telegram_dm")

    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    supplier_offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("supplier_offers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tour_id: Mapped[int | None] = mapped_column(ForeignKey("tours.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    contact_resolution_status: Mapped[str] = mapped_column(String(64), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    readiness_warnings: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)

    dispatch_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_dispatch")
    telegram_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_delivery_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actor_surface: Mapped[str | None] = mapped_column(String(64), nullable=True)
