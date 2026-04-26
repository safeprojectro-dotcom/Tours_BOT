"""B4: admin-triggered draft packaging (deterministic or pluggable AI). No publish, no Tour, no bookings."""

from __future__ import annotations

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
    format_date_range_pretty,
    format_price_for_display,
    format_route_pretty,
    format_sales_and_payment_pretty,
    format_seats_count,
    parse_snapshot_datetimes,
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
    base_price: str | None
    currency: str | None
    seats_total: int
    sales_mode: str
    payment_mode: str
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
        base_price=str(row.base_price) if row.base_price is not None else None,
        currency=row.currency,
        seats_total=row.seats_total,
        sales_mode=row.sales_mode.value,
        payment_mode=row.payment_mode.value,
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
                "base_price": snapshot.base_price,
                "currency": snapshot.currency,
                "seats_total": snapshot.seats_total,
                "sales_mode": snapshot.sales_mode,
                "payment_mode": snapshot.payment_mode,
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

    short_hook = _clip(
        f"{snap.title} — {seats_count} seats" if snap.seats_total > 0 else f"{snap.title} — {seats_count}",
        500,
    )
    marketing = _clip(
        f"{snap.title}\n\n{strip_iso_timestamps_for_display(snap.description)}\n\n"
        f"🗓 {date_range}\n"
        f"💶 {price_line}\n"
        f"👥 {seats_count} seats (capacity from intake)\n"
        f"🛂 {format_sales_and_payment_pretty(snap.sales_mode, snap.payment_mode)}\n"
        f"(All facts from supplier snapshot — verify before publish.)",
        10000,
    )
    route = format_route_pretty(snap.boarding_places_text)
    if dts is not None:
        t_post = build_telegram_post_draft(
            title=snap.title,
            description=snap.description,
            dep=dep_dt,
            ret=ret_dt,
            price_line=price_line,
            seats_line=seats_count,
            sales_mode=snap.sales_mode,
            payment_mode=snap.payment_mode,
            route=route,
            included=snap.included_text,
            excluded=snap.excluded_text,
        )
    else:
        r_line = f"🚍 Route: {route}\n" if route else ""
        inc = (snap.included_text or "").strip()
        exc = (snap.excluded_text or "").strip()
        extra = ""
        if inc:
            extra += f"\n\n✅ Includes: {inc}"
        if exc:
            extra += f"\n\n❌ Not included: {exc}"
        t_post = (
            f"**{snap.title}**\n\n"
            f"⚠️ {date_range}\n\n"
            f"💶 Price: {price_line}\n"
            f"👥 Seats: {seats_count}\n"
            f"{r_line}"
            f"🛂 {format_sales_and_payment_pretty(snap.sales_mode, snap.payment_mode)}\n"
            f"{_clip(strip_iso_timestamps_for_display(snap.description), 1500)}"
            f"{extra}"
        )
    brief_p = _clip(program_norm, 1500)
    mini_line = f"{seats_count} seats" if snap.seats_total > 0 else seats_count
    mini_short = _clip(
        f"{snap.title} — {price_line}. {mini_line}. {date_range}.",
        500,
    )
    mini_full = _clip(marketing, 20000)
    cta1 = "Open details in Mini App (after publication)"
    cta2 = "Contact operator (no automatic booking in packaging step)"
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
            "style": "facts_only",
            "price_line_grounded": bool(snap.base_price and snap.currency),
            "grounding_debug": build_grounding_debug_json(
                departure_iso=snap.departure_iso,
                return_iso=snap.return_iso,
                sales_mode=snap.sales_mode,
                payment_mode=snap.payment_mode,
            ),
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
