"""B6: deterministic branded Telegram post/card preview (read-only, no publish, no image download, no AI)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.models.supplier import SupplierOffer
from app.schemas.supplier_admin import AdminSupplierOfferRead
from app.services.packaging_formatting import (
    format_date_range_pretty,
    format_price_for_display,
    format_route_for_telegram,
    format_vehicle_block_ro,
    parse_snapshot_datetimes,
)

B6_TEMPLATE_VERSION = "b6_v1"
_MISSING_PRICE = (
    "[PRICE — not on file: confirm with supplier. Do not invent an amount.]"
)

_MSG_COVER_TG = (
    "Cover is a Telegram file reference, not a public URL — visual check required before channel publish."
)
_MSG_COVER_MISSING = "No cover image on file — a branded card image will be required before publish."


def _quality_warning_items_from_row(row: SupplierOffer) -> list[dict[str, str]]:
    qj = row.quality_warnings_json
    if qj is None:
        return []
    if isinstance(qj, dict) and "items" in qj:
        out: list[dict[str, str]] = []
        for x in qj.get("items") or []:
            if isinstance(x, dict) and ("message" in x or "code" in x):
                out.append({"code": str(x.get("code", "")), "message": str(x.get("message", ""))})
        return out
    if isinstance(qj, list):
        return [
            x if isinstance(x, dict) else {"code": "legacy", "message": str(x)} for x in qj
        ]
    return []


def _base_draft(packaging_draft: dict | list | None) -> dict[str, Any]:
    if isinstance(packaging_draft, dict):
        return dict(packaging_draft)
    return {}


def _cover_block(ref: str | None) -> tuple[dict[str, Any] | None, bool, list[dict[str, str]]]:
    extra: list[dict[str, str]] = []
    r = (ref or "").strip()
    if not r:
        return None, True, [
            {
                "code": "b6_cover_missing",
                "message": _MSG_COVER_MISSING,
            }
        ]
    is_tg = r.startswith(SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX)
    if is_tg:
        source = "telegram_photo"
        extra.append(
            {
                "code": "b6_cover_telegram_not_public",
                "message": _MSG_COVER_TG,
            }
        )
    elif r.lower().startswith(("http://", "https://")):
        source = "url"
    else:
        source = "other"
    cover: dict[str, Any] = {
        "source": source,
        "ref": r,
        "status": "needs_admin_visual_review",
    }
    return cover, False, extra


def _build_card_lines(
    row: SupplierOffer, *, date_pretty: str, route: str | None, price_display: str
) -> list[dict[str, str]]:
    sm = (row.sales_mode.value if row.sales_mode is not None else "") or ""
    sm_low = sm.lower()
    lines: list[dict[str, str]] = [
        {"id": "date", "label": "Data", "value": date_pretty},
    ]
    rline = (route or "").strip()
    if rline:
        lines.append({"id": "route", "label": "Traseu", "value": rline})
    if sm_low == "full_bus":
        if price_display != _MISSING_PRICE:
            pl = f"{price_display} — tot autobuzul"
        else:
            pl = price_display
        lines.append({"id": "price", "label": "Pret", "value": pl})
        vb = format_vehicle_block_ro(
            sm,
            row.vehicle_label,
            row.seats_total,
        )
        lines.append({"id": "vehicle", "label": "Vehicul", "value": vb})
    elif sm_low == "per_seat":
        if price_display != _MISSING_PRICE:
            pl = f"{price_display} / persoana"
        else:
            pl = price_display
        lines.append({"id": "price", "label": "Pret", "value": pl})
        lines.append(
            {
                "id": "availability",
                "label": "Disponibilitate",
                "value": "Locurile se confirma la rezervare",
            }
        )
    else:
        lines.append(
            {
                "id": "price",
                "label": "Pret",
                "value": price_display,
            }
        )
    return lines


def build_branded_telegram_preview(
    row: SupplierOffer,
    packaging_draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = _base_draft(packaging_draft)

    d_iso = row.departure_datetime.isoformat() if row.departure_datetime is not None else ""
    r_iso = row.return_datetime.isoformat() if row.return_datetime is not None else ""
    dts = parse_snapshot_datetimes(d_iso, r_iso) if d_iso and r_iso else None
    if dts is not None:
        dep_dt, ret_dt = dts
        date_pretty = format_date_range_pretty(dep_dt, ret_dt)
    else:
        date_pretty = "—"

    raw_route = format_route_for_telegram(
        row.description, row.program_text, row.transport_notes
    )
    pds = str(row.base_price) if row.base_price is not None else None
    price_display = format_price_for_display(
        pds, row.currency, missing_placeholder=_MISSING_PRICE
    )

    cover, fallback_needed, cover_warnings = _cover_block(row.cover_media_reference)
    warn = list(_quality_warning_items_from_row(row))
    warn.extend(cover_warnings)
    cta: list[str] = []
    raw_cta = base.get("cta_variants")
    if isinstance(raw_cta, list):
        cta = [str(x) for x in raw_cta if str(x).strip()]

    caption = str(base.get("telegram_post_draft") or "").strip()

    out: dict[str, Any] = {
        "template_version": B6_TEMPLATE_VERSION,
        "channel": "telegram",
        "title": row.title,
        "card_lines": _build_card_lines(
            row, date_pretty=date_pretty, route=raw_route, price_display=price_display
        ),
        "caption": caption,
        "cta": cta,
        "warnings": warn,
    }
    if cover is not None:
        out["cover"] = cover
    if fallback_needed:
        out["fallback_branded_card_needed"] = True
    return out


def read_with_branded_preview(row: SupplierOffer) -> AdminSupplierOfferRead:
    base = _base_draft(row.packaging_draft_json)
    preview = build_branded_telegram_preview(row, base)
    merged: dict[str, Any] = {**base, "branded_telegram_preview": preview}
    read = AdminSupplierOfferRead.model_validate(row, from_attributes=True)
    return read.model_copy(update={"packaging_draft_json": merged})


class BrandedTelegramPreviewNotFoundError(Exception):
    pass


def persist_branded_preview_to_db(session: Session, *, offer_id: int) -> AdminSupplierOfferRead:
    from app.repositories.supplier import SupplierOfferRepository

    row = SupplierOfferRepository().get_any(session, offer_id=offer_id)
    if row is None:
        raise BrandedTelegramPreviewNotFoundError
    base = _base_draft(row.packaging_draft_json)
    preview = build_branded_telegram_preview(row, base)
    merged: dict[str, Any] = {**base, "branded_telegram_preview": preview}
    row.packaging_draft_json = merged
    session.flush()
    session.refresh(row)
    return read_with_branded_preview(row)
