"""Romanian customer-facing HTML for moderated supplier-offer Telegram showcase posts."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.models.enums import SupplierServiceComposition, TourSalesMode
from app.models.supplier import SupplierOffer
from app.services.supplier_offer_deep_link import private_bot_deeplink

_BUCHAREST = ZoneInfo("Europe/Bucharest")

_RO_MONTHS = (
    "ianuarie",
    "februarie",
    "martie",
    "aprilie",
    "mai",
    "iunie",
    "iulie",
    "august",
    "septembrie",
    "octombrie",
    "noiembrie",
    "decembrie",
)


def format_datetime_ro_bucharest(dt: datetime) -> str:
    """Format as e.g. ``10 mai 2026, 11:00`` in Europe/Bucharest (customer-facing, no UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    local = dt.astimezone(_BUCHAREST)
    day = local.day
    month_name = _RO_MONTHS[local.month - 1]
    year = local.year
    hm = f"{local.hour:d}:{local.minute:02d}"
    return f"{day} {month_name} {year}, {hm}"


def parse_boarding_places(boarding_places_text: str | None) -> list[str]:
    """Split supplier-provided boarding text; supports newlines, ``|``, or ``•`` separators."""
    if not boarding_places_text or not boarding_places_text.strip():
        return []
    raw = boarding_places_text.replace("•", "\n").replace("|", "\n")
    out: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if s and s not in out:
            out.append(s)
    return out


def _marketing_hook(description: str) -> str:
    text = (description or "").strip()
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    hook = " ".join(lines[:2]) if lines else ""
    if len(hook) > 280:
        hook = hook[:277].rsplit(" ", 1)[0] + "…"
    return hook


def _include_nu_include_lines(composition: SupplierServiceComposition) -> tuple[str | None, str | None]:
    """Short Romanian Include / Nu include from service composition only (no invention)."""
    include_map = {
        SupplierServiceComposition.TRANSPORT_ONLY: "Include: transport.",
        SupplierServiceComposition.TRANSPORT_GUIDE: "Include: transport și ghid.",
        SupplierServiceComposition.TRANSPORT_WATER: "Include: transport și apă (minerală).",
        SupplierServiceComposition.TRANSPORT_GUIDE_WATER: "Include: transport, ghid și apă (minerală).",
    }
    inc = include_map.get(composition)
    if not inc:
        return None, None
    nu = "Nu include: bilete de intrare și cheltuieli personale."
    return inc, nu


def _truncate_telegram_caption(html: str, max_len: int = 1024) -> str:
    if len(html) <= max_len:
        return html
    return html[: max(0, max_len - 1)] + "…"


@dataclass(frozen=True)
class ShowcasePublication:
    caption_html: str
    photo_url: str | None


def build_showcase_publication(offer: SupplierOffer, settings: Settings) -> ShowcasePublication:
    """Romanian marketing caption + optional photo URL for Telegram showcase."""
    title = html.escape((offer.title or "").strip() or "Ofertă")
    hook_raw = _marketing_hook(offer.description)
    hook = html.escape(hook_raw) if hook_raw else ""

    plecare = format_datetime_ro_bucharest(offer.departure_datetime)
    intoarcere = format_datetime_ro_bucharest(offer.return_datetime)

    body_lines: list[str] = [
        f"<b>{title}</b>",
        "",
    ]
    if offer.sales_mode == TourSalesMode.FULL_BUS:
        body_lines.append("<i>Potrivit pentru grupuri.</i>")
        body_lines.append("")
    if hook:
        body_lines.append(hook)
        body_lines.append("")
    body_lines.append(f"<b>Plecare:</b> {html.escape(plecare)}")
    body_lines.append(f"<b>Întoarcere:</b> {html.escape(intoarcere)}")

    places = parse_boarding_places(offer.boarding_places_text)
    if places:
        places_esc = [html.escape(p) for p in places]
        body_lines.append(f"<b>Îmbarcare:</b> {' • '.join(places_esc)}")

    vehicle = (offer.vehicle_label or "").strip() or (offer.transport_notes or "").strip()
    if vehicle:
        body_lines.append(f"<b>Transport:</b> {html.escape(vehicle[:200])}")

    if offer.seats_total and offer.seats_total > 0:
        body_lines.append(f"<b>Locuri:</b> {offer.seats_total}")

    if offer.base_price is not None and (offer.currency or "").strip():
        cur = offer.currency.strip()
        body_lines.append(
            f"<b>Preț:</b> de la {html.escape(str(offer.base_price))} {html.escape(cur)}",
        )

    inc_line, nu_line = _include_nu_include_lines(offer.service_composition)
    if inc_line and nu_line:
        body_lines.append("")
        body_lines.append(html.escape(inc_line))
        body_lines.append(html.escape(nu_line))

    body_lines.append("")

    uname = (settings.telegram_bot_username or "").strip().lstrip("@")
    mini = (settings.telegram_mini_app_url or "").strip().rstrip("/")
    cta_parts: list[str] = []
    if uname:
        det_url = html.escape(private_bot_deeplink(bot_username=uname, offer_id=offer.id))
        cta_parts.append(f'<a href="{det_url}">Detalii</a>')
    if mini:
        cta_parts.append(f'<a href="{html.escape(mini)}">Rezervă</a>')
    if cta_parts:
        body_lines.append("<b>" + " | ".join(cta_parts) + "</b>")

    body_lines.append("")
    body_lines.append("Abonează-te la canal pentru rute noi și oferte viitoare.")

    caption = "\n".join(body_lines)
    caption = _truncate_telegram_caption(caption)

    photo = (offer.showcase_photo_url or "").strip() or None
    return ShowcasePublication(caption_html=caption, photo_url=photo)


def format_supplier_offer_showcase_html(offer: SupplierOffer, settings: Settings) -> str:
    """Backward-compatible: caption HTML only (use :func:`build_showcase_publication` for photo)."""
    return build_showcase_publication(offer, settings).caption_html
