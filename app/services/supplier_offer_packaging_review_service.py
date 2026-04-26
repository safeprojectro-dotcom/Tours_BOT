"""B5: admin packaging review (approve/reject/clarify/draft edit). No publish, no Tour, no Telegram send, no lifecycle change."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferPackagingStatus
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead


class SupplierOfferPackagingReviewNotFoundError(Exception):
    pass


class SupplierOfferPackagingReviewStateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOfferPackagingReviewService:
    def __init__(self) -> None:
        self._repo = SupplierOfferRepository()

    def get_review(self, session: Session, *, offer_id: int) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferPackagingReviewNotFoundError
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def approve(
        self,
        session: Session,
        *,
        offer_id: int,
        accept_warnings: bool,
        reviewed_by: str | None,
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferPackagingReviewNotFoundError
        st = row.packaging_status
        if st == SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
            raise SupplierOfferPackagingReviewStateError("Packaging is already approved for publish.")
        if st not in (
            SupplierOfferPackagingStatus.PACKAGING_GENERATED,
            SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW,
        ):
            raise SupplierOfferPackagingReviewStateError(
                f"Cannot approve packaging from status {st.value}. Generate or refresh packaging first."
            )
        if st == SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW and not accept_warnings:
            raise SupplierOfferPackagingReviewStateError(
                "accept_warnings=true is required when packaging_status is needs_admin_review."
            )
        now = datetime.now(UTC)
        row.packaging_status = SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH
        row.packaging_reviewed_at = now
        row.packaging_reviewed_by = reviewed_by
        row.packaging_rejection_reason = None
        row.clarification_reason = None
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def reject(
        self,
        session: Session,
        *,
        offer_id: int,
        reason: str,
        reviewed_by: str | None,
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferPackagingReviewNotFoundError
        now = datetime.now(UTC)
        row.packaging_status = SupplierOfferPackagingStatus.PACKAGING_REJECTED
        row.packaging_rejection_reason = reason
        row.clarification_reason = None
        row.packaging_reviewed_at = now
        row.packaging_reviewed_by = reviewed_by
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def request_clarification(
        self,
        session: Session,
        *,
        offer_id: int,
        reason: str,
        reviewed_by: str | None,
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferPackagingReviewNotFoundError
        now = datetime.now(UTC)
        row.packaging_status = SupplierOfferPackagingStatus.CLARIFICATION_REQUESTED
        row.clarification_reason = reason
        row.packaging_rejection_reason = None
        row.packaging_reviewed_at = now
        row.packaging_reviewed_by = reviewed_by
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def patch_telegram_draft(
        self,
        session: Session,
        *,
        offer_id: int,
        telegram_post_draft: str,
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferPackagingReviewNotFoundError
        if row.packaging_status == SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
            raise SupplierOfferPackagingReviewStateError("Cannot edit draft after packaging is approved for publish.")
        if row.packaging_draft_json is None or not isinstance(row.packaging_draft_json, dict):
            row.packaging_draft_json = {}
        else:
            row.packaging_draft_json = dict(row.packaging_draft_json)
        row.packaging_draft_json["telegram_post_draft"] = telegram_post_draft
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)
