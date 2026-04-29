"""Read-only deterministic content quality signals for supplier offers (Slice 1 — admin visibility).

Does not mutate data, call AI, or gate publish/catalog/bridge.
Reuses packaging assessment helpers where aligned with operator-facing copy risks.
"""

from __future__ import annotations

from app.models.supplier import SupplierOffer
from app.schemas.supplier_admin import (
    AdminSupplierOfferContentQualityReviewRead,
    ContentQualityWarningItemRead,
)
from app.services.supplier_offer_packaging_service import (
    assess_missing_and_warnings,
    assess_packaging_truth_warnings,
)


def _dedupe_append(
    out: list[ContentQualityWarningItemRead],
    seen: set[str],
    *,
    code: str,
    message: str,
) -> None:
    if code in seen:
        return
    seen.add(code)
    out.append(ContentQualityWarningItemRead(code=code, message=message))


def evaluate_content_quality_review(offer: SupplierOffer) -> AdminSupplierOfferContentQualityReviewRead:
    """Aggregate deterministic warnings for marketing/copy readiness before publish-like decisions."""
    seen: set[str] = set()
    items: list[ContentQualityWarningItemRead] = []

    _missing, miss_warnings = assess_missing_and_warnings(offer)
    for w in miss_warnings:
        _dedupe_append(items, seen, code=w["code"], message=w["message"])

    for w in assess_packaging_truth_warnings(offer):
        _dedupe_append(items, seen, code=w["code"], message=w["message"])

    title = (offer.title or "").strip()
    short_hook = (offer.short_hook or "").strip()
    marketing_summary = (offer.marketing_summary or "").strip()
    description = (offer.description or "").strip()

    if short_hook:
        if len(short_hook) < 20:
            _dedupe_append(
                items,
                seen,
                code="short_hook_very_short",
                message="short_hook is very short — consider richer hook copy before channel/Mini App emphasis.",
            )
        if title and short_hook.casefold() == title.casefold():
            _dedupe_append(
                items,
                seen,
                code="short_hook_equals_title",
                message="short_hook equals title — add distinct hook text if marketing relies on it.",
            )

    if marketing_summary and len(marketing_summary) < 120:
        _dedupe_append(
            items,
            seen,
            code="marketing_summary_thin",
            message="marketing_summary is shorter than recommended — verify it reflects the trip before publishing.",
        )

    if description and len(description) < 80:
        _dedupe_append(
            items,
            seen,
            code="description_thin",
            message="description is very short — supplier narrative may be insufficient for customer-facing surfaces.",
        )

    return AdminSupplierOfferContentQualityReviewRead(
        warnings=items,
        has_quality_warnings=len(items) > 0,
    )


__all__ = ["evaluate_content_quality_review"]
