"""B7.4D: ``publish_safe`` vNext metadata blocks — pure merge helpers (no ingest, no publish)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.core.media_storage_types import StoredObject
from app.models.supplier import SupplierOffer
from app.services.supplier_offer_publish_safe_stub import (
    EXPECTED_FUTURE_STORAGE,
    MEDIA_REVIEW_KEY,
    PUBLISH_SAFE_KEY,
    REASON_NO_DURABLE_STORAGE,
    STORAGE_KIND_NONE,
    merge_publish_safe_into_draft as merge_publish_safe_stub_into_draft,
)

B7_4D_VERSION = "b7_4d"


class PublishSafeVNextStatus(StrEnum):
    """``publish_safe.status`` values for B7.4D metadata."""

    DEFERRED = "deferred"
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    BLOCKED = "blocked"


def fingerprint_source_media_reference(source_media_reference: str) -> str:
    """SHA-256 hex of normalized UTF-8 reference (no raw secret material)."""

    norm = (source_media_reference or "").strip().encode("utf-8")
    return hashlib.sha256(norm).hexdigest()


def review_snapshot_to_stored_value(review_snapshot: dict[str, Any] | str | None) -> str | None:
    """Normalize ``review_snapshot`` for JSON (string preferred; dict JSON-dumped stably)."""

    if review_snapshot is None:
        return None
    if isinstance(review_snapshot, str):
        s = review_snapshot.strip()
        return s or None
    return json.dumps(review_snapshot, sort_keys=True, ensure_ascii=False)


def merge_publish_safe_vnext_into_packaging_draft(
    packaging_draft_json: dict[str, Any] | list | None,
    publish_safe_block: dict[str, Any],
) -> dict[str, Any]:
    """Return a new draft dict with only ``publish_safe`` replaced."""

    d = dict(packaging_draft_json) if isinstance(packaging_draft_json, dict) else {}
    out = {**d, PUBLISH_SAFE_KEY: dict(publish_safe_block)}
    return out


def build_publish_safe_deferred(
    *,
    source_media_reference: str | None,
    marked_by: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """vNext-shaped deferred block (backward-compatible with B7.3B stub keys)."""

    t = (now or datetime.now(UTC)).replace(microsecond=0)
    ref = (source_media_reference or "").strip() or None
    return {
        "version": B7_4D_VERSION,
        "status": PublishSafeVNextStatus.DEFERRED.value,
        "reason": REASON_NO_DURABLE_STORAGE,
        "source_media_reference": ref,
        "source_fingerprint": fingerprint_source_media_reference(ref) if ref else None,
        "review_snapshot": None,
        "storage_kind": STORAGE_KIND_NONE,
        "object_key": None,
        "public_url": None,
        "expected_future_storage": EXPECTED_FUTURE_STORAGE,
        "content_type": None,
        "size_bytes": None,
        "ingested_at": None,
        "ingested_by": None,
        "attempt_count": 0,
        "last_error_code": None,
        "last_error_message": None,
        "marked_at": t.isoformat(),
        "marked_by": marked_by,
    }


def build_publish_safe_pending(
    *,
    source_media_reference: str,
    review_snapshot: dict[str, Any] | str | None,
    attempt_count: int,
    ingested_by: str | None,
    now: datetime | None = None,
    reason: str | None = "ingestion_pending",
    storage_kind: str = STORAGE_KIND_NONE,
) -> dict[str, Any]:
    t = (now or datetime.now(UTC)).replace(microsecond=0)
    ref = source_media_reference.strip()
    snap = review_snapshot_to_stored_value(review_snapshot)
    return {
        "version": B7_4D_VERSION,
        "status": PublishSafeVNextStatus.PENDING.value,
        "reason": reason,
        "source_media_reference": ref,
        "source_fingerprint": fingerprint_source_media_reference(ref),
        "review_snapshot": snap,
        "storage_kind": storage_kind,
        "object_key": None,
        "public_url": None,
        "content_type": None,
        "size_bytes": None,
        "ingested_at": t.isoformat(),
        "ingested_by": ingested_by,
        "attempt_count": int(attempt_count),
        "last_error_code": None,
        "last_error_message": None,
    }


def build_publish_safe_ready(
    *,
    stored_object: StoredObject,
    source_media_reference: str,
    review_snapshot: dict[str, Any] | str | None,
    ingested_by: str,
    attempt_count: int,
    storage_kind: str,
    public_url: str | None = None,
    reason: str | None = "ingested",
    now: datetime | None = None,
) -> dict[str, Any]:
    t = (now or datetime.now(UTC)).replace(microsecond=0)
    ref = source_media_reference.strip()
    snap = review_snapshot_to_stored_value(review_snapshot)
    return {
        "version": B7_4D_VERSION,
        "status": PublishSafeVNextStatus.READY.value,
        "reason": reason,
        "source_media_reference": ref,
        "source_fingerprint": fingerprint_source_media_reference(ref),
        "review_snapshot": snap,
        "storage_kind": storage_kind,
        "object_key": stored_object.object_key,
        "public_url": (public_url.strip() if public_url else None) or None,
        "content_type": stored_object.content_type,
        "size_bytes": stored_object.byte_size,
        "ingested_at": t.isoformat(),
        "ingested_by": ingested_by,
        "attempt_count": int(attempt_count),
        "last_error_code": None,
        "last_error_message": None,
    }


def build_publish_safe_failed(
    *,
    source_media_reference: str,
    review_snapshot: dict[str, Any] | str | None,
    last_error_code: str,
    last_error_message: str,
    attempt_count: int,
    ingested_by: str | None,
    now: datetime | None = None,
    storage_kind: str = STORAGE_KIND_NONE,
) -> dict[str, Any]:
    t = (now or datetime.now(UTC)).replace(microsecond=0)
    ref = source_media_reference.strip()
    snap = review_snapshot_to_stored_value(review_snapshot)
    return {
        "version": B7_4D_VERSION,
        "status": PublishSafeVNextStatus.FAILED.value,
        "reason": "ingestion_failed",
        "source_media_reference": ref,
        "source_fingerprint": fingerprint_source_media_reference(ref),
        "review_snapshot": snap,
        "storage_kind": storage_kind,
        "object_key": None,
        "public_url": None,
        "content_type": None,
        "size_bytes": None,
        "ingested_at": t.isoformat(),
        "ingested_by": ingested_by,
        "attempt_count": int(attempt_count),
        "last_error_code": last_error_code,
        "last_error_message": last_error_message,
    }


def build_publish_safe_blocked(
    *,
    reason: str,
    source_media_reference: str | None,
    review_snapshot: dict[str, Any] | str | None,
    marked_by: str | None,
    now: datetime | None = None,
    last_error_code: str | None = "blocked",
    last_error_message: str | None = None,
    attempt_count: int | None = None,
    previous_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t = (now or datetime.now(UTC)).replace(microsecond=0)
    ref = (source_media_reference or "").strip() or None
    snap = review_snapshot_to_stored_value(review_snapshot)
    prev_attempt = int(previous_block.get("attempt_count") or 0) if isinstance(previous_block, dict) else 0
    ac = int(attempt_count) if attempt_count is not None else prev_attempt
    base_storage = STORAGE_KIND_NONE
    if isinstance(previous_block, dict) and previous_block.get("storage_kind"):
        base_storage = str(previous_block.get("storage_kind"))
    return {
        "version": B7_4D_VERSION,
        "status": PublishSafeVNextStatus.BLOCKED.value,
        "reason": reason,
        "source_media_reference": ref,
        "source_fingerprint": fingerprint_source_media_reference(ref) if ref else None,
        "review_snapshot": snap,
        "storage_kind": base_storage,
        "object_key": None,
        "public_url": None,
        "content_type": None,
        "size_bytes": None,
        "ingested_at": None,
        "ingested_by": None,
        "attempt_count": ac,
        "last_error_code": last_error_code,
        "last_error_message": last_error_message,
        "marked_at": t.isoformat(),
        "marked_by": marked_by,
    }


def _current_hero_alignment(
    offer: SupplierOffer, draft: dict[str, Any]
) -> tuple[str | None, str | None]:
    cur = (offer.cover_media_reference or "").strip() or None
    mr = draft.get(MEDIA_REVIEW_KEY)
    snap = (
        (mr.get("cover_media_reference") or "").strip() or None if isinstance(mr, dict) else None
    )
    return cur, snap


def publish_safe_apply_hero_drift_block(
    offer: SupplierOffer,
    packaging_draft_json: dict[str, Any] | list | None,
    *,
    marked_by: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """If ``publish_safe`` is ``ready`` and hero/snapshot no longer align, set ``blocked``; else return merged draft copy."""

    d = dict(packaging_draft_json) if isinstance(packaging_draft_json, dict) else {}
    ps = d.get(PUBLISH_SAFE_KEY)
    if not isinstance(ps, dict) or ps.get("status") != PublishSafeVNextStatus.READY.value:
        return d
    cur, mr_snap = _current_hero_alignment(offer, d)
    stored = review_snapshot_to_stored_value(ps.get("review_snapshot"))
    drift = False
    if not cur:
        drift = True
    elif not stored:
        drift = True
    elif stored != cur:
        drift = True
    elif mr_snap is not None and mr_snap != cur:
        drift = True
    elif mr_snap is not None and stored != mr_snap:
        drift = True
    if not drift:
        return d
    blocked = build_publish_safe_blocked(
        reason="hero_or_review_snapshot_drift",
        source_media_reference=cur or ps.get("source_media_reference"),
        review_snapshot=mr_snap or stored,
        marked_by=marked_by,
        now=now,
        last_error_code="publish_safe_hero_drift",
        last_error_message="publish_safe was ready but cover_media_reference or media_review snapshot drifted",
        previous_block=ps,
    )
    return merge_publish_safe_vnext_into_packaging_draft(d, blocked)


def mark_publish_safe_ready(
    offer: SupplierOffer,
    *,
    stored_object: StoredObject,
    source_media_reference: str,
    review_snapshot: dict[str, Any] | str | None,
    ingested_by: str,
    storage_kind: str = "memory",
    public_url: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Merge a ``ready`` ``publish_safe`` vNext block into the offer's packaging draft (returns full draft)."""

    draft = offer.packaging_draft_json if isinstance(offer.packaging_draft_json, dict) else {}
    prev = draft.get(PUBLISH_SAFE_KEY) if isinstance(draft.get(PUBLISH_SAFE_KEY), dict) else {}
    attempt_count = int(prev.get("attempt_count") or 0) + 1
    block = build_publish_safe_ready(
        stored_object=stored_object,
        source_media_reference=source_media_reference,
        review_snapshot=review_snapshot,
        ingested_by=ingested_by,
        attempt_count=attempt_count,
        storage_kind=storage_kind,
        public_url=public_url,
        now=now,
    )
    return merge_publish_safe_vnext_into_packaging_draft(draft, block)


def merge_deferred_publish_safe_compat(
    row: SupplierOffer,
    draft: dict[str, Any] | None,
    *,
    marked_by: str | None,
    now: datetime | None = None,
    use_vnext_shape: bool = True,
) -> dict[str, Any]:
    """B7.3B deferred merge, optionally as B7.4D-shaped block (replaces ``publish_safe`` only)."""

    if use_vnext_shape:
        base_d = dict(draft) if isinstance(draft, dict) else {}
        stub_merged = merge_publish_safe_stub_into_draft(row, base_d, marked_by=marked_by, now=now)
        ref = None
        ps0 = stub_merged.get(PUBLISH_SAFE_KEY)
        if isinstance(ps0, dict):
            ref = ps0.get("source_media_reference")
        block = build_publish_safe_deferred(source_media_reference=ref, marked_by=marked_by, now=now)
        return merge_publish_safe_vnext_into_packaging_draft(stub_merged, block)
    return merge_publish_safe_stub_into_draft(row, draft, marked_by=marked_by, now=now)
