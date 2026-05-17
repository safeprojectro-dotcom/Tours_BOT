"""A4: durable internal outbox for supplier clarification drafts (no supplier send)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin

# Active items: at most one logical "current" draft per supplier_offer for save/replay (see outbox service).
CLARIFICATION_OUTBOX_ACTIVE_STATUSES: frozenset[str] = frozenset({"draft", "ready_for_review"})


class SupplierClarificationOutboxItem(TimestampMixin, Base):
    """Persisted snapshot of a clarification draft + admin workflow status only."""

    __tablename__ = "supplier_clarification_outbox_items"
    __table_args__ = (
        CheckConstraint(
            "workflow_status IN ('draft', 'ready_for_review', 'cancelled', 'sent_externally_later')",
            name="ck_supplier_clarification_outbox_items_workflow_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_offer_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    draft_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_reviewed_by_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
