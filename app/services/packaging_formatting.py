"""B4.1 / B4.2: human-readable deterministic packaging (no new facts, no AI, no publish)."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# --- English month names (marketing_summary / tooltips; stable for tests) ---
_MONTHS_EN: tuple[str, ...] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

LB_DEPARTURE = "Departure"
LB_RETURN = "Return"
LB_PRICE = "Price"
LB_SEATS = "Seats"
LB_SALES = "Sales"
LB_PAYMENT = "Payment"
LB_ROUTE = "Route"
LB_INCLUDES = "Includes"
LB_NOT_INCLUDED = "Not included"


def parse_snapshot_datetimes(
    departure_iso: str, return_iso: str
) -> tuple[datetime, datetime] | None:
    """Parse ISO strings from :class:`PackagingFactSnapshot` for formatting."""
    try:
        d1 = _parse_one_iso(departure_iso)
        d2 = _parse_one_iso(return_iso)
        return d1, d2
    except (ValueError, TypeError, OverflowError):
        return None


def _parse_one_iso(s: str) -> datetime:
    if not s or not str(s).strip():
        raise ValueError("empty iso")
    raw = str(s).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    return datetime.fromisoformat(raw)


def format_date_range_pretty(dep: datetime, ret: datetime) -> str:
    """e.g. '10–12 May 2026' or '10 May 2026' (same day). No ISO timestamps."""
    a, b = dep.date(), ret.date()
    if a == b:
        return _format_day_month_year_en(a)
    y1, m1, d1_ = a.year, a.month, a.day
    y2, m2, d2_ = b.year, b.month, b.day
    if y1 == y2 and m1 == m2:
        return f"{d1_}–{d2_} {_MONTHS_EN[m1 - 1]} {y1}"
    if y1 == y2:
        return f"{d1_} {_MONTHS_EN[m1 - 1]} – {d2_} {_MONTHS_EN[m2 - 1]} {y1}"
    return f"{_format_day_month_year_en(a)} – {_format_day_month_year_en(b)}"


def _format_day_month_year_en(d: date) -> str:
    return f"{d.day} {_MONTHS_EN[d.month - 1]} {d.year}"


def format_time_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def format_departure_time_line(dt: datetime) -> str:
    return f"🕒 {LB_DEPARTURE}: {format_time_hhmm(dt)}"


def format_return_time_line(dep: datetime, ret: datetime) -> str:
    t = format_time_hhmm(ret)
    if ret.date() == dep.date():
        return f"🕒 {LB_RETURN}: {t}"
    return f"🕒 {LB_RETURN}: {t} · {_format_day_month_year_en(ret.date())}"


# B4.2: Romanian time lines for Telegram template
def format_departure_time_line_ro(dt: datetime) -> str:
    return f"🕒 Plecare: {format_time_hhmm(dt)}"


def format_return_time_line_ro(dep: datetime, ret: datetime) -> str:
    t = format_time_hhmm(ret)
    if ret.date() == dep.date():
        return f"🕒 Intoarcere: {t}"
    return f"🕒 Intoarcere: {t} · {_format_day_month_year_en(ret.date())}"


def format_price_for_display(
    base_price: str | None, currency: str | None, *, missing_placeholder: str
) -> str:
    if base_price is None or not str(base_price).strip():
        return missing_placeholder
    cur = (currency or "").strip()
    s = str(base_price).strip()
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return f"{s} {cur}".strip() if cur else s
    dec_str = _decimal_trim(d)
    return f"{dec_str} {cur}".strip() if cur else dec_str


def _decimal_trim(d: Decimal) -> str:
    t = d.normalize()
    s = format(t, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def format_seats_count(n: int, *, not_confirmed: str) -> str:
    if n > 0:
        return str(n)
    return not_confirmed


def label_tour_sales_mode(raw: str) -> str:
    v = (raw or "").strip().lower()
    if v == "per_seat":
        return "Per seat"
    if v == "full_bus":
        return "Full bus"
    return raw or "—"


def label_supplier_payment_mode(raw: str) -> str:
    v = (raw or "").strip().lower()
    if v == "platform_checkout":
        return "Platform checkout"
    if v == "assisted_closure":
        return "Reservation / pay at boarding"
    return raw or "—"


def format_sales_and_payment_pretty(sales_mode: str, payment_mode: str) -> str:
    return f"{LB_SALES}: {label_tour_sales_mode(sales_mode)} · {LB_PAYMENT}: {label_supplier_payment_mode(payment_mode)}"


def format_commercial_summary_prose(sales_mode: str, payment_mode: str) -> str:
    """
    B4.3: human commercial intent for admin marketing blocks — no raw enum values,
    no 'Sales: Full bus' style labels.
    """
    sm = (sales_mode or "").strip().lower()
    pm = (payment_mode or "").strip().lower()
    if sm == "per_seat":
        comm = "Pretul afisat este per persoana (nu inventar live in acest pas)."
    elif sm == "full_bus":
        comm = "Pretul afisat este pentru intregul autobuz; capacitatea nu este disponibilitate live in acest pas."
    else:
        comm = "Mod comercial: verificati oferta sursa."
    if pm == "platform_checkout":
        pl = "Plata poate fi gestionata prin platforma, conform setarilor la publicare."
    elif pm == "assisted_closure":
        pl = "Rezervare / plata pot fi finalizate la imbarcare sau prin echipa, conform politicii."
    else:
        pl = "Mod plata: verificati oferta sursa."
    return f"{comm} {pl}"


def narrative_for_telegram_footer(
    description: str,
    program_text: str | None,
    transport_notes: str | None,
) -> str:
    """
    B4.3: avoid duplicating the route or full description that already appears in Traseu / program block.
    """
    d = (description or "").strip()
    if not d:
        return ""
    if not (program_text or "").strip():
        return ""
    if (transport_notes or "").strip():
        return _clip(strip_iso_timestamps_for_display(d), 1500)
    parts = d.split("\n", 1)
    if len(parts) == 2:
        return _clip(strip_iso_timestamps_for_display(parts[1].strip()), 1500)
    return ""


def format_route_pretty(text: str | None) -> str | None:
    if not (text or "").strip():
        return None
    t = " ".join(str(text).split())
    if "→" in t:
        return t
    for sep in (";", " — ", " - "):
        if sep in t:
            parts = [p.strip() for p in t.split(sep) if p.strip()]
            if len(parts) > 1:
                return " → ".join(parts)
    if "," in t:
        parts = [p.strip() for p in t.split(",") if p.strip()]
        if len(parts) > 1 and max(len(p) for p in parts) <= 64:
            return " → ".join(parts)
    return t


def pick_route_source_for_telegram(
    description: str, program_text: str | None, transport_notes: str | None
) -> str | None:
    """
    B4.2: route for marketing = supplier route facts, not boarding list.
    Priority: transport_notes, then first line of description, then program (first line).
    """
    tn = (transport_notes or "").strip()
    if tn:
        return tn
    d = (description or "").strip()
    if d:
        first = d.split("\n", 1)[0].strip()
        if len(first) > 400:
            return first[:400] + "…"
        return first
    p = (program_text or "").strip()
    if p:
        return p.split("\n", 1)[0].strip()[:500]
    return None


def format_route_for_telegram(
    description: str, program_text: str | None, transport_notes: str | None
) -> str | None:
    raw = pick_route_source_for_telegram(description, program_text, transport_notes)
    if not raw:
        return None
    return format_route_pretty(raw) or None


def _seats_mentioned_in_vehicle(vehicle_label: str | None, seats: int) -> bool:
    if not vehicle_label or seats <= 0:
        return False
    s = str(vehicle_label)
    return str(seats) in s


def format_vehicle_block_ro(
    sales_mode: str, vehicle_label: str | None, seats_total: int
) -> str:
    v = (vehicle_label or "").strip()
    st = int(seats_total) if seats_total and seats_total > 0 else 0
    sm = (sales_mode or "").strip().lower()
    if sm == "full_bus":
        line = f"🚍 {v}" if v else "🚍 Microbuz / autocar"
        if st and not _seats_mentioned_in_vehicle(vehicle_label, st):
            # B4.3: capacity of vehicle/offer, not "live available seats"
            return f"{line} (cap. max. {st} locuri, autobuz complet)"
        return line
    if v:
        return f"🚍 {v}"
    return "🚍 Transport confort"


def format_marketing_price_line_ro(
    sales_mode: str,
    base_price: str | None,
    currency: str | None,
    *,
    missing_placeholder: str,
) -> str:
    p = format_price_for_display(
        base_price, currency, missing_placeholder=missing_placeholder
    )
    if p == missing_placeholder:
        return p
    sm = (sales_mode or "").strip().lower()
    if sm == "full_bus":
        return f"💰 {p} — tot autobuzul"
    if sm == "per_seat":
        return f"👤 {p} / persoana"
    return f"💶 {p}"


def _parse_decimal_maybe(s: str | None) -> Decimal | None:
    if s is None or not str(s).strip():
        return None
    try:
        return Decimal(str(s).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def format_discount_block_lines(
    discount_percent: str | None,
    discount_amount: str | None,
    discount_code: str | None,
    discount_valid_until_iso: str | None,
    *, currency: str | None
) -> list[str]:
    """
    B4.2.1: Show code only with a real percent or amount; code alone is not customer-facing
    in the Telegram post (stays in grounding/audit only).
    """
    out: list[str] = []
    d_pct = _parse_decimal_maybe(discount_percent)
    d_amt = _parse_decimal_maybe(discount_amount)
    has_real_discount = (d_pct is not None and d_pct > 0) or (d_amt is not None and d_amt > 0)
    if d_pct is not None and d_pct > 0:
        until = ""
        dtp = parse_snapshot_datetimes(discount_valid_until_iso, discount_valid_until_iso)
        if dtp is not None:
            until = _format_day_month_year_en(dtp[0].date())
        else:
            raw = (discount_valid_until_iso or "").strip()
            if raw:
                until = _format_discount_until_fallback(raw)
        pct = _decimal_trim(d_pct)
        u = until or "—"
        out.append(f"🔥 -{pct}% pana la {u}")
    if d_amt is not None and d_amt > 0:
        cur = (currency or "").strip() or "—"
        out.append(
            f"🔥 -{_decimal_trim(d_amt)} {cur} reducere"
        )
    code = (discount_code or "").strip()
    if code and has_real_discount:
        out.append(f"🏷 Cod: {code}")
    return out


def _format_discount_until_fallback(s: str) -> str:
    p = parse_snapshot_datetimes(s, s)
    if p is not None:
        return _format_day_month_year_en(p[0].date())
    t = s.strip()
    if not _RE_ISOish.search(t):
        return t[:32]
    return "[data vezi audit]"


def build_grounding_debug_json(
    *,
    departure_iso: str,
    return_iso: str,
    sales_mode: str,
    payment_mode: str,
) -> dict[str, str]:
    return {
        "departure_iso": departure_iso,
        "return_iso": return_iso,
        "sales_mode": sales_mode,
        "payment_mode": payment_mode,
    }


_RE_ISOish = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)


def strip_iso_timestamps_for_display(s: str) -> str:
    if not s:
        return s
    return _RE_ISOish.sub("[datetime — use formatted lines above]", s)


def _clip(s: str, n: int) -> str:
    t = s.strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


# --- B4.2.1 program polish (no supplier narrative removal beyond duplicate meta-lines) ---

_RE_STRIP_LEADING_PROGRAM_LABEL = re.compile(
    r"^\s*Program:\s*",
    re.IGNORECASE | re.DOTALL,
)
_RE_INCLUS_LINE = re.compile(
    r"^\s*(?:[•\u2022\u2023]\s*|[✅\u2705]\s*)?(?:Inclus|Include|Included)\s*:",
    re.IGNORECASE,
)


def polish_program_text_for_telegram_block(program_block: str) -> str:
    """
    Remove leading "Program:" label; drop single lines that duplicate Include/Inclus/Included
    (admin/include block is the only place for inclusions in the post).
    """
    if not (program_block or "").strip():
        return ""
    s = str(program_block)
    s = _RE_STRIP_LEADING_PROGRAM_LABEL.sub("", s, count=1)
    out_lines: list[str] = []
    for line in s.splitlines():
        if _RE_INCLUS_LINE.match(line):
            continue
        out_lines.append(line)
    return "\n".join(out_lines).strip()


def _normalize_telegram_post_spacing(s: str) -> str:
    """
    At most one blank line between content (collapse 3+ newlines to 2).
    Strip stray spaces before key system emojis.
    """
    t = s.replace("\r\n", "\n")
    while "\n\n\n" in t:
        t = t.replace("\n\n\n", "\n\n")
    lines: list[str] = []
    for line in t.splitlines():
        s = line
        if s[:1] in " \t" and s.lstrip().startswith("🔒"):
            s = s.lstrip()
        lines.append(s.rstrip())
    t = "\n".join(lines)
    while "\n\n\n" in t:
        t = t.replace("\n\n\n", "\n\n")
    return t.rstrip() + "\n" if t.strip() else t


# --- B4.2 Telegram post (Romanian CTA, rule-based) ---

def _per_seat_seats_reassurance() -> str:
    return "📩 Locurile se confirma la rezervare"


def _full_bus_exclusivity_block() -> list[str]:
    return [
        "🔒 Rezervare exclusiva pentru grup (autobuz complet)",
        "🧭 Ai nevoie de alt traseu sau alt numar de locuri? Cere oferta personalizata in platforma.",
    ]


def _ctas(sales_mode: str) -> tuple[str, str, str]:
    sm = (sales_mode or "").strip().lower()
    if sm == "full_bus":
        return "👉 Rezerva pentru grupul tau", "👉 Cere oferta personalizata", "custom_secondary"
    if sm == "per_seat":
        return "👉 Rezerva locul tau", "👉 Cere oferta personalizata", "custom_secondary"
    return "👉 Cere oferta personalizata", "👉 Cere oferta personalizata", "custom_only"


def build_telegram_post_draft(
    *,
    title: str,
    description: str,
    program_text: str | None,
    transport_notes: str | None,
    dep: datetime | None,
    ret: datetime | None,
    base_price: str | None,
    currency: str | None,
    sales_mode: str,
    payment_mode: str,
    vehicle_label: str | None,
    seats_total: int,
    discount_code: str | None,
    discount_percent: str | None,
    discount_amount: str | None,
    discount_valid_until_iso: str | None,
    included: str | None,
    excluded: str | None,
    missing_price_placeholder: str,
) -> str:
    """
    B4.2 marketing template: structured Romanian Telegram draft (admin preview; not published).
    Do not use boarding_places_text for the route line (see format_route_for_telegram).
    """
    sm = (sales_mode or "").strip().lower()
    body: list[str] = [f"**{title}**", ""]
    if dep is not None and ret is not None:
        dr = format_date_range_pretty(dep, ret)
        body.append(f"🗓 {dr}")
        body.append(format_departure_time_line_ro(dep))
        body.append(format_return_time_line_ro(dep, ret))
    else:
        body.append("🗓 [Pornire/intoarcere — verifica datele]")

    price_line = format_marketing_price_line_ro(
        sm, base_price, currency, missing_placeholder=missing_price_placeholder
    )
    body.append("")
    body.append(price_line)
    d_lines = format_discount_block_lines(
        discount_percent,
        discount_amount,
        discount_code,
        discount_valid_until_iso,
        currency=currency,
    )
    for dl in d_lines:
        body.append(dl)

    body.append("")
    ve = format_vehicle_block_ro(sm, vehicle_label, seats_total)
    body.append(ve)
    if sm == "per_seat":
        body.append(_per_seat_seats_reassurance())

    route = format_route_for_telegram(description, program_text, transport_notes)
    if route:
        body.extend(["", f"🧭 Traseu: {route}"])

    # B4.2.1: no "Vanzare / Plata" in customer-facing post (stays in layout_hint.grounding_debug)
    if sm == "full_bus":
        body.append("")
        body.extend(_full_bus_exclusivity_block())
    cta1, cta2, _ = _ctas(sales_mode)
    body.append("")
    body.append(cta1)
    if cta1 != cta2:
        body.append(cta2)

    raw_prog = (program_text or "").strip() or (description or "").strip()[:2000] or "—"
    prog = polish_program_text_for_telegram_block(raw_prog) or (raw_prog if raw_prog != "—" else "—")
    if not (prog and prog.strip()):
        prog = "—"
    body.extend(["", "✨ Ce vezi:", _clip(strip_iso_timestamps_for_display(prog), 2000)])
    footer = narrative_for_telegram_footer(description, program_text, transport_notes)
    if footer:
        body.append(footer)
    if (included or "").strip():
        body.extend(["", f"✅ Include: {included.strip()}"])
    if (excluded or "").strip():
        body.extend(["", f"❌ Nu include: {excluded.strip()}"])
    return _normalize_telegram_post_spacing("\n".join(body))
