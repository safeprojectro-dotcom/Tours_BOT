"""Romanian customer-facing HTML for moderated supplier-offer Telegram showcase posts.

B12/B13: deterministic **text-only** channel posts (photo URL not sent from this builder).
B13.1: branded RO layout; B13.2: marketing copy polish (period + times lines, ``program_text`` block,
FULL_BUS firm ``Preț … / grup``, single-line ``Detalii | Rezervă`` CTAs, custom-request upsell).

Channel CTA line: **Detalii** → bot ``supoffer_<id>`` (B11); **Rezervă** → Mini App supplier-offer landing — booking logic unchanged elsewhere.
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

# B13.2: short channel CTAs (links only; execution truth remains in Mini App + bot flows).
_CTA_DETAILS_LABEL = "Detalii"
_CTA_RESERVE_LABEL = "Rezervă"
_CUSTOM_REQUEST_UPSELL = (
    "🧭 Ai nevoie de alt traseu sau alt număr de locuri? Cere o ofertă personalizată."
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


def _bucharest_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(_BUCHAREST)


def format_date_range_compact_ro(departure: datetime, return_at: datetime) -> str:
    """e.g. ``28–29 aprilie 2026`` or single day when same calendar date (Europe/Bucharest)."""
    d1 = _bucharest_local(departure)
    d2 = _bucharest_local(return_at)
    if d1.date() == d2.date():
        return f"{d1.day} {_RO_MONTHS[d1.month - 1]} {d1.year}"
    if d1.year == d2.year and d1.month == d2.month:
        return f"{d1.day}–{d2.day} {_RO_MONTHS[d1.month - 1]} {d1.year}"
    if d1.year == d2.year:
        return (
            f"{d1.day} {_RO_MONTHS[d1.month - 1]} – {d2.day} {_RO_MONTHS[d2.month - 1]} {d1.year}"
        )
    return (
        f"{d1.day} {_RO_MONTHS[d1.month - 1]} {d1.year} – "
        f"{d2.day} {_RO_MONTHS[d2.month - 1]} {d2.year}"
    )


def format_times_line_ro(departure: datetime, return_at: datetime) -> str:
    """``🕘 Plecare: … · Întoarcere: …`` (times only, Bucharest)."""
    d1 = _bucharest_local(departure)
    d2 = _bucharest_local(return_at)
    h1 = f"{d1.hour:d}:{d1.minute:02d}"
    h2 = f"{d2.hour:d}:{d2.minute:02d}"
    return f"🕘 <b>Plecare:</b> {h1} · <b>Întoarcere:</b> {h2}"


def _route_or_destination_plain(offer: SupplierOffer) -> str | None:
    """Supplier data only: boarding stops, short_hook, or first line of marketing_summary."""
    places = parse_boarding_places(getattr(offer, "boarding_places_text", None))
    if len(places) == 2:
        return f"{places[0]} → {places[1]}"
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
            return f"Până la {n} persoane (capacitate maximă vehicul)."
        return "Întreg autocar / pachet grup (capacitate conform vehiculului)."
    if n > 0:
        return f"Până la {n} locuri în cadrul excursiei (în limita disponibilității)."
    return "Capacitate în funcție de disponibilitate (se verifică în bot și în aplicație)."


def _full_bus_individual_seats_line_html() -> str:
    return "ℹ️ <i>Locurile individuale nu se vând separat.</i>"


def _price_and_vehicle_lines_html(offer: SupplierOffer) -> list[str]:
    """Price row + FULL_BUS Format or PER_SEAT Transport (supplier fields only)."""
    out: list[str] = []
    vehicle = ((offer.vehicle_label or "").strip() or (getattr(offer, "transport_notes", None) or "").strip())

    if offer.base_price is not None and (offer.currency or "").strip():
        cur = (offer.currency or "").strip()
        p_esc = html.escape(str(offer.base_price))
        c_esc = html.escape(cur)
        if offer.sales_mode == TourSalesMode.FULL_BUS:
            out.append(f"💰 <b>Preț:</b> {p_esc} {c_esc} / grup")
        else:
            out.append(f"💰 <b>Preț:</b> orientativ de la {p_esc} {c_esc}")

    if offer.sales_mode == TourSalesMode.FULL_BUS:
        if vehicle:
            out.append(f"🚌 <b>Format:</b> {html.escape(vehicle[:400])} — întreg pentru grup")
        else:
            out.append("🚌 <b>Format:</b> autocar întreg (pachet grup)")
    elif vehicle:
        out.append(f"🚐 <b>Transport:</b> {html.escape(vehicle[:400])}")

    return out


def _program_lines_html(offer: SupplierOffer) -> list[str]:
    rows = _split_bullet_lines(getattr(offer, "program_text", None))
    if not rows:
        return []
    lines = ["🗺️ <b>Program:</b>"]
    lines.extend(f"• {html.escape(row)}" for row in rows)
    lines.append("")
    return lines


def _include_exclude_sections_html(
    offer: SupplierOffer,
    *,
    composition: SupplierServiceComposition,
) -> tuple[list[str], list[str]]:
    """
    HTML bullet lines under ✅ Include / ❌ Nu include.
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
    """Branded Romanian Telegram HTML sections (facts + upsell); no CTAs."""
    title_esc = html.escape((offer.title or "").strip() or "Ofertă")
    lines: list[str] = [f"🚌 <b>{title_esc}</b>", ""]

    hook_raw = _marketing_hook(offer.description)
    if hook_raw:
        lines.extend([html.escape(hook_raw), ""])

    route = _route_or_destination_plain(offer)
    if route:
        lines.append(f"📍 <b>Ruta:</b> {html.escape(route)}")

    period_txt = format_date_range_compact_ro(offer.departure_datetime, offer.return_datetime)
    lines.append(f"📅 {html.escape(period_txt)}")
    lines.append("")
    lines.append(format_times_line_ro(offer.departure_datetime, offer.return_datetime))
    lines.append("")

    lines.extend(_program_lines_html(offer))

    pv = _price_and_vehicle_lines_html(offer)
    if pv:
        lines.extend(pv)
        lines.append("")

    lines.append(f"👥 <b>Capacitate:</b> {html.escape(_capacity_line_plain(offer))}")
    lines.append("")

    if offer.sales_mode == TourSalesMode.FULL_BUS:
        lines.append(_full_bus_individual_seats_line_html())
        lines.append("")

    inc_lines, exc_lines = _include_exclude_sections_html(offer, composition=offer.service_composition)
    if inc_lines:
        lines.append("✅ <b>Include:</b>")
        lines.extend(inc_lines)
        lines.append("")
    if exc_lines:
        lines.append("❌ <b>Nu include:</b>")
        lines.extend(exc_lines)
        lines.append("")

    lines.append(html.escape(_CUSTOM_REQUEST_UPSELL))
    return lines


def _cta_block_html(*, offer_id: int, settings: Settings) -> str | None:
    """One line: Detalii → bot ``supoffer_<id>`` | Rezervă → Mini App landing."""
    uname = (settings.telegram_bot_username or "").strip().lstrip("@")
    mini_base = (settings.telegram_mini_app_url or "").strip().rstrip("/")
    segments: list[str] = []

    if uname:
        bot_url = html.escape(private_bot_deeplink(bot_username=uname, offer_id=offer_id))
        segments.append(f'ℹ️ <a href="{bot_url}">{html.escape(_CTA_DETAILS_LABEL)}</a>')
    if mini_base:
        mini_url = html.escape(mini_app_supplier_offer_url(mini_app_url=mini_base, offer_id=offer_id))
        segments.append(f'✅ <a href="{mini_url}">{html.escape(_CTA_RESERVE_LABEL)}</a>')

    if not segments:
        return None
    return " | ".join(segments)


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
