"""v1 source-of-truth facts snapshot for supplier offers (AI fact-lock grounding).

Aligned with ``PackagingFactSnapshot`` / packaging grounding JSON — commercial fields only,
serialized deterministically for content hashing. Does not call AI or mutate persistence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.models.supplier import SupplierOffer


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def build_facts_dict_v1(offer: SupplierOffer) -> dict[str, Any]:
    """Normalized plain dict for hashing and AI ``fact_claims`` comparison."""
    dp = offer.discount_percent
    da = offer.discount_amount
    bp = offer.base_price
    return {
        "title": (offer.title or "").strip(),
        "description": offer.description or "",
        "program_text": _str_or_none(offer.program_text),
        "included_text": _str_or_none(offer.included_text),
        "excluded_text": _str_or_none(offer.excluded_text),
        "departure": offer.departure_datetime.isoformat(),
        "return": offer.return_datetime.isoformat(),
        "boarding_places_text": _str_or_none(offer.boarding_places_text),
        "transport_notes": _str_or_none(offer.transport_notes),
        "vehicle_label": _str_or_none(offer.vehicle_label),
        "base_price": str(bp) if bp is not None else None,
        "currency": _str_or_none(offer.currency),
        "seats_total": int(offer.seats_total),
        "sales_mode": offer.sales_mode.value,
        "payment_mode": offer.payment_mode.value,
        "service_composition": offer.service_composition.value,
        "discount_code": _str_or_none(offer.discount_code),
        "discount_percent": str(dp) if dp is not None else None,
        "discount_amount": str(da) if da is not None else None,
        "discount_valid_until": offer.discount_valid_until.isoformat()
        if offer.discount_valid_until is not None
        else None,
        "cover_media_reference": _str_or_none(offer.cover_media_reference),
        "recurrence_type": _str_or_none(offer.recurrence_type),
        "recurrence_rule": _str_or_none(offer.recurrence_rule),
        "short_hook": _str_or_none(offer.short_hook),
        "marketing_summary": _str_or_none(offer.marketing_summary),
    }


def compute_facts_content_hash(facts: dict[str, Any]) -> str:
    """Stable SHA-256 over canonical JSON (sorted keys, UTF-8)."""
    canonical = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SourceFactsSnapshotV1:
    """Server-side source facts snapshot for one supplier offer row."""

    source_facts_version: str
    supplier_offer_id: int
    content_hash: str
    facts: dict[str, Any]


def build_source_facts_snapshot_v1(offer: SupplierOffer) -> SourceFactsSnapshotV1:
    facts = build_facts_dict_v1(offer)
    h = compute_facts_content_hash(facts)
    return SourceFactsSnapshotV1(
        source_facts_version="v1",
        supplier_offer_id=int(offer.id),
        content_hash=h,
        facts=facts,
    )


# Keys emitted by ``build_facts_dict_v1`` — ``fact_claims`` must not invent extra keys.
ALLOWED_FACT_CLAIM_KEYS: frozenset[str] = frozenset(
    [
        "title",
        "description",
        "program_text",
        "included_text",
        "excluded_text",
        "departure",
        "return",
        "boarding_places_text",
        "transport_notes",
        "vehicle_label",
        "base_price",
        "currency",
        "seats_total",
        "sales_mode",
        "payment_mode",
        "service_composition",
        "discount_code",
        "discount_percent",
        "discount_amount",
        "discount_valid_until",
        "cover_media_reference",
        "recurrence_type",
        "recurrence_rule",
        "short_hook",
        "marketing_summary",
    ]
)


__all__ = [
    "ALLOWED_FACT_CLAIM_KEYS",
    "SourceFactsSnapshotV1",
    "build_facts_dict_v1",
    "build_source_facts_snapshot_v1",
    "compute_facts_content_hash",
]
