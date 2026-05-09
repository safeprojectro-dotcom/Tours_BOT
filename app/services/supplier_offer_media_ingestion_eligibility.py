"""B7.4C: pure ingestion eligibility vs ``docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`` §4 (no I/O)."""

from __future__ import annotations

from dataclasses import dataclass

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.core.media_storage_types import MediaSourceKind
from app.models.enums import SupplierOfferMediaReviewStatus
from app.services.supplier_offer_media_review_service import MEDIA_REVIEW_KEY


def classify_cover_media_reference(ref: str | None) -> MediaSourceKind:
    """Classify a trimmed cover/source reference (B7.4B §3)."""

    s = (ref or "").strip()
    if not s:
        return MediaSourceKind.EMPTY
    if s.startswith(SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX):
        rest = s.removeprefix(SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX).strip()
        if not rest:
            return MediaSourceKind.UNSUPPORTED
        return MediaSourceKind.TELEGRAM_PHOTO
    low = s.lower()
    if low.startswith("https://"):
        return MediaSourceKind.HTTPS_URL
    if low.startswith("http://"):
        return MediaSourceKind.HTTP_URL
    return MediaSourceKind.UNSUPPORTED


@dataclass(frozen=True, slots=True)
class MediaIngestionEligibilityResult:
    allowed: bool
    """Stable machine codes for tests and future logging."""
    block_codes: tuple[str, ...]


def _norm(s: str | None) -> str | None:
    v = (s or "").strip()
    return v or None


def evaluate_media_ingestion_eligibility(
    *,
    cover_media_reference: str | None,
    packaging_draft_json: dict | list | None,
    allow_https_source: bool = False,
) -> MediaIngestionEligibilityResult:
    """Return whether durable ingestion is allowed for the current offer JSON state.

    ``allow_https_source`` implements B7.4B HTTPS policy (off until ops enables it via settings).
    """

    blocks: list[str] = []
    cur = _norm(cover_media_reference)
    if not cur:
        blocks.append("ingestion_no_cover_reference")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))

    draft = packaging_draft_json if isinstance(packaging_draft_json, dict) else {}
    mr = draft.get(MEDIA_REVIEW_KEY)
    if not isinstance(mr, dict):
        blocks.append("ingestion_media_review_missing")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))

    status_raw = _norm(mr.get("status"))
    if status_raw != SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value:
        blocks.append("ingestion_not_approved_for_card")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))

    snap = _norm(mr.get("cover_media_reference"))
    if not snap:
        blocks.append("ingestion_review_snapshot_missing")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))
    if snap != cur:
        blocks.append("ingestion_cover_snapshot_mismatch")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))

    kind = classify_cover_media_reference(cur)
    if kind is MediaSourceKind.EMPTY or kind is MediaSourceKind.UNSUPPORTED:
        blocks.append("ingestion_unsupported_source")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))
    if kind is MediaSourceKind.HTTP_URL:
        blocks.append("ingestion_http_source_blocked")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))
    if kind is MediaSourceKind.HTTPS_URL and not allow_https_source:
        blocks.append("ingestion_https_source_disabled_by_policy")
        return MediaIngestionEligibilityResult(allowed=False, block_codes=tuple(blocks))
    # TELEGRAM_PHOTO or HTTPS_URL when allowed — bytes fetch remains future work.
    return MediaIngestionEligibilityResult(allowed=True, block_codes=())
