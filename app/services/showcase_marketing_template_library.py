"""B12A: showcase marketing template library — selection + safe supplemental copy (no publish path changes).

Inference uses only SupplierOffer fields. ``LAST_SEATS_URGENT`` is never auto-inferred (requires verified live inventory).
Supplemental lines are factual only (discounts from real columns; seat counts only when explicitly passed in preview helpers).
"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import Any, TypeAlias

from app.models.enums import (
    ShowcaseMarketingTemplateId,
    SupplierOfferPaymentMode,
    SupplierServiceComposition,
    TourSalesMode,
)
from app.models.supplier import SupplierOffer
from app.services.supplier_offer_showcase_message import (
    build_showcase_fact_lines_html,
    format_datetime_ro_bucharest,
)

JsonDict: TypeAlias = dict[str, Any]


def early_bird_grounded(offer: SupplierOffer) -> bool:
    """True when public promo fields are complete enough for an early-bird supplement (no orphan deadlines)."""
    has_pct = offer.discount_percent is not None and offer.discount_percent > 0
    has_amt = offer.discount_amount is not None and offer.discount_amount > 0
    if not has_pct and not has_amt:
        return False
    return offer.discount_valid_until is not None


def infer_showcase_marketing_template(offer: SupplierOffer) -> ShowcaseMarketingTemplateId:
    """Deterministic template hint from supplier facts. Never infers ``LAST_SEATS_URGENT`` (needs live stock)."""
    sm = offer.sales_mode
    if sm == TourSalesMode.FULL_BUS:
        if early_bird_grounded(offer):
            return ShowcaseMarketingTemplateId.EARLY_BIRD_DISCOUNT
        return ShowcaseMarketingTemplateId.FULL_BUS_PRIVATE_GROUP

    if early_bird_grounded(offer):
        return ShowcaseMarketingTemplateId.EARLY_BIRD_DISCOUNT
    if offer.payment_mode == SupplierOfferPaymentMode.ASSISTED_CLOSURE:
        return ShowcaseMarketingTemplateId.CUSTOM_REQUEST_CTA
    if offer.service_composition != SupplierServiceComposition.TRANSPORT_ONLY:
        return ShowcaseMarketingTemplateId.SUPPLIER_SERVICE_PROMO
    return ShowcaseMarketingTemplateId.PER_SEAT_STANDARD


def last_seats_urgent_allowed(*, live_seats_remaining: int | None) -> bool:
    """Gate for urgency framing — only when a verified non-negative seats count is supplied."""
    return live_seats_remaining is not None and live_seats_remaining > 0


def build_safe_supplemental_lines_ro(
    offer: SupplierOffer,
    template_id: ShowcaseMarketingTemplateId,
) -> list[str]:
    """Plain-text RO lines safe to show ops alongside packaging (facts only). Not wired into channel publish."""
    if template_id == ShowcaseMarketingTemplateId.EARLY_BIRD_DISCOUNT and early_bird_grounded(offer):
        return [_format_early_bird_line_ro(offer)]
    return []


def _format_early_bird_line_ro(offer: SupplierOffer) -> str:
    pct = offer.discount_percent
    amt = offer.discount_amount
    cur = (offer.currency or "").strip()
    parts: list[str] = []
    if pct is not None and pct > 0:
        parts.append(f"{pct:g}%")
    if amt is not None and amt > 0:
        parts.append(f"{amt} {cur}".strip())
    promo = " + ".join(parts) if parts else ""
    code = (offer.discount_code or "").strip()
    valid = offer.discount_valid_until
    if valid is None:
        return "🎟 Ofertă timpurie — din datele ofertei."
    du = format_datetime_ro_bucharest(valid)
    if code and promo:
        return f"🎟 Ofertă timpurie: {promo} (cod {code}) până la {du} — din datele ofertei."
    if promo:
        return f"🎟 Ofertă timpurie: {promo} până la {du} — din datele ofertei."
    return f"🎟 Ofertă timpurie până la {du} — din datele ofertei."


def build_showcase_marketing_template_library_v1(offer: SupplierOffer) -> JsonDict:
    """Structured block stored under ``packaging_draft_json['showcase_marketing_template_library_v1']``."""
    tid = infer_showcase_marketing_template(offer)
    supplemental = build_safe_supplemental_lines_ro(offer, tid)
    return {
        "schema_version": 1,
        "inferred_template_id": tid.value,
        "selection_rules": _selection_trace(offer, tid),
        "blocked_auto_inference": {
            ShowcaseMarketingTemplateId.LAST_SEATS_URGENT.value: "requires_verified_live_seats_remaining",
            ShowcaseMarketingTemplateId.SHORT_ANNOUNCEMENT.value: "admin_or_future_explicit_choice",
            ShowcaseMarketingTemplateId.IMAGE_ONLY_TEASER.value: "admin_or_future_explicit_choice",
            ShowcaseMarketingTemplateId.BRAND_AWARENESS_POST.value: "admin_or_future_explicit_choice",
        },
        "safe_supplemental_lines_ro": supplemental,
    }


def _selection_trace(
    offer: SupplierOffer,
    resolved: ShowcaseMarketingTemplateId,
) -> list[str]:
    trace: list[str] = []
    if offer.sales_mode == TourSalesMode.FULL_BUS:
        trace.append("sales_mode=full_bus")
    else:
        trace.append("sales_mode=per_seat")
    if early_bird_grounded(offer):
        trace.append("early_bird_fields_complete")
    if offer.payment_mode == SupplierOfferPaymentMode.ASSISTED_CLOSURE:
        trace.append("payment_mode=assisted_closure")
    if offer.service_composition != SupplierServiceComposition.TRANSPORT_ONLY:
        trace.append(f"service_composition={offer.service_composition.value}")
    trace.append(f"resolved={resolved.value}")
    return trace


def merge_showcase_marketing_template_library_v1(
    packaging_draft_extras: dict[str, Any],
    offer: SupplierOffer,
) -> None:
    """Mutates ``packaging_draft_extras`` in place. Preserves admin B12B selection keys when regenerating."""
    preserved: dict[str, Any] = {}
    prev = offer.packaging_draft_json
    if isinstance(prev, dict):
        blk = prev.get("showcase_marketing_template_library_v1")
        if isinstance(blk, dict):
            for k in ("admin_selected_template_id", "admin_selected_at", "admin_live_seats_remaining"):
                if k in blk and blk[k] is not None:
                    preserved[k] = blk[k]
    new_block = build_showcase_marketing_template_library_v1(offer)
    new_block.update(preserved)
    packaging_draft_extras["showcase_marketing_template_library_v1"] = new_block


def extract_showcase_marketing_template_library_v1(offer: SupplierOffer) -> JsonDict:
    """Return the v1 library block from ``offer.packaging_draft_json`` or {}."""
    prev = offer.packaging_draft_json
    if not isinstance(prev, dict):
        return {}
    blk = prev.get("showcase_marketing_template_library_v1")
    return dict(blk) if isinstance(blk, dict) else {}


SHOWCASE_TEMPLATE_LIBRARY_ADMIN_KEYS: frozenset[str] = frozenset(
    {"admin_selected_template_id", "admin_selected_at", "admin_live_seats_remaining"}
)


def resolve_effective_showcase_marketing_template(
    offer: SupplierOffer,
) -> tuple[ShowcaseMarketingTemplateId, ShowcaseMarketingTemplateId | None, list[str]]:
    """Effective template for previews: admin selection when valid, else inference.

    Returns ``(effective, selected_or_none, warnings)``.
    """
    inferred = infer_showcase_marketing_template(offer)
    lib = extract_showcase_marketing_template_library_v1(offer)
    raw_sel = lib.get("admin_selected_template_id")
    if raw_sel is None or (isinstance(raw_sel, str) and not raw_sel.strip()):
        return inferred, None, []

    if not isinstance(raw_sel, str):
        return inferred, None, ["invalid_admin_selected_template_id_type"]

    try:
        selected = ShowcaseMarketingTemplateId(raw_sel.strip())
    except ValueError:
        return inferred, None, ["unknown_admin_selected_template_id"]

    if selected == ShowcaseMarketingTemplateId.LAST_SEATS_URGENT:
        n_raw = lib.get("admin_live_seats_remaining")
        try:
            n_int = int(n_raw) if n_raw is not None else None
        except (TypeError, ValueError):
            n_int = None
        if not last_seats_urgent_allowed(live_seats_remaining=n_int):
            return inferred, selected, ["last_seats_urgent_requires_positive_verified_live_seats_remaining"]

    return selected, selected, []


def live_seats_for_preview(offer: SupplierOffer, template_id: ShowcaseMarketingTemplateId) -> int | None:
    """Seat count for template preview helpers (LAST_SEATS only)."""
    if template_id != ShowcaseMarketingTemplateId.LAST_SEATS_URGENT:
        return None
    lib = extract_showcase_marketing_template_library_v1(offer)
    n_raw = lib.get("admin_live_seats_remaining")
    try:
        return int(n_raw) if n_raw is not None else None
    except (TypeError, ValueError):
        return None


def validate_admin_showcase_template_patch(
    *,
    template_id: str | None,
    live_seats_remaining: int | None,
) -> str | None:
    """Return user-facing error message or ``None`` if OK."""
    if template_id is None:
        return None
    try:
        tid = ShowcaseMarketingTemplateId(template_id.strip())
    except ValueError:
        return "template_id must be a known ShowcaseMarketingTemplateId value"
    if tid == ShowcaseMarketingTemplateId.LAST_SEATS_URGENT:
        if live_seats_remaining is None or live_seats_remaining < 1:
            return "live_seats_remaining (>= 1) is required when template_id is last_seats_urgent"
    return None


def apply_admin_showcase_template_to_library_block(
    block: JsonDict,
    *,
    template_id: str | None,
    live_seats_remaining: int | None,
) -> None:
    """Mutates ``block`` in place (expected: ``showcase_marketing_template_library_v1`` contents)."""
    now = datetime.now(UTC).isoformat()
    for k in SHOWCASE_TEMPLATE_LIBRARY_ADMIN_KEYS:
        block.pop(k, None)
    if template_id is None:
        return
    block["admin_selected_template_id"] = template_id.strip()
    block["admin_selected_at"] = now
    try:
        tid = ShowcaseMarketingTemplateId(template_id.strip())
    except ValueError:
        return
    if tid == ShowcaseMarketingTemplateId.LAST_SEATS_URGENT and live_seats_remaining is not None:
        block["admin_live_seats_remaining"] = int(live_seats_remaining)
    elif tid != ShowcaseMarketingTemplateId.LAST_SEATS_URGENT:
        pass


def build_showcase_template_preview_payload(offer: SupplierOffer) -> dict[str, Any]:
    """Plain dict for :class:`AdminSupplierOfferShowcaseTemplatePreviewRead` (avoid circular imports)."""
    inferred = infer_showcase_marketing_template(offer)
    lib = extract_showcase_marketing_template_library_v1(offer)
    raw_selected = lib.get("admin_selected_template_id")
    selected_out: str | None = raw_selected.strip() if isinstance(raw_selected, str) and raw_selected.strip() else None

    effective, _, notes = resolve_effective_showcase_marketing_template(offer)
    live = live_seats_for_preview(offer, effective)
    preview_lines = build_preview_fact_lines_for_template(
        offer,
        effective,
        live_seats_remaining=live,
    )

    choices = [
        {
            "template_id": m.value,
            "requires_verified_live_seats": m == ShowcaseMarketingTemplateId.LAST_SEATS_URGENT,
        }
        for m in ShowcaseMarketingTemplateId
    ]

    overrides = effective != inferred
    return {
        "inferred_template_id": inferred.value,
        "selected_template_id": selected_out,
        "effective_template_id": effective.value,
        "selection_overrides_inference": overrides,
        "preview_fact_lines_ro_html": preview_lines,
        "channel_publish_unchanged": True,
        "notes": notes,
        "template_choices": choices,
    }


def build_preview_fact_lines_for_template(
    offer: SupplierOffer,
    template_id: ShowcaseMarketingTemplateId,
    *,
    live_seats_remaining: int | None = None,
) -> list[str]:
    """Deterministic variant bodies for ops/tooling — **not** used by ``build_showcase_publication`` (channel unchanged)."""
    base = build_showcase_fact_lines_html(offer)
    supplemental = [html.escape(s) for s in build_safe_supplemental_lines_ro(offer, template_id)]

    if template_id == ShowcaseMarketingTemplateId.SHORT_ANNOUNCEMENT:
        cap = 12
        if len(base) <= cap:
            return list(base)
        return base[:cap] + [html.escape("…")]

    if template_id == ShowcaseMarketingTemplateId.IMAGE_ONLY_TEASER:
        teaser: list[str] = []
        for line in base:
            if line.startswith("🚌 ") or line.startswith("📍 "):
                teaser.append(line)
            elif line.startswith("📅 "):
                teaser.append(line)
                break
        return teaser or base[:3]

    if template_id == ShowcaseMarketingTemplateId.BRAND_AWARENESS_POST:
        return base + ["", html.escape("— Voiaj organizat cu plecări planificate. Abonare pentru rute noi.")]

    if template_id == ShowcaseMarketingTemplateId.LAST_SEATS_URGENT:
        if not last_seats_urgent_allowed(live_seats_remaining=live_seats_remaining):
            return list(base)
        n = int(live_seats_remaining or 0)
        extra = html.escape(f"ℹ️ Locuri disponibile (sursă verificată): {n}.")
        insert_at = max(0, len(base) - 4)
        return [*base[:insert_at], extra, *base[insert_at:]]

    out = list(base)
    for s in supplemental:
        if s and (not out or s not in out):
            out.append(s)
    return out
