"""AI public copy fact-lock: compare persisted ``fact_claims`` to live source facts (no AI HTTP).

Reads optional ``packaging_draft_json['ai_public_copy_v1']`` — populated later when AI drafts exist.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.supplier import SupplierOffer
from app.schemas.supplier_admin import AdminSupplierOfferAiPublicCopyReviewRead
from app.services.supplier_offer_source_facts_snapshot import (
    ALLOWED_FACT_CLAIM_KEYS,
    SourceFactsSnapshotV1,
    build_source_facts_snapshot_v1,
)


def _extract_ai_public_copy_v1(packaging_draft_json: Any) -> dict[str, Any] | None:
    if not isinstance(packaging_draft_json, dict):
        return None
    raw = packaging_draft_json.get("ai_public_copy_v1")
    return raw if isinstance(raw, dict) else None


def _normalize_for_compare(field: str, source_val: Any, claimed_val: Any) -> tuple[Any, Any]:
    """Return (normalized_source, normalized_claim) for equality check."""
    if field in {"base_price", "discount_percent", "discount_amount"}:
        return _norm_decimal(source_val), _norm_decimal(claimed_val)

    if field == "seats_total":
        try:
            return int(source_val), int(claimed_val)
        except (TypeError, ValueError):
            return source_val, claimed_val

    if field in {"departure", "return", "discount_valid_until"}:
        return _norm_iso(str(source_val) if source_val is not None else ""), _norm_iso(
            str(claimed_val) if claimed_val is not None else ""
        )

    sv, cv = source_val, claimed_val
    if isinstance(sv, str):
        sv = sv.strip()
    if isinstance(cv, str):
        cv = cv.strip()
    return sv, cv


def _norm_decimal(v: Any) -> Decimal | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _norm_iso(s: str) -> str:
    """Best-effort normalize ISO datetime strings (allows comparison after parse)."""
    if not s:
        return ""
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.isoformat()
    except ValueError:
        return s.strip()


def evaluate_ai_public_copy_fact_lock(offer: SupplierOffer) -> AdminSupplierOfferAiPublicCopyReviewRead:
    """Compare ``ai_public_copy_v1.fact_claims`` to live facts; surface staleness and mismatches."""
    snap: SourceFactsSnapshotV1 = build_source_facts_snapshot_v1(offer)
    ai_block = _extract_ai_public_copy_v1(offer.packaging_draft_json)

    blocking: list[str] = []
    warns: list[str] = []

    if ai_block is None:
        return AdminSupplierOfferAiPublicCopyReviewRead(
            source_facts_version=snap.source_facts_version,
            snapshot_content_hash=snap.content_hash,
            ai_block_present=False,
            packaged_snapshot_ref=None,
            snapshot_stale=False,
            fact_claims_present=False,
            fact_lock_passed=True,
            blocking_issues=[],
            warnings=[],
        )

    ref = ai_block.get("snapshot_ref") or ai_block.get("snapshot_content_hash") or ai_block.get("content_hash")
    packaged_ref = str(ref).strip() if ref is not None else None
    stale = bool(packaged_ref) and packaged_ref != snap.content_hash
    if stale:
        blocking.append(
            "snapshot_stale: ai_public_copy_v1.snapshot_ref does not match live source facts hash "
            "(edit offer or regenerate AI draft).",
        )

    rc_raw = ai_block.get("fact_claims")
    claims_invalid = rc_raw is not None and not isinstance(rc_raw, dict)
    if claims_invalid:
        blocking.append("invalid_fact_claims: fact_claims must be an object when present.")

    raw_claims: dict[str, Any] = rc_raw if isinstance(rc_raw, dict) else {}
    claims_present = len(raw_claims) > 0

    if claims_present and not claims_invalid:
        facts = snap.facts
        for key in raw_claims:
            if key not in ALLOWED_FACT_CLAIM_KEYS:
                blocking.append(f"unknown_fact_claim_key:{key}")

        for key in sorted(raw_claims.keys()):
            if key not in ALLOWED_FACT_CLAIM_KEYS:
                continue
            claimed_val = raw_claims[key]
            src_val = facts.get(key)
            ns, nc = _normalize_for_compare(key, src_val, claimed_val)
            if ns != nc:
                blocking.append(f"fact_mismatch:{key}")

    elif ai_block and not claims_present and not claims_invalid:
        warns.append(
            "ai_public_copy_v1 present without non-empty fact_claims — fact-lock cannot validate commercial claims.",
        )

    passed = len(blocking) == 0
    return AdminSupplierOfferAiPublicCopyReviewRead(
        source_facts_version=snap.source_facts_version,
        snapshot_content_hash=snap.content_hash,
        ai_block_present=True,
        packaged_snapshot_ref=packaged_ref,
        snapshot_stale=stale,
        fact_claims_present=claims_present,
        fact_lock_passed=passed,
        blocking_issues=blocking,
        warnings=warns,
    )


__all__ = ["evaluate_ai_public_copy_fact_lock"]
