"""B12A: showcase marketing template library — selection + safe supplemental copy (no publish path changes).

Inference uses only SupplierOffer fields. ``LAST_SEATS_URGENT`` is never auto-inferred (requires verified live inventory).
Supplemental lines are factual only (discounts from real columns; seat counts only when explicitly passed in preview helpers).
"""

from __future__ import annotations

import html
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
    """Mutates ``packaging_draft_extras`` in place."""
    packaging_draft_extras["showcase_marketing_template_library_v1"] = build_showcase_marketing_template_library_v1(
        offer
    )


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
