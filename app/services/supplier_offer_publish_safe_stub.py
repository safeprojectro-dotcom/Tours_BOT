"""B7.3B: metadata-only `publish_safe` block in `packaging_draft_json` — no getFile, no storage, no publish."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.supplier import SupplierOffer

PUBLISH_SAFE_KEY = "publish_safe"
B7_3B_VERSION = "b7_3b"
STATUS_DEFERRED = "deferred"
REASON_NO_DURABLE_STORAGE = "no_durable_media_storage"
STORAGE_KIND_NONE = "none"

# B7.3A: durable public assets = future S3-compatible object store when download/storage is explicitly scoped.
EXPECTED_FUTURE_STORAGE = "s3_compatible_object_store_when_explicitly_scoped"

MEDIA_REVIEW_KEY = "media_review"


def _source_media_reference_from_draft(draft: dict[str, Any], row: SupplierOffer) -> str | None:
    """Prefer snapshot from media_review, then row.cover_media_reference."""
    mr = draft.get(MEDIA_REVIEW_KEY)
    if isinstance(mr, dict):
        cr = (mr.get("cover_media_reference") or "").strip()
        if cr:
            return cr
    r = (row.cover_media_reference or "").strip()
    return r or None


def merge_publish_safe_into_draft(
    row: SupplierOffer, draft: dict[str, Any] | None, *, marked_by: str | None, now: datetime | None = None
) -> dict[str, Any]:
    """Merge the deferred `publish_safe` stub; does not write to the row."""
    d = dict(draft) if isinstance(draft, dict) else {}
    t = (now or datetime.now(UTC)).replace(microsecond=0)
    ref = _source_media_reference_from_draft(d, row)
    d[PUBLISH_SAFE_KEY] = {
        "version": B7_3B_VERSION,
        "status": STATUS_DEFERRED,
        "reason": REASON_NO_DURABLE_STORAGE,
        "source_media_reference": ref,
        "storage_kind": STORAGE_KIND_NONE,
        "object_key": None,
        "public_url": None,
        "expected_future_storage": EXPECTED_FUTURE_STORAGE,
        "marked_at": t.isoformat(),
        "marked_by": marked_by,
    }
    return d
