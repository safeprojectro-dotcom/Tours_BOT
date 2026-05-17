"""A4/A5: business rules for supplier clarification outbox (persistence only; no supplier I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.supplier import SupplierOfferRepository
from app.repositories.supplier_clarification_outbox import SupplierClarificationOutboxRepository
from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead
from app.schemas.supplier_clarification_outbox import (
    CLARIFICATION_OUTBOX_WORKFLOW_STATUSES,
    SupplierClarificationOutboxItemRead,
    SupplierClarificationOutboxStatusPatchRequest,
)

_offer_repo = SupplierOfferRepository()
_outbox_repo = SupplierClarificationOutboxRepository()

# current_status -> allowed target statuses
_OUTBOX_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"ready_for_review", "cancelled"}),
    "ready_for_review": frozenset({"cancelled", "sent_externally_later"}),
}


class SupplierClarificationOutboxOfferNotFoundError(Exception):
    pass


class SupplierClarificationOutboxItemNotFoundError(Exception):
    pass


class SupplierClarificationOutboxInvalidTransitionError(Exception):
    def __init__(self, *, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


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
            last_reviewed_at=getattr(row, "last_reviewed_at", None),
            last_reviewed_by_telegram_user_id=getattr(row, "last_reviewed_by_telegram_user_id", None),
            review_note=getattr(row, "review_note", None),
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

    def apply_status_patch(
        self,
        session: Session,
        *,
        item_id: int,
        body: SupplierClarificationOutboxStatusPatchRequest,
        reviewed_by_telegram_user_id: int | None = None,
    ) -> SupplierClarificationOutboxItemRead:
        """Validated workflow transition + optional review note (A5)."""
        row = _outbox_repo.get_by_id(session, item_id=item_id)
        if row is None:
            raise SupplierClarificationOutboxItemNotFoundError()
        target = body.workflow_status.strip()
        if target not in CLARIFICATION_OUTBOX_WORKFLOW_STATUSES:
            raise SupplierClarificationOutboxInvalidTransitionError(
                detail="Unknown workflow_status value.",
            )
        allowed = _OUTBOX_TRANSITIONS.get(row.workflow_status, frozenset())
        if target not in allowed:
            raise SupplierClarificationOutboxInvalidTransitionError(
                detail=f"Cannot transition from {row.workflow_status!r} to {target!r}.",
            )
        update_note = "review_note" in body.model_fields_set
        note_val: str | None = body.review_note
        if note_val is not None:
            note_val = note_val.strip() or None

        reviewer = (
            reviewed_by_telegram_user_id
            if reviewed_by_telegram_user_id is not None
            else body.reviewed_by_telegram_user_id
        )

        now = datetime.now(UTC)
        updated = _outbox_repo.apply_workflow_update(
            session,
            item_id=item_id,
            workflow_status=target,
            review_note=note_val,
            update_review_note=update_note,
            last_reviewed_at=now,
            last_reviewed_by_telegram_user_id=reviewer,
        )
        assert updated is not None
        return self.to_read(updated)

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
    "SupplierClarificationOutboxInvalidTransitionError",
    "SupplierClarificationOutboxItemNotFoundError",
    "SupplierClarificationOutboxOfferNotFoundError",
    "SupplierClarificationOutboxService",
    "SupplierClarificationOutboxUpsertResult",
]
