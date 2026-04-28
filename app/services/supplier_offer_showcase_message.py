"""Romanian customer-facing HTML for moderated supplier-offer Telegram showcase posts.

B12/B13: deterministic **text-only** channel posts (photo URL not sent from this builder).
B13.1: branded RO layout (emoji sections, ``Perioada``, capacity/sales-mode-safe lines, optional
``included_text``/``excluded_text`` bullets); CTA block is ``👉``/``📲`` links, not pipe-joined.

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


def _split_bullet_lines(text: str | None) -> list[str]:
    """Non-empty lines from supplier free text (newlines, •, |)."""
    if not text or not str(text).strip():
        return []
    raw = str(text).replace("•", "\n").replace("|", "\n")
    out: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if s and s not in out:
            out.append(s)
    return out


def _route_or_destination_plain(offer: SupplierOffer) -> str | None:
    """Supplier data only: boarding stops, short_hook, or first line of marketing_summary."""
    places = parse_boarding_places(getattr(offer, "boarding_places_text", None))
    if places:
        return " • ".join(places)
    sh = (getattr(offer, "short_hook", None) or "").strip()
    if sh:
        return sh
    ms = (getattr(offer, "marketing_summary", None) or "").strip()
    if not ms:
        return None
    first = next((ln.strip() for ln in ms.splitlines() if ln.strip()), None)
    return first


def _capacity_line_plain(offer: SupplierOffer) -> str:
    seats = getattr(offer, "seats_total", None) or 0
    n = int(seats) if seats else 0
    if offer.sales_mode == TourSalesMode.FULL_BUS:
        if n > 0:
            return f"Închiriere / grup întreg; ~{n} locuri (orientativ pentru planificare)."
        return "Închiriere / grup întreg (autocar)."
    if n > 0:
        return f"Până la {n} locuri în cadrul excursiei (în limita disponibilității)."
    return "Capacitate în funcție de disponibilitate (se verifică în bot și în aplicație)."


def _sales_mode_safe_line_html(offer: SupplierOffer) -> str | None:
    if offer.sales_mode == TourSalesMode.FULL_BUS:
        return (
            "<i>Ofertă pentru grup / închiriere întreg autocar; detaliile comerciale și disponibilitatea "
            "se confirmă în bot și în aplicație.</i>"
        )
    return (
        "<i>Locurile sunt limitate la capacitatea indicată; tariful este orientativ; "
            "disponibilitatea efectivă se confirmă în bot și în aplicație.</i>"
    )


def _include_exclude_sections_html(
    offer: SupplierOffer,
    *,
    composition: SupplierServiceComposition,
) -> tuple[list[str], list[str]]:
    """
    HTML bullet lines under ✅ Include / ℹ️ Nu include.
    Prefer supplier ``included_text`` / ``excluded_text``; else composition + default exclusions.
    """
    inc_custom = _split_bullet_lines(getattr(offer, "included_text", None))
    exc_custom = _split_bullet_lines(getattr(offer, "excluded_text", None))

    include_map = {
        SupplierServiceComposition.TRANSPORT_ONLY: "transport",
        SupplierServiceComposition.TRANSPORT_GUIDE: "transport și ghid",
        SupplierServiceComposition.TRANSPORT_WATER: "transport și apă (minerală)",
        SupplierServiceComposition.TRANSPORT_GUIDE_WATER: "transport, ghid și apă (minerală)",
    }
    base_inc = include_map.get(composition)

    if inc_custom:
        inc_lines = [f"• {html.escape(s)}" for s in inc_custom]
    elif base_inc:
        inc_lines = [f"• {html.escape(base_inc)}"]
    else:
        inc_lines = []

    if exc_custom:
        exc_lines = [f"• {html.escape(s)}" for s in exc_custom]
    else:
        exc_lines = [
            "• " + html.escape("bilete de intrare"),
            "• " + html.escape("cheltuieli personale"),
        ]
    return inc_lines, exc_lines


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


def _truncate_telegram_caption(html_cap: str, max_len: int = 1024) -> str:
    if len(html_cap) <= max_len:
        return html_cap
    return html_cap[: max(0, max_len - 1)] + "…"


def _template_fact_lines_html(offer: SupplierOffer) -> list[str]:
    """Branded Romanian Telegram HTML sections (facts + disclaimer); no CTAs."""
    title_esc = html.escape((offer.title or "").strip() or "Ofertă")
    lines: list[str] = [f"🚌 <b>{title_esc}</b>", ""]

    hook_raw = _marketing_hook(offer.description)
    if hook_raw:
        lines.extend([html.escape(hook_raw), ""])

    route = _route_or_destination_plain(offer)
    if route:
        lines.append(f"📍 <b>Ruta:</b> {html.escape(route)}")

    plecare = format_datetime_ro_bucharest(offer.departure_datetime)
    intoarcere = format_datetime_ro_bucharest(offer.return_datetime)
    lines.append(f"📅 <b>Perioada:</b> {html.escape(plecare)} – {html.escape(intoarcere)}")
    lines.append("")

    if offer.base_price is not None and (offer.currency or "").strip():
        cur = (offer.currency or "").strip()
        lines.append(
            f"💰 <b>Preț:</b> orientativ de la {html.escape(str(offer.base_price))} {html.escape(cur)}",
        )
        lines.append("")

    vehicle = ((offer.vehicle_label or "").strip() or (getattr(offer, "transport_notes", None) or "").strip())
    if vehicle:
        lines.append(f"🚐 <b>Transport:</b> {html.escape(vehicle[:400])}")
        lines.append("")

    lines.append(f"👥 <b>Capacitate:</b> {html.escape(_capacity_line_plain(offer))}")
    lines.append("")

    lines.append(_sales_mode_safe_line_html(offer))
    lines.append("")

    inc_lines, exc_lines = _include_exclude_sections_html(offer, composition=offer.service_composition)
    if inc_lines:
        lines.append("✅ <b>Include:</b>")
        lines.extend(inc_lines)
        lines.append("")
    if exc_lines:
        lines.append("ℹ️ <b>Nu include:</b>")
        lines.extend(exc_lines)
        lines.append("")

    lines.append(f"🔎 {_DISCLAIMER_LINE}")
    return lines


def _cta_block_html(*, offer_id: int, settings: Settings) -> str | None:
    """Primary: stable bot ``supoffer_<id>``. Secondary: Mini App landing (non-booking label)."""
    uname = (settings.telegram_bot_username or "").strip().lstrip("@")
    mini_base = (settings.telegram_mini_app_url or "").strip().rstrip("/")
    rows: list[str] = []

    if uname:
        bot_url = html.escape(private_bot_deeplink(bot_username=uname, offer_id=offer_id))
        rows.append(f'👉 <a href="{bot_url}">{html.escape(_CTA_BOT_LABEL)}</a>')

    if mini_base:
        mini_url = html.escape(mini_app_supplier_offer_url(mini_app_url=mini_base, offer_id=offer_id))
        rows.append(f'📲 <a href="{mini_url}">{html.escape(_CTA_MINI_APP_LABEL)}</a>')

    if not rows:
        return None
    return "\n".join(rows)


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
    cta = _cta_block_html(offer_id=offer.id, settings=settings)
    footer = _footer_lines_html()
    caption_html = _assemble_showcase_html(facts=facts, cta_row=cta, footer=footer)
    return ShowcasePublication(caption_html=caption_html, photo_url=None)


def format_supplier_offer_showcase_html(offer: SupplierOffer, settings: Settings) -> str:
    """Backward-compatible: caption HTML only (uses :func:`build_showcase_publication`)."""
    return build_showcase_publication(offer, settings).caption_html
