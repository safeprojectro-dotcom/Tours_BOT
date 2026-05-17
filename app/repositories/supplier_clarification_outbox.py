"""A4: persistence for supplier clarification outbox rows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.supplier_clarification_outbox import (
    CLARIFICATION_OUTBOX_ACTIVE_STATUSES,
    SupplierClarificationOutboxItem,
)


class SupplierClarificationOutboxRepository:
    def get_by_id(self, session: Session, *, item_id: int) -> SupplierClarificationOutboxItem | None:
        return session.get(SupplierClarificationOutboxItem, item_id)

    def list_for_supplier_offer(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SupplierClarificationOutboxItem]:
        stmt = (
            select(SupplierClarificationOutboxItem)
            .where(SupplierClarificationOutboxItem.supplier_offer_id == supplier_offer_id)
            .order_by(desc(SupplierClarificationOutboxItem.id))
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def find_latest_active_for_supplier_offer(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
    ) -> SupplierClarificationOutboxItem | None:
        stmt = (
            select(SupplierClarificationOutboxItem)
            .where(
                SupplierClarificationOutboxItem.supplier_offer_id == supplier_offer_id,
                SupplierClarificationOutboxItem.workflow_status.in_(CLARIFICATION_OUTBOX_ACTIVE_STATUSES),
            )
            .order_by(desc(SupplierClarificationOutboxItem.id))
            .limit(1)
        )
        return session.scalars(stmt).first()

    def add(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        draft_snapshot: dict,
        workflow_status: str = "draft",
        created_by_telegram_user_id: int | None = None,
    ) -> SupplierClarificationOutboxItem:
        row = SupplierClarificationOutboxItem(
            supplier_offer_id=supplier_offer_id,
            workflow_status=workflow_status,
            draft_snapshot=draft_snapshot,
            created_by_telegram_user_id=created_by_telegram_user_id,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row

    def apply_workflow_update(
        self,
        session: Session,
        *,
        item_id: int,
        workflow_status: str,
        review_note: str | None,
        update_review_note: bool,
        last_reviewed_at: datetime,
        last_reviewed_by_telegram_user_id: int | None,
    ) -> SupplierClarificationOutboxItem | None:
        row = self.get_by_id(session, item_id=item_id)
        if row is None:
            return None
        row.workflow_status = workflow_status
        if update_review_note:
            row.review_note = review_note
        row.last_reviewed_at = last_reviewed_at
        row.last_reviewed_by_telegram_user_id = last_reviewed_by_telegram_user_id
        session.flush()
        session.refresh(row)
        return row


outbox_repository = SupplierClarificationOutboxRepository()
