"""B7.1: admin visual decisions on cover media (metadata in packaging_draft_json only). No getFile, no download, no publish."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferMediaReviewStatus
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead
from app.services.supplier_offer_publish_safe_stub import merge_publish_safe_into_draft
from app.services.supplier_offer_showcase_cover_sendability import (
    is_raw_cover_reference_sendable_for_telegram_sendphoto,
)

MEDIA_REVIEW_KEY = "media_review"
B7_1_VERSION = "b7_1"

# C2B6: Telegram admin “request photo” uses this fixed audit string (Admin API otherwise requires free-text reason).
DEFAULT_TELEGRAM_PREVIEW_COVER_REPLACEMENT_REASON = (
    "Marked from Telegram admin preview: cover photo needs replacement."
)


class SupplierOfferMediaReviewNotFoundError(Exception):
    pass


class SupplierOfferMediaReviewStateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _as_draft_dict(row: SupplierOffer) -> dict:
    p = row.packaging_draft_json
    if isinstance(p, dict):
        return dict(p)
    return {}


def media_review_status_value(row: SupplierOffer) -> str | None:
    """Return ``packaging_draft_json.media_review.status`` when present (B7.1 / C2B6)."""

    mr = _as_draft_dict(row).get(MEDIA_REVIEW_KEY)
    if not isinstance(mr, dict):
        return None
    st = (mr.get("status") or "").strip()
    return st or None


def _set_media_review(
    row: SupplierOffer,
    *,
    status: SupplierOfferMediaReviewStatus,
    cover_snapshot: str | None,
    reason: str | None,
    reviewed_by: str | None,
) -> None:
    d = _as_draft_dict(row)
    now = datetime.now(UTC)
    d[MEDIA_REVIEW_KEY] = {
        "version": B7_1_VERSION,
        "cover_media_reference": (cover_snapshot or None),
        "status": status.value,
        "reason": reason,
        "reviewed_at": now.isoformat(),
        "reviewed_by": reviewed_by,
    }
    d = merge_publish_safe_into_draft(row, d, marked_by=reviewed_by, now=now)
    row.packaging_draft_json = d


def _current_cover_ref(row: SupplierOffer) -> str | None:
    r = (row.cover_media_reference or "").strip()
    return r or None


class SupplierOfferMediaReviewService:
    def __init__(self) -> None:
        self._repo = SupplierOfferRepository()

    def get_read(self, session: Session, *, offer_id: int) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferMediaReviewNotFoundError
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def approve_for_card(
        self, session: Session, *, offer_id: int, reviewed_by: str | None
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferMediaReviewNotFoundError
        cover = _current_cover_ref(row)
        if not cover:
            raise SupplierOfferMediaReviewStateError("Cannot approve: cover_media_reference is empty.")
        if not is_raw_cover_reference_sendable_for_telegram_sendphoto(cover):
            raise SupplierOfferMediaReviewStateError(
                "Cannot approve: cover_media_reference is not sendable as a Telegram photo "
                "(use telegram_photo:{file_id} or a direct image URL; not share/page links such as Google share).",
            )
        _set_media_review(
            row,
            status=SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD,
            cover_snapshot=cover,
            reason=None,
            reviewed_by=reviewed_by,
        )
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def reject(
        self,
        session: Session,
        *,
        offer_id: int,
        status: SupplierOfferMediaReviewStatus,
        reason: str,
        reviewed_by: str | None,
    ) -> AdminSupplierOfferRead:
        if status not in (
            SupplierOfferMediaReviewStatus.REJECTED_BAD_QUALITY,
            SupplierOfferMediaReviewStatus.REJECTED_IRRELEVANT,
        ):
            raise SupplierOfferMediaReviewStateError("Invalid rejection status for this action.")
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferMediaReviewNotFoundError
        cover = _current_cover_ref(row)
        _set_media_review(
            row,
            status=status,
            cover_snapshot=cover,
            reason=reason,
            reviewed_by=reviewed_by,
        )
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def request_replacement(
        self, session: Session, *, offer_id: int, reason: str, reviewed_by: str | None
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferMediaReviewNotFoundError
        cover = _current_cover_ref(row)
        _set_media_review(
            row,
            status=SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED,
            cover_snapshot=cover,
            reason=reason,
            reviewed_by=reviewed_by,
        )
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def clear_cover_for_channel_text_only_publish(
        self,
        session: Session,
        *,
        offer_id: int,
        reviewed_by: str | None,
        reason: str | None = None,
    ) -> AdminSupplierOfferRead:
        """B15C4: remove showcase hero from the offer row and record audit state for text-only channel publish."""

        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferMediaReviewNotFoundError
        cover = _current_cover_ref(row)
        if not cover:
            raise SupplierOfferMediaReviewStateError(
                "cover_media_reference is already empty; nothing to clear for text-only publish.",
            )
        row.cover_media_reference = None
        _set_media_review(
            row,
            status=SupplierOfferMediaReviewStatus.COVER_CLEARED_FOR_CHANNEL_TEXT_ONLY,
            cover_snapshot=cover,
            reason=reason or "Admin cleared showcase cover for text-only channel publish.",
            reviewed_by=reviewed_by,
        )
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)

    def use_fallback_card(
        self,
        session: Session,
        *,
        offer_id: int,
        reason: str | None,
        reviewed_by: str | None,
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferMediaReviewNotFoundError
        cover = _current_cover_ref(row)
        _set_media_review(
            row,
            status=SupplierOfferMediaReviewStatus.FALLBACK_CARD_REQUIRED,
            cover_snapshot=cover,
            reason=reason,
            reviewed_by=reviewed_by,
        )
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)
