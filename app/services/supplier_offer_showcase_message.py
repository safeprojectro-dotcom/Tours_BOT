"""Romanian customer-facing HTML for moderated supplier-offer Telegram showcase posts.

B12/B13: deterministic **text-only** channel posts (photo URL not sent from this builder);
template vs Telegram HTML assembly vs CTA helpers are split for clarity.

Primary public CTA remains the stable bot deep link ``supoffer_<id>`` (B11 resolves exact Tour
when an active execution link exists). Mini App link uses non-booking wording.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.models.enums import SupplierServiceComposition, TourSalesMode
from app.models.supplier import SupplierOffer
from app.services.supplier_offer_deep_link import mini_app_supplier_offer_url, private_bot_deeplink

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

# CTA labels (Romanian) — avoid "Rezervă" in channel unless bookability is wired; B12 slice is soft.
_CTA_BOT_LABEL = "Deschide în bot"
_CTA_MINI_APP_LABEL = "Vezi în aplicație"
_DISCLAIMER_LINE = (
    "<i>Disponibilitatea și pașii pentru rezervare se verifică în aplicație și prin bot.</i>"
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


def _truncate_telegram_caption(html_cap: str, max_len: int = 1024) -> str:
    if len(html_cap) <= max_len:
        return html_cap
    return html_cap[: max(0, max_len - 1)] + "…"


def _template_fact_lines_html(offer: SupplierOffer) -> list[str]:
    """Build escaped HTML lines from SupplierOffer ORM facts (no CTAs)."""
    title = html.escape((offer.title or "").strip() or "Ofertă")
    hook_raw = _marketing_hook(offer.description)
    hook = html.escape(hook_raw) if hook_raw else ""

    plecare = format_datetime_ro_bucharest(offer.departure_datetime)
    intoarcere = format_datetime_ro_bucharest(offer.return_datetime)

    lines: list[str] = [
        f"<b>{title}</b>",
        "",
    ]
    if offer.sales_mode == TourSalesMode.FULL_BUS:
        lines.append("<i>Potrivit pentru grupuri.</i>")
        lines.append("")
    if hook:
        lines.append(hook)
        lines.append("")
    lines.append(f"<b>Plecare:</b> {html.escape(plecare)}")
    lines.append(f"<b>Întoarcere:</b> {html.escape(intoarcere)}")

    places = parse_boarding_places(offer.boarding_places_text)
    if places:
        places_esc = [html.escape(p) for p in places]
        lines.append(f"<b>Îmbarcare:</b> {' • '.join(places_esc)}")

    vehicle = (offer.vehicle_label or "").strip() or (offer.transport_notes or "").strip()
    if vehicle:
        lines.append(f"<b>Transport:</b> {html.escape(vehicle[:200])}")

    if offer.seats_total and offer.seats_total > 0:
        lines.append(f"<b>Locuri:</b> {offer.seats_total}")

    if offer.base_price is not None and (offer.currency or "").strip():
        cur = offer.currency.strip()
        lines.append(
            f"<b>Preț:</b> orientativ de la {html.escape(str(offer.base_price))} {html.escape(cur)}",
        )

    inc_line, nu_line = _include_nu_include_lines(offer.service_composition)
    if inc_line and nu_line:
        lines.append("")
        lines.append(html.escape(inc_line))
        lines.append(html.escape(nu_line))

    lines.append("")
    lines.append(_DISCLAIMER_LINE)
    return lines


def _cta_row_html(*, offer_id: int, settings: Settings) -> str | None:
    """Primary: stable bot ``supoffer_<id>``. Secondary: Mini App landing (non-booking label)."""
    uname = (settings.telegram_bot_username or "").strip().lstrip("@")
    mini_base = (settings.telegram_mini_app_url or "").strip().rstrip("/")
    parts: list[str] = []

    if uname:
        bot_url = html.escape(private_bot_deeplink(bot_username=uname, offer_id=offer_id))
        parts.append(f'<a href="{bot_url}">{html.escape(_CTA_BOT_LABEL)}</a>')

    if mini_base:
        mini_url = html.escape(mini_app_supplier_offer_url(mini_app_url=mini_base, offer_id=offer_id))
        parts.append(f'<a href="{mini_url}">{html.escape(_CTA_MINI_APP_LABEL)}</a>')

    if not parts:
        return None
    return "<b>" + " | ".join(parts) + "</b>"


def _footer_lines_html() -> list[str]:
    return [
        "",
        "Abonează-te la canal pentru rute noi și oferte viitoare.",
    ]


def _assemble_showcase_html(
    *,
    facts: list[str],
    cta_row: str | None,
    footer: list[str],
) -> str:
    """Glue template sections and apply Telegram-safe caption length limit."""
    out: list[str] = [*facts]
    out.append("")
    if cta_row:
        out.append(cta_row)
    out.extend(footer)
    caption = "\n".join(out)
    return _truncate_telegram_caption(caption)


@dataclass(frozen=True)
class ShowcasePublication:
    caption_html: str
    photo_url: str | None


def build_showcase_publication(offer: SupplierOffer, settings: Settings) -> ShowcasePublication:
    """Romanian marketing caption; **B12/B13 slice:** ``photo_url`` is always ``None`` (text-only send)."""
    facts = _template_fact_lines_html(offer)
    cta = _cta_row_html(offer_id=offer.id, settings=settings)
    footer = _footer_lines_html()
    caption_html = _assemble_showcase_html(facts=facts, cta_row=cta, footer=footer)
    return ShowcasePublication(caption_html=caption_html, photo_url=None)


def format_supplier_offer_showcase_html(offer: SupplierOffer, settings: Settings) -> str:
    """Backward-compatible: caption HTML only (uses :func:`build_showcase_publication`)."""
    return build_showcase_publication(offer, settings).caption_html
