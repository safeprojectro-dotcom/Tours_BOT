"""B4: admin-triggered draft packaging (deterministic or pluggable AI). No publish, no Tour, no bookings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferPackagingStatus
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead


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


def _fmt_price(snap: PackagingFactSnapshot) -> str:
    if snap.base_price and snap.currency:
        return f"{snap.base_price} {snap.currency}"
    if snap.base_price:
        return str(snap.base_price)
    return "[PRICE — not on file: confirm with supplier. Do not invent an amount.]"


def build_deterministic_draft(
    snap: PackagingFactSnapshot,
    *,
    missing: list[str],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    price_line = _fmt_price(snap)
    seats_line = str(snap.seats_total) if snap.seats_total > 0 else "[SEAT COUNT — not confirmed]"
    program_norm = (snap.program_text or "").strip()
    if not program_norm:
        program_norm = (snap.description or "").strip()[:2000]
    if not program_norm:
        program_norm = "[Program details pending — require supplier program_text.]"

    short_hook = _clip(
        f"{snap.title} · {seats_line} seats" if snap.seats_total > 0 else f"{snap.title} · {seats_line}",
        500,
    )
    marketing = _clip(
        f"{snap.title}\n\n{snap.description}\n\nDeparture: {snap.departure_iso}\nReturn: {snap.return_iso}\n"
        f"Price: {price_line}\nSeats: {seats_line}\n(All facts copied from supplier intake — verify before publish.)",
        10000,
    )
    t_post = (
        f"**{snap.title}**\n\n"
        f"🗓 Departure: {snap.departure_iso}\n"
        f"🔙 Return: {snap.return_iso}\n"
        f"💶 Price: {price_line}\n"
        f"👥 Capacity: {seats_line}\n"
        f"🛂 Sales/payment: {snap.sales_mode} / {snap.payment_mode}\n\n"
        f"{_clip(snap.description, 1500)}"
    )
    brief_p = _clip(program_norm, 1500)
    mini_short = _clip(
        f"{snap.title} — {price_line}. {seats_line} seats. {snap.departure_iso[:10]} → {snap.return_iso[:10]}",
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
        "layout_hint": {"style": "facts_only", "price_line_grounded": bool(snap.base_price and snap.currency)},
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
