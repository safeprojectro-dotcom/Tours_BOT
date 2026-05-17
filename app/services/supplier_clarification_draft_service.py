"""A3B: whitelist-only supplier clarification drafts; hard technical filter (read-only)."""

from __future__ import annotations

import re

from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead
from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead

# Exact catalogue (order fixed; indices 0..16).
_ALLOWED_RO_ASKS: tuple[str, ...] = (
    "Vă rugăm să trimiteți o fotografie clară pentru ofertă.",
    "Vă rugăm să confirmați prețul pentru această ofertă.",
    "Vă rugăm să confirmați moneda prețului.",
    "Vă rugăm să confirmați data și ora plecării.",
    "Vă rugăm să confirmați data și ora întoarcerii.",
    "Vă rugăm să confirmați ruta și destinația.",
    "Vă rugăm să confirmați locul de îmbarcare.",
    "Vă rugăm să confirmați durata aproximativă a drumului.",
    "Vă rugăm să confirmați câte locuri sunt disponibile.",
    "Vă rugăm să confirmați tipul vehiculului.",
    "Vă rugăm să confirmați ce este inclus în preț.",
    "Vă rugăm să confirmați ce nu este inclus în preț.",
    "Vă rugăm să trimiteți o descriere scurtă a excursiei.",
    "Vă rugăm să confirmați dacă există reducere pentru această ofertă.",
    "Dacă există reducere, vă rugăm să confirmați valoarea, perioada și condițiile reducerii.",
    "Vă rugăm să confirmați condițiile de plată.",
    "Vă rugăm să confirmați condițiile de anulare.",
)

_MAX_SUPPLIER_ASKS = 5

# Substrings (case-insensitive) that disqualify any candidate line from supplier-facing copy.
_FORBIDDEN_SUPPLIER_SUBSTRINGS: tuple[str, ...] = (
    "execution link",
    "execution_link",
    "conversion chain",
    "exact-tour",
    "exact_tour",
    "mini app",
    "mini_app",
    "mini-app",
    "blockers_count",
    "prepare_chain",
    "prepare chain",
    "prepare_conversion",
    "prepare_conversion_chain",
    "cta_safety",
    "publish_readiness",
    "offer_debug",
    "flags_publish_not_ready",
    "content_quality",
    "orphan_promo_code",
    "description_thin",
    "media_review_replacement_requested",
    "publish_safe",
    "showcase_media",
    "showcase_preview",
    "catalog gate",
    "gate:",
    "b7",
    "b10",
    "b11",
    "b15",
    "layer a",
    "layer_a",
    "internal path",
    "admin_action_path",
    "admin_tour_path",
    "route key",
    "payload",
    "debug",
    "blocker code",
    "console_",
    "preview_payload",
    "ineligible",
    "tour_not_listed",
    "missing_execution",
    "wire payment",
    "/admin/",
    "/mini",
    "qr",
)

