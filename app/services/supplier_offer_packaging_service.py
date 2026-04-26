"""B4: admin-triggered draft packaging (deterministic or pluggable AI). No publish, no Tour, no bookings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferPackagingStatus
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead
from app.services.packaging_formatting import (
    build_grounding_debug_json,
    build_telegram_post_draft,
    format_commercial_summary_prose,
    format_date_range_pretty,
    format_marketing_price_line_ro,
    format_price_for_display,
    format_seats_count,
    parse_snapshot_datetimes,
    polish_program_text_for_telegram_block,
    strip_iso_timestamps_for_display,
)


class SupplierOfferPackagingNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class PackagingFactSnapshot:
    """Grounding for prompts / deterministic text — no admin_internal_notes."""

    offer_id: int
    title: str
    description: str
    program_text: str | None
    included_text: str | None
    excluded_text: str | None
    departure_iso: str
    return_iso: str
    boarding_places_text: str | None
    transport_notes: str | None
    vehicle_label: str | None
    base_price: str | None
    currency: str | None
    seats_total: int
    sales_mode: str
    payment_mode: str
    discount_code: str | None
    discount_percent: str | None
    discount_amount: str | None
    discount_valid_until_iso: str | None
    cover_media_reference: str | None
    recurrence_type: str | None
    recurrence_rule: str | None
    short_hook: str | None
    marketing_summary: str | None


class PackagingAIGenerator(Protocol):
    def generate_draft(
        self,
        snapshot: PackagingFactSnapshot,
        *,
        missing_field_codes: list[str],
        quality_warnings: list[dict[str, str]],
    ) -> dict[str, Any] | None: ...


def build_packaging_system_prompt() -> str:
    return (
        "You are a tour packaging assistant. Output JSON only, no markdown fences. "
        "You MUST copy commercial facts (dates, times, price, currency, seat counts) only from the grounding object. "
        "Never invent dates, prices, or seat numbers. If a value is null or missing, use explicit placeholders and list "
        "gaps in missing_fields, not made-up numbers. This is a draft for admin review — not published."
    )


def _as_snapshot(row: SupplierOffer) -> PackagingFactSnapshot:
    return PackagingFactSnapshot(
        offer_id=row.id,
        title=row.title,
        description=row.description,
        program_text=row.program_text,
        included_text=row.included_text,
        excluded_text=row.excluded_text,
        departure_iso=row.departure_datetime.isoformat(),
        return_iso=row.return_datetime.isoformat(),
        boarding_places_text=row.boarding_places_text,
        transport_notes=row.transport_notes,
        vehicle_label=row.vehicle_label,
        base_price=str(row.base_price) if row.base_price is not None else None,
        currency=row.currency,
        seats_total=row.seats_total,
        sales_mode=row.sales_mode.value,
        payment_mode=row.payment_mode.value,
        discount_code=row.discount_code,
        discount_percent=str(row.discount_percent) if row.discount_percent is not None else None,
        discount_amount=str(row.discount_amount) if row.discount_amount is not None else None,
        discount_valid_until_iso=row.discount_valid_until.isoformat()
        if row.discount_valid_until is not None
        else None,
        cover_media_reference=row.cover_media_reference,
        recurrence_type=row.recurrence_type,
        recurrence_rule=row.recurrence_rule,
        short_hook=row.short_hook,
        marketing_summary=row.marketing_summary,
    )


def build_packaging_user_json_blob(snapshot: PackagingFactSnapshot, existing_missing: list[str], existing_warnings: list) -> str:
    import json

    return json.dumps(
        {
            "grounding": {
                "title": snapshot.title,
                "description": snapshot.description,
                "program_text": snapshot.program_text,
                "included_text": snapshot.included_text,
                "excluded_text": snapshot.excluded_text,
                "departure": snapshot.departure_iso,
                "return": snapshot.return_iso,
                "boarding": snapshot.boarding_places_text,
                "transport_notes": snapshot.transport_notes,
                "vehicle_label": snapshot.vehicle_label,
                "base_price": snapshot.base_price,
                "currency": snapshot.currency,
                "seats_total": snapshot.seats_total,
                "sales_mode": snapshot.sales_mode,
                "payment_mode": snapshot.payment_mode,
                "discount_code": snapshot.discount_code,
                "discount_percent": snapshot.discount_percent,
                "discount_amount": snapshot.discount_amount,
                "discount_valid_until": snapshot.discount_valid_until_iso,
                "cover": snapshot.cover_media_reference,
                "recurrence": snapshot.recurrence_rule,
                "recurrence_type": snapshot.recurrence_type,
            },
            "precomputed_gaps": {"missing": existing_missing, "warnings": existing_warnings},
        },
        ensure_ascii=False,
    )


def assess_missing_and_warnings(row: SupplierOffer) -> tuple[list[str], list[dict[str, str]]]:
    missing: list[str] = []
    warnings: list[dict[str, str]] = []

    if row.base_price is None:
        missing.append("base_price")
        warnings.append({"code": "missing_price", "message": "base_price is not set — do not invent an amount."})
    if row.base_price is not None and not (row.currency or "").strip():
        missing.append("currency")
        warnings.append({"code": "missing_currency", "message": "currency is not set while price is present."})
    if not (row.program_text or "").strip():
        missing.append("program_text")
        warnings.append({"code": "weak_program", "message": "program_text is empty or very thin."})
    if row.seats_total <= 0:
        missing.append("seats_total")
        warnings.append({"code": "invalid_capacity", "message": "seats_total is zero — invalid."})
    if not (row.included_text or "").strip() and not (row.excluded_text or "").strip():
        warnings.append(
            {
                "code": "inclusions_undefined",
                "message": "Both included and excluded are empty; supplier should confirm.",
            }
        )
    return missing, warnings


_FAKE_SCARCITY_RE = re.compile(
    r"(?i)\b(ultim[ae]?\s+loc(uri)?|last\s+seats?|only\s+\d+\s+left|hurry|grab\s+now|"
    r"urgent|restante?\s+loc(uri)?|putin[ae]?\s+loc(uri)?|few\s+seats|selling\s+fast)\b"
)


def assess_packaging_truth_warnings(row: SupplierOffer) -> list[dict[str, str]]:
    """B4.3: discount / scarcity truth — no live inventory; formatting-only inferences."""
    w: list[dict[str, str]] = []
    dp, da = row.discount_percent, row.discount_amount
    has_pct = dp is not None and dp > 0
    has_amt = da is not None and da > 0
    if (row.discount_code or "").strip() and not has_pct and not has_amt:
        w.append(
            {
                "code": "orphan_promo_code",
                "message": "discount_code is set without discount_percent or discount_amount — not a public promo in this draft.",
            }
        )
    if row.discount_valid_until is not None and not has_pct and not has_amt:
        w.append(
            {
                "code": "discount_deadline_without_value",
                "message": "discount_valid_until is set but no percent/amount discount — deadline is not customer-facing alone.",
            }
        )
    blob = f"{row.title or ''}\n{row.description or ''}"
    if _FAKE_SCARCITY_RE.search(blob):
        w.append(
            {
                "code": "scarcity_language_unsubstantiated",
                "message": "Marketing text may imply limited seats/urgency without a live stock source in this step — review.",
            }
        )
    return w


def _clip(s: str, n: int) -> str:
    t = s.strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


_MISSING_PRICE = (
    "[PRICE — not on file: confirm with supplier. Do not invent an amount.]"
)
_SEATS_UNCONF = "[SEAT COUNT — not confirmed]"


def build_deterministic_draft(
    snap: PackagingFactSnapshot,
    *,
    missing: list[str],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    price_line = format_price_for_display(
        snap.base_price, snap.currency, missing_placeholder=_MISSING_PRICE
    )
    seats_count = format_seats_count(snap.seats_total, not_confirmed=_SEATS_UNCONF)
    dts = parse_snapshot_datetimes(snap.departure_iso, snap.return_iso)
    if dts is not None:
        dep_dt, ret_dt = dts
        date_range = format_date_range_pretty(dep_dt, ret_dt)
    else:
        dep_dt = ret_dt = None
        date_range = "[Trip dates — see supplier record; could not format snapshot]"
    program_norm = (snap.program_text or "").strip()
    if not program_norm:
        program_norm = (snap.description or "").strip()[:2000]
    if not program_norm:
        program_norm = "[Program details pending — require supplier program_text.]"
    elif program_norm != "[Program details pending — require supplier program_text.]":
        p2 = polish_program_text_for_telegram_block(program_norm)
        if p2 and p2.strip():
            program_norm = p2
        else:
            program_norm = "[Program details pending — require supplier program_text.]"

    sm_low = (snap.sales_mode or "").strip().lower()
    if sm_low == "full_bus":
        short_hook = _clip(f"{snap.title} — autobuz complet", 500)
    elif sm_low == "per_seat":
        short_hook = _clip(f"{snap.title} — tarif per loc", 500)
    else:
        short_hook = _clip(f"{snap.title}", 500)
    m_price = format_marketing_price_line_ro(
        snap.sales_mode, snap.base_price, snap.currency, missing_placeholder=_MISSING_PRICE
    )
    marketing = _clip(
        f"{snap.title}\n\n{strip_iso_timestamps_for_display(snap.description)}\n\n"
        f"🗓 {date_range}\n"
        f"{m_price}\n"
        f"{format_commercial_summary_prose(snap.sales_mode, snap.payment_mode)}\n"
        f"(Toate datele din oferta furnizor — verificati inainte de publicare.)",
        10000,
    )
    common_tg_kwargs: dict[str, Any] = {
        "title": snap.title,
        "description": snap.description,
        "program_text": snap.program_text,
        "transport_notes": snap.transport_notes,
        "base_price": snap.base_price,
        "currency": snap.currency,
        "sales_mode": snap.sales_mode,
        "payment_mode": snap.payment_mode,
        "vehicle_label": snap.vehicle_label,
        "seats_total": snap.seats_total,
        "discount_code": snap.discount_code,
        "discount_percent": snap.discount_percent,
        "discount_amount": snap.discount_amount,
        "discount_valid_until_iso": snap.discount_valid_until_iso,
        "included": snap.included_text,
        "excluded": snap.excluded_text,
        "missing_price_placeholder": _MISSING_PRICE,
    }
    if dts is not None:
        t_post = build_telegram_post_draft(
            dep=dep_dt,
            ret=ret_dt,
            **common_tg_kwargs,  # type: ignore[misc]
        )
    else:
        t_post = build_telegram_post_draft(dep=None, ret=None, **common_tg_kwargs)  # type: ignore[misc]
    brief_p = _clip(program_norm, 1500)
    if sm_low == "full_bus" and snap.seats_total > 0:
        mini_line = f"cap. max. {seats_count} locuri (autobuz complet, fara stoc live)"
    else:
        mini_line = "per loc; locurile se confirma la rezervare"
    mini_short = _clip(
        f"{snap.title} — {price_line}. {mini_line}. {date_range}.",
        500,
    )
    mini_full = _clip(marketing, 20000)
    if sm_low == "full_bus":
        cta1, cta2 = "👉 Rezerva pentru grupul tau", "👉 Cere oferta personalizata"
    else:
        cta1, cta2 = "👉 Rezerva locul tau", "👉 Cere oferta personalizata"
    inc = (snap.included_text or "").strip() or None
    exc = (snap.excluded_text or "").strip() or None
    extras: dict[str, Any] = {
        "telegram_post_draft": t_post,
        "brief_program": brief_p,
        "mini_app_short_description": mini_short,
        "mini_app_full_description": mini_full,
        "cta_variants": [cta1, cta2],
        "image_card_prompt": f"Layout hint: hero for “{snap.title}”. Reuse supplier cover only; B7 may render card.",
        "layout_hint": {
            "style": "b4_2_marketing_template",
            "price_line_grounded": bool(snap.base_price and snap.currency),
            "grounding_debug": {
                **build_grounding_debug_json(
                    departure_iso=snap.departure_iso,
                    return_iso=snap.return_iso,
                    sales_mode=snap.sales_mode,
                    payment_mode=snap.payment_mode,
                ),
                "boarding_places_text": snap.boarding_places_text,
            },
        },
        "source": "deterministic",
    }
    return {
        "short_hook": _clip(short_hook, 512),
        "marketing_summary": marketing,
        "normalized_program_text": _clip(program_norm, 20000),
        "polished_included": inc,
        "polished_excluded": exc,
        "packaging_draft_extras": extras,
        "missing_field_codes": list(missing),
        "quality_warning_items": [dict(x) for x in warnings],
    }


class _NullAIGenerator:
    def generate_draft(
        self,
        snapshot: PackagingFactSnapshot,
        *,
        missing_field_codes: list[str],
        quality_warnings: list[dict[str, str]],
    ) -> dict[str, Any] | None:
        return None


def _packaging_status_after_assessment(missing: list[str], warnings: list[dict[str, str]]) -> SupplierOfferPackagingStatus:
    if missing or warnings:
        return SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW
    return SupplierOfferPackagingStatus.PACKAGING_GENERATED


class SupplierOfferPackagingService:
    def __init__(self, *, ai: PackagingAIGenerator | None = None) -> None:
        self._repo = SupplierOfferRepository()
        self._ai: PackagingAIGenerator = ai or _NullAIGenerator()

    def generate_and_persist(self, session: Session, *, offer_id: int) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferPackagingNotFoundError
        row.packaging_status = SupplierOfferPackagingStatus.PACKAGING_PENDING
        session.flush()
        missing, qwarn = assess_missing_and_warnings(row)
        qwarn.extend(assess_packaging_truth_warnings(row))
        snap = _as_snapshot(row)
        draft = self._ai.generate_draft(
            snap, missing_field_codes=missing, quality_warnings=qwarn
        )
        if not draft:
            draft = build_deterministic_draft(snap, missing=missing, warnings=qwarn)

        sh = str(draft.get("short_hook") or "").strip()
        row.short_hook = _clip(sh, 512) if sh else None
        ms0 = str(draft.get("marketing_summary") or "").strip()
        row.marketing_summary = (ms0[:10000] if ms0 else None)
        if draft.get("normalized_program_text") is not None:
            row.program_text = (str(draft["normalized_program_text"]))[:20000]
        if "polished_included" in draft:
            v = draft.get("polished_included")
            row.included_text = (str(v)[:10000] if v is not None and str(v).strip() else None)
        if "polished_excluded" in draft:
            v = draft.get("polished_excluded")
            row.excluded_text = (str(v)[:10000] if v is not None and str(v).strip() else None)
        extras = draft.get("packaging_draft_extras") or {}
        row.packaging_draft_json = extras
        m_codes: list[str] = list(draft.get("missing_field_codes", missing))
        w_raw = draft.get("quality_warning_items")
        if w_raw is not None:
            w_items: list[dict[str, str]] = [dict(x) for x in w_raw]  # type: ignore[misc]
        else:
            w_items = [dict(x) for x in qwarn]
        # Prefer structured list for missing; admin UI can show codes.
        row.missing_fields_json = {"field_codes": m_codes, "b4": True}
        row.quality_warnings_json = {"items": w_items, "b4": True}
        row.packaging_status = _packaging_status_after_assessment(m_codes, w_items)
        session.commit()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)
