"""B7.2: server-side card render *plan* JSON only (no image bytes, no getFile, no upload, no publish)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferMediaReviewStatus
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead
from app.services.branded_telegram_preview import _base_draft, build_branded_telegram_preview
from app.services.supplier_offer_media_review_service import MEDIA_REVIEW_KEY

B7_2_VERSION = "b7_2"

# Fixed layout for future renderer (4:5 @ 1080px wide)
_DEFAULT_LAYOUT: dict[str, Any] = {
    "aspect_ratio": "4:5",
    "width": 1080,
    "height": 1350,
    "safe_area": {"top": 64, "bottom": 64, "left": 48, "right": 48},
}

# Display-only label; B7.3+ may source from product config
_DEFAULT_BRAND_TEXT = "Tours from Timisoara"

_MAX_TITLE = 220
_MAX_LINE = 480


def _clip(s: str, n: int) -> str:
    t = s.strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def _media_review_status(draft: dict[str, Any]) -> str | None:
    mr = draft.get(MEDIA_REVIEW_KEY)
    if not isinstance(mr, dict):
        return None
    st = (mr.get("status") or "").strip()
    return st or None


def _cover_ref_for_approved(row: SupplierOffer, draft: dict[str, Any]) -> str | None:
    mr = draft.get(MEDIA_REVIEW_KEY)
    if isinstance(mr, dict):
        cr = (mr.get("cover_media_reference") or "").strip()
        if cr:
            return cr
    r = (row.cover_media_reference or "").strip()
    return r or None


def _branded_telegram(row: SupplierOffer, draft: dict[str, Any]) -> dict[str, Any]:
    return build_branded_telegram_preview(row, draft)


def _text_layers_from_branded(brand: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    title = (brand.get("title") or "").strip()
    if title:
        out.append({"role": "title", "text": _clip(title, _MAX_TITLE)})

    lines = brand.get("card_lines") or []
    by_id: dict[str, str] = {}
    for ln in lines:
        if not isinstance(ln, dict):
            continue
        lid = (ln.get("id") or "").strip()
        if not lid:
            continue
        by_id[lid] = str(ln.get("value") or "").strip()

    for role, key in (
        ("date", "date"),
        ("route", "route"),
        ("price", "price"),
        ("vehicle", "vehicle"),
    ):
        v = (by_id.get(key) or "").strip()
        if v:
            out.append({"role": role, "text": _clip(v, _MAX_LINE)})
    return out


def _brand_layers() -> list[dict[str, str]]:
    return [{"role": "brand", "text": _DEFAULT_BRAND_TEXT}]


def build_card_render_preview(row: SupplierOffer, draft: dict[str, Any] | None) -> dict[str, Any]:
    base = _base_draft(draft)
    brand = _branded_telegram(row, base)
    mrs = _media_review_status(base)

    text_layers = _text_layers_from_branded(brand)
    warn: list[dict[str, str]] = []

    if mrs == SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value:
        ref = _cover_ref_for_approved(row, base)
        if not ref:
            warn.append(
                {
                    "code": "b7_2_approved_missing_cover",
                    "message": "media_review is approved_for_card but no cover reference is on file.",
                }
            )
            return {
                "version": B7_2_VERSION,
                "status": "blocked_needs_photo_review",
                "layout": dict(_DEFAULT_LAYOUT),
                "source": {
                    "mode": "approved_cover",
                    "cover_media_reference": None,
                    "source_status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
                },
                "text_layers": text_layers,
                "brand_layers": _brand_layers(),
                "warnings": warn + [dict(x) for x in (brand.get("warnings") or []) if isinstance(x, dict)][:20],
            }
        w_br = [dict(x) for x in (brand.get("warnings") or []) if isinstance(x, dict)][:20]
        return {
            "version": B7_2_VERSION,
            "status": "render_plan_ready",
            "layout": dict(_DEFAULT_LAYOUT),
            "source": {
                "mode": "approved_cover",
                "cover_media_reference": ref,
                "source_status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
            },
            "text_layers": text_layers,
            "brand_layers": _brand_layers(),
            "warnings": w_br,
        }

    if mrs == SupplierOfferMediaReviewStatus.FALLBACK_CARD_REQUIRED.value:
        w_br = [dict(x) for x in (brand.get("warnings") or []) if isinstance(x, dict)][:20]
        return {
            "version": B7_2_VERSION,
            "status": "fallback_plan_ready",
            "layout": dict(_DEFAULT_LAYOUT),
            "source": {
                "mode": "fallback_branded_background",
                "cover_media_reference": _cover_ref_for_approved(row, base) or None,
                "source_status": SupplierOfferMediaReviewStatus.FALLBACK_CARD_REQUIRED.value,
            },
            "text_layers": text_layers,
            "brand_layers": _brand_layers(),
            "warnings": w_br,
        }

    w_br = [dict(x) for x in (brand.get("warnings") or []) if isinstance(x, dict)][:20]
    block_msg = "Cover media is not approved for card rendering (B7.1) or not set to fallback plan."
    if mrs in (
        SupplierOfferMediaReviewStatus.REJECTED_BAD_QUALITY.value,
        SupplierOfferMediaReviewStatus.REJECTED_IRRELEVANT.value,
        SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED.value,
    ):
        block_msg = f"media_review status is {mrs}; resolve review before a render plan can be used."
    elif not mrs:
        block_msg = "No media_review record; set B7.1 status to approved_for_card or fallback_card_required."

    warn.append({"code": "b7_2_needs_photo_review", "message": block_msg})
    return {
        "version": B7_2_VERSION,
        "status": "blocked_needs_photo_review",
        "layout": dict(_DEFAULT_LAYOUT),
        "source": {
            "mode": "blocked_pending_review",
            "cover_media_reference": _cover_ref_for_approved(row, base) or None,
            "source_status": mrs or "none",
        },
        "text_layers": text_layers,
        "brand_layers": _brand_layers(),
        "warnings": warn + w_br,
    }


class CardRenderPreviewNotFoundError(Exception):
    pass


def persist_card_render_preview(session: Session, *, offer_id: int) -> AdminSupplierOfferRead:
    repo = SupplierOfferRepository()
    row = repo.get_any(session, offer_id=offer_id)
    if row is None:
        raise CardRenderPreviewNotFoundError
    base = _base_draft(row.packaging_draft_json)
    plan = build_card_render_preview(row, base)
    merged = {**base, "card_render_preview": plan}
    row.packaging_draft_json = merged
    session.flush()
    session.refresh(row)
    return AdminSupplierOfferRead.model_validate(row, from_attributes=True)