class SupplierClarificationDraftService:
    """Builds ``SupplierClarificationDraftRead`` from ``SupplierOfferIntakeValidationRead``."""

    @staticmethod
    def _push_unique(bucket: list[str], value: str) -> None:
        v = (value or "").strip()
        if v and v not in bucket:
            bucket.append(v)

    @classmethod
    def _forbidden_supplier_copy(cls, text: str) -> bool:
        t = (text or "").lower()
        if not t:
            return False
        if "[" in text and "]" in text and re.search(r"\[[a-z0-9_]+\]", text, re.I):
            return True
        if re.search(r"\b[b](7|10|11|15)\b", t):
            return True
        if re.search(r"\b[a-z]{2,}_[a-z][a-z0-9_]*", t):
            return True
        if re.search(r"\bcta\b", t):
            return True
        for m in _FORBIDDEN_SUPPLIER_SUBSTRINGS:
            if m in t:
                return True
        return False

    @classmethod
    def _text_sounds_internal(cls, text: str) -> bool:
        return cls._forbidden_supplier_copy(text)

    @classmethod
    def _collect_internal_from_intake(cls, intake: SupplierOfferIntakeValidationRead) -> list[str]:
        internal: list[str] = []
        for raw in intake.blocks_catalog_conversion:
            cls._push_unique(internal, str(raw))
        for raw in intake.blocks_publication:
            cls._push_unique(internal, str(raw))
        for w in intake.facts_weak_or_unclear:
            cls._push_unique(internal, str(w))
        for line in intake.suggested_supplier_requests:
            cls._push_unique(internal, str(line).strip())
        return internal

    @classmethod
    def _indices_from_missing_fact(cls, fact_key: str) -> set[int]:
        fk = (fact_key or "").strip()
        if fk == "offer_list_title":
            return {5}
        if fk == "preview_customer_body":
            return {12}
        if fk == "preview_primary_cta":
            return {15}
        return set()

    @classmethod
    def _indices_from_weak(cls, entry: str) -> tuple[set[int], bool]:
        """Return (whitelist indices, raw_is_internal_copy)."""
        e = (entry or "").strip()
        lower = e.lower()
        idx: set[int] = set()
        if lower.startswith("preview_media_reference") or lower.startswith("preview_media"):
            idx.add(0)
        if lower.startswith("offer_title_descriptive") or lower.startswith("offer_list_title"):
            idx.add(5)
        if lower.startswith("preview_customer_body_depth"):
            idx.add(12)
        if lower.startswith("packaging:"):
            return {12}, False
        if lower.startswith("preview_warning:"):
            rest = e.split(":", 1)[-1].lower()
            if "reducere" in rest or "discount" in rest or "promo" in rest or "orphan_promo" in rest:
                idx.update({13, 14})
            if "description" in rest or "thin" in rest or "content_quality" in rest:
                idx.add(12)
            if cls._forbidden_supplier_copy(rest) and not idx:
                return set(), True
        if lower.startswith("lifecycle:") or lower.startswith("publish_readiness:"):
            return set(), True
        if lower.startswith("gate_warning:"):
            return set(), True
        if cls._forbidden_supplier_copy(e):
            return set(), True
        return idx, False

    @classmethod
    def _indices_from_publication_line(cls, line: str) -> set[int]:
        s = str(line).lower()
        idx: set[int] = set()
        if "media_policy:media_blocked" in s or "media_blocked" in s:
            idx.add(0)
        return idx

    @classmethod
    def _merge_supplier_indices(cls, intake: SupplierOfferIntakeValidationRead) -> list[int]:
        collected: set[int] = set()
        for k in intake.facts_missing_required:
            collected |= cls._indices_from_missing_fact(k)
        for w in intake.facts_weak_or_unclear:
            add, _ = cls._indices_from_weak(str(w))
            collected |= add
        for pub in intake.blocks_publication:
            collected |= cls._indices_from_publication_line(str(pub))
        ordered = sorted(collected)
        return ordered[:_MAX_SUPPLIER_ASKS]

    @classmethod
    def _build_whitelist_strings(cls, indices: list[int]) -> list[str]:
        out: list[str] = []
        for i in indices:
            if 0 <= i < len(_ALLOWED_RO_ASKS):
                s = _ALLOWED_RO_ASKS[i]
                if not cls._forbidden_supplier_copy(s):
                    cls._push_unique(out, s)
        return out[:_MAX_SUPPLIER_ASKS]

    @classmethod
    def _format_supplier_message_ro(cls, asks: list[str]) -> str | None:
        if not asks:
            return None
        body_lines = [
            "Bună ziua! Pentru ofertă avem nevoie de câteva clarificări:",
            "",
        ]
        for n, q in enumerate(asks[:_MAX_SUPPLIER_ASKS], start=1):
            body_lines.append(f"{n}. {q}")
        body_lines.extend(["", "Mulțumim!"])
        return "\n".join(body_lines)

    @classmethod
    def build_from_intake_validation(
        cls,
        intake: SupplierOfferIntakeValidationRead,
    ) -> SupplierClarificationDraftRead:
        internal = cls._collect_internal_from_intake(intake)
        idx_list = cls._merge_supplier_indices(intake)
        supplier = cls._build_whitelist_strings(idx_list)
        msg = cls._format_supplier_message_ro(supplier)
        return SupplierClarificationDraftRead(
            supplier_offer_id=intake.supplier_offer_id,
            supplier_facing_asks=supplier,
            supplier_facing_message_ro=msg,
            internal_admin_tasks=internal[:80],
        )


__all__ = ["SupplierClarificationDraftService"]
