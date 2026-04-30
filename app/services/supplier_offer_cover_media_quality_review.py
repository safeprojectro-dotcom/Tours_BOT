"""C2B5: deterministic read-only cover/showcase media hints for admin review-package (no mutations, no AI).

Uses ``offer.cover_media_reference`` as the sole showcase photo source (same as ``build_showcase_publication``)
and ``packaging_draft_json.media_review`` when present (B7.1).
"""

from __future__ import annotations

from app.models.enums import SupplierOfferMediaReviewStatus
from app.models.supplier import SupplierOffer
from app.schemas.supplier_admin import (
    AdminSupplierOfferCoverMediaQualityReviewRead,
    CoverMediaWarningItemRead,
)
from app.services.supplier_offer_media_review_service import MEDIA_REVIEW_KEY
from app.services.supplier_offer_showcase_message import showcase_photo_send_argument_from_offer


def _norm_ref(value: str | None) -> str | None:
    s = (value or "").strip()
    return s or None


def _media_review_dict(row: SupplierOffer) -> dict | None:
    p = row.packaging_draft_json
    if not isinstance(p, dict):
        return None
    mr = p.get(MEDIA_REVIEW_KEY)
    return mr if isinstance(mr, dict) else None


_NEGATIVE_MEDIA_REVIEW: frozenset[str] = frozenset(
    {
        SupplierOfferMediaReviewStatus.REJECTED_BAD_QUALITY.value,
        SupplierOfferMediaReviewStatus.REJECTED_IRRELEVANT.value,
        SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED.value,
        SupplierOfferMediaReviewStatus.FALLBACK_CARD_REQUIRED.value,
    }
)

_NEGATIVE_MESSAGES: dict[str, tuple[str, str]] = {
    SupplierOfferMediaReviewStatus.REJECTED_BAD_QUALITY.value: (
        "media_review_rejected_bad_quality",
        "B7.1 media_review marks this cover as rejected (bad quality). Replace cover_media_reference "
        "or update media review before trusting showcase photo.",
    ),
    SupplierOfferMediaReviewStatus.REJECTED_IRRELEVANT.value: (
        "media_review_rejected_irrelevant",
        "B7.1 media_review marks this cover as rejected (irrelevant). Replace cover_media_reference "
        "or update media review before trusting showcase photo.",
    ),
    SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED.value: (
        "media_review_replacement_requested",
        "B7.1 media_review requested supplier replacement for cover media — resolve before trusting showcase photo.",
    ),
    SupplierOfferMediaReviewStatus.FALLBACK_CARD_REQUIRED.value: (
        "media_review_fallback_card_required",
        "B7.1 media_review requires a fallback card treatment — verify cover intent before channel publish.",
    ),
}


def evaluate_cover_media_quality_review(row: SupplierOffer) -> AdminSupplierOfferCoverMediaQualityReviewRead:
    """Return deterministic warnings only; semantic image correctness stays a human Preview decision."""
    seen: set[str] = set()
    items: list[CoverMediaWarningItemRead] = []

    def add(code: str, message: str) -> None:
        if code in seen:
            return
        seen.add(code)
        items.append(CoverMediaWarningItemRead(code=code, message=message))

    cur_cover = _norm_ref(row.cover_media_reference)
    showcase_col = _norm_ref(row.showcase_photo_url)

    if showcase_col and not cur_cover:
        add(
            "showcase_photo_url_without_cover_media_reference",
            "showcase_photo_url is set but cover_media_reference is empty — Telegram showcase uses "
            "cover_media_reference only; align data if you expect a hero photo.",
        )
    elif showcase_col and cur_cover and showcase_col != cur_cover:
        add(
            "showcase_photo_url_differs_from_cover_media_reference",
            "showcase_photo_url differs from cover_media_reference — showcase preview/publish uses "
            "cover_media_reference only.",
        )

    mr = _media_review_dict(row)
    mr_status = ((mr.get("status") or "").strip()) if mr else ""

    if mr_status in _NEGATIVE_MESSAGES:
        code, msg = _NEGATIVE_MESSAGES[mr_status]
        add(code, msg)

    snap = _norm_ref(mr.get("cover_media_reference")) if mr else None
    has_drift = bool(snap and cur_cover and snap != cur_cover)
    if has_drift:
        add(
            "media_review_cover_snapshot_mismatch",
            "packaging_draft_json.media_review snapshot differs from current cover_media_reference — "
            "after visual check, POST .../media/approve-for-card (or clear/replace review) so records match.",
        )

    usable_photo = showcase_photo_send_argument_from_offer(row) is not None

    if not usable_photo:
        if not cur_cover:
            add(
                "cover_media_missing_showcase_photo",
                "No cover_media_reference — showcase preview/publish runs text-only (no hero photo).",
            )
        else:
            add(
                "cover_media_not_sendable_for_showcase",
                "cover_media_reference is set but is not sendable as Telegram photo "
                "(use telegram_photo:{file_id} or https URL) — showcase preview/publish will be text-only.",
            )

    if usable_photo and mr_status not in _NEGATIVE_MEDIA_REVIEW:
        aligned_approved = (
            mr_status == SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value
            and snap
            and cur_cover
            and snap == cur_cover
        )
        if not aligned_approved and not has_drift:
            add(
                "cover_media_not_explicitly_approved_for_card",
                "Showcase can send a photo from cover_media_reference, but B7.1 media_review is not "
                "approved_for_card for this reference — open Preview, then POST .../media/approve-for-card "
                "if the image matches the offer.",
            )
    return AdminSupplierOfferCoverMediaQualityReviewRead(
        warnings=items,
        has_warnings=bool(items),
    )
