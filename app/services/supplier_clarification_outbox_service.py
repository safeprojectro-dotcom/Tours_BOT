"""A4: business rules for supplier clarification outbox (persistence only; no supplier I/O)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories.supplier import SupplierOfferRepository
from app.repositories.supplier_clarification_outbox import SupplierClarificationOutboxRepository
from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead
from app.schemas.supplier_clarification_outbox import SupplierClarificationOutboxItemRead

_offer_repo = SupplierOfferRepository()
_outbox_repo = SupplierClarificationOutboxRepository()


class SupplierClarificationOutboxOfferNotFoundError(Exception):
    pass


class SupplierClarificationOutboxItemNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class SupplierClarificationOutboxUpsertResult:
    item: SupplierClarificationOutboxItemRead
    replayed_existing: bool


class SupplierClarificationOutboxService:
    @staticmethod
    def to_read(row) -> SupplierClarificationOutboxItemRead:
        return SupplierClarificationOutboxItemRead(
            id=row.id,
            supplier_offer_id=row.supplier_offer_id,
            workflow_status=row.workflow_status,
            draft_snapshot=dict(row.draft_snapshot),
            created_by_telegram_user_id=row.created_by_telegram_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def upsert_from_draft(
        self,
        session: Session,
        *,
        draft: SupplierClarificationDraftRead,
        created_by_telegram_user_id: int | None = None,
    ) -> SupplierClarificationOutboxUpsertResult:
        """Create a new draft row, or return the latest active one for the same offer (no duplicate draft/review)."""
        offer = _offer_repo.get_any(session, offer_id=draft.supplier_offer_id)
        if offer is None:
            raise SupplierClarificationOutboxOfferNotFoundError()
        existing = _outbox_repo.find_latest_active_for_supplier_offer(
            session,
            supplier_offer_id=draft.supplier_offer_id,
        )
        if existing is not None:
            return SupplierClarificationOutboxUpsertResult(
                item=self.to_read(existing),
                replayed_existing=True,
            )
        snapshot = draft.model_dump(mode="json")
        row = _outbox_repo.add(
            session,
            supplier_offer_id=draft.supplier_offer_id,
            draft_snapshot=snapshot,
            workflow_status="draft",
            created_by_telegram_user_id=created_by_telegram_user_id,
        )
        return SupplierClarificationOutboxUpsertResult(
            item=self.to_read(row),
            replayed_existing=False,
        )

    def list_for_supplier_offer(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        limit: int = 50,
    ) -> list[SupplierClarificationOutboxItemRead]:
        rows = _outbox_repo.list_for_supplier_offer(
            session,
            supplier_offer_id=supplier_offer_id,
            limit=limit,
        )
        return [self.to_read(r) for r in rows]

    def get_by_id(self, session: Session, *, item_id: int) -> SupplierClarificationOutboxItemRead:
        row = _outbox_repo.get_by_id(session, item_id=item_id)
        if row is None:
            raise SupplierClarificationOutboxItemNotFoundError()
        return self.to_read(row)


__all__ = [
    "SupplierClarificationOutboxItemNotFoundError",
    "SupplierClarificationOutboxOfferNotFoundError",
    "SupplierClarificationOutboxService",
    "SupplierClarificationOutboxUpsertResult",
]
