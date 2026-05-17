"""A3: derive supplier-safe clarification drafts vs internal tasks from A2 intake validation (read-only)."""

from __future__ import annotations

import re

from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead
from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead

# Substrings (lowercase) that must never be echoed to suppliers as-is.
_INTERNAL_MARKERS: tuple[str, ...] = (
    "execution link",
    "execution_link",
    "prepare_chain",
    "prepare chain",
    "prepare_conversion",
    "conversion chain",
    "conversion_chain",
    "conversion target",
    " mini app",
    "mini_app",
    "mini-app",
    "b11",
    "layer a",
    "layer_a",
    "cta_safety",
    "exact_tour",
    "tour_not_listed",
    "missing_execution",
    "ineligible",
    "media_review_replacement",
    "publish_safe",
    "catalog gate",
    "gate:",
    "gate_failed",
    "console_",
    "preview_payload",
    "offer_debug",
    "cta:",
    "blockers_count",
    "/admin/",
    "/mini",
    "wire payment",
)


class SupplierClarificationDraftService:
    """Builds ``SupplierClarificationDraftRead`` from ``SupplierOfferIntakeValidationRead``."""

    _ASK_TITLE = (
        "Ne puteți ajuta cu un titlu foarte clar pentru excursie, ca toată lumea să înțeleagă destinația?"
    )
    _ASK_PROGRAM = (
        "Vă rugăm să ne trimiteți pe scurt programul excursiei: ce se vizitează și ordinea aproximativă a opririlor."
    )
    _ASK_PROGRAM_MORE = (
        "Dacă puteți, completați câteva detalii în plus despre program (timpii și opririle principale)."
    )
    _ASK_BOOKING_CONTACT = (
        "Cum preferați să fie contactul pentru rezervări: telefon, mesaj sau alt mod simplu pentru clienți?"
    )
    _ASK_PHOTO = (
        "Aveți o fotografie clară cu excursia sau autocarul? Dacă da, o putem folosi ca imagine principală."
    )
    _ASK_LIFECYCLE_DRAFT = (
        "Oferta este încă în lucru? Vă rugăm să ne confirmați când este gata pentru verificare."
    )
    _ASK_FINAL_DESCRIPTION = (
        "Vă rugăm să verificați descrierea ofertei: lipsește ceva important pentru clienți "
        "(loc de plecare, ore, ce este inclus)?"
    )
    _ASK_GENERIC_FOLLOWUP = (
        "Aveți alte clarificări practice despre tur (preț pentru un loc, locul de îmbarcare, durata drumului)?"
    )

    @staticmethod
    def _push_unique(bucket: list[str], value: str) -> None:
        v = (value or "").strip()
        if v and v not in bucket:
            bucket.append(v)

    @classmethod
    def _text_sounds_internal(cls, text: str) -> bool:
        t = (text or "").lower()
        if not t:
            return False
        if re.search(r"\bcta\b", t):
            return True
        if re.search(r"\bqr\b", t):
            return True
        for m in _INTERNAL_MARKERS:
            if m in t:
                return True
        return False

    @classmethod
    def _supplier_prompt_for_missing_fact(cls, fact_key: str) -> str | None:
        if fact_key == "offer_list_title":
            return cls._ASK_TITLE
        if fact_key == "preview_customer_body":
            return cls._ASK_PROGRAM
        if fact_key == "preview_primary_cta":
            return cls._ASK_BOOKING_CONTACT
        return None

    @classmethod
    def _supplier_prompt_for_weak(cls, entry: str) -> tuple[str | None, bool]:
        """Returns (supplier_line, is_internal_only)."""
        e = (entry or "").strip()
        lower = e.lower()
        if lower.startswith("offer_title_descriptive"):
            return cls._ASK_TITLE, False
        if lower.startswith("preview_customer_body_depth"):
            return cls._ASK_PROGRAM_MORE, False
        if lower.startswith("preview_media_reference"):
            return cls._ASK_PHOTO, False
        if lower.startswith("lifecycle:"):
            sub = lower.removeprefix("lifecycle:").strip()
            if sub in ("draft", "rejected"):
                return cls._ASK_LIFECYCLE_DRAFT, False
            return None, True
        if lower.startswith("publish_readiness:") or lower.startswith("gate_warning:"):
            return None, True
        if lower.startswith("packaging:"):
            return cls._ASK_FINAL_DESCRIPTION, False
        if lower.startswith("preview_warning:"):
            rest = e.split(":", 1)[-1].strip()
            if cls._text_sounds_internal(rest):
                return None, True
            return cls._ASK_GENERIC_FOLLOWUP, False
        if cls._text_sounds_internal(e):
            return None, True
        return None, False

    @classmethod
    def build_from_intake_validation(
        cls,
        intake: SupplierOfferIntakeValidationRead,
    ) -> SupplierClarificationDraftRead:
        supplier: list[str] = []
        internal: list[str] = []

        for raw in intake.blocks_catalog_conversion:
            cls._push_unique(internal, str(raw))

        for raw in intake.blocks_publication:
            cls._push_unique(internal, str(raw))

        for key in intake.facts_missing_required:
            line = cls._supplier_prompt_for_missing_fact(key)
            if line:
                cls._push_unique(supplier, line)

        for w in intake.facts_weak_or_unclear:
            w_str = str(w)
            if w_str.lower().startswith("packaging:"):
                cls._push_unique(internal, w_str)
            s_line, force_internal = cls._supplier_prompt_for_weak(w_str)
            if force_internal:
                cls._push_unique(internal, w_str)
            if s_line:
                cls._push_unique(supplier, s_line)
            elif not force_internal and cls._text_sounds_internal(w_str):
                cls._push_unique(internal, w_str)

        for pub_line in intake.blocks_publication:
            if "media_policy:media_blocked" in str(pub_line):
                cls._push_unique(supplier, cls._ASK_PHOTO)

        for line in intake.suggested_supplier_requests:
            s = str(line).strip()
            if not s:
                continue
            if cls._text_sounds_internal(s):
                cls._push_unique(internal, s)
            else:
                # Plain-language free text may still confuse suppliers; keep internal unless obviously human.
                if len(s) > 220 or "http" in s.lower() or "/" in s:
                    cls._push_unique(internal, s)
                else:
                    cls._push_unique(supplier, s)

        return SupplierClarificationDraftRead(
            supplier_offer_id=intake.supplier_offer_id,
            supplier_facing_asks=supplier[:15],
            internal_admin_tasks=internal[:40],
        )


__all__ = ["SupplierClarificationDraftService"]
