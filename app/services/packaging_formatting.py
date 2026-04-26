"""B4.1: human-readable text for deterministic packaging drafts (no new facts, no AI)."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Stable neutral labels (EN) for admin review when tour language is unknown.
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


def _calendar(d: date) -> tuple[int, int, int]:
    return d.year, d.month, d.day


def format_date_range_pretty(dep: datetime, ret: datetime) -> str:
    """e.g. '10–12 May 2026' or '10 May 2026' (same day). No ISO timestamps."""
    a, b = dep.date(), ret.date()
    if a == b:
        return _format_day_month_year(a)
    y1, m1, d1_ = a.year, a.month, a.day
    y2, m2, d2_ = b.year, b.month, b.day
    if y1 == y2 and m1 == m2:
        return f"{d1_}–{d2_} {_MONTHS_EN[m1 - 1]} {y1}"
    if y1 == y2:
        return f"{d1_} {_MONTHS_EN[m1 - 1]} – {d2_} {_MONTHS_EN[m2 - 1]} {y1}"
    return f"{_format_day_month_year(a)} – {_format_day_month_year(b)}"


def _format_day_month_year(d: date) -> str:
    return f"{d.day} {_MONTHS_EN[d.month - 1]} {d.year}"


def format_time_hhmm(dt: datetime) -> str:
    """24h local/offset time of the stored instant (no T…Z)."""
    return dt.strftime("%H:%M")


def format_departure_time_line(dt: datetime) -> str:
    return f"🕒 {LB_DEPARTURE}: {format_time_hhmm(dt)}"


def format_return_time_line(dep: datetime, ret: datetime) -> str:
    t = format_time_hhmm(ret)
    if ret.date() == dep.date():
        return f"🕒 {LB_RETURN}: {t}"
    return f"🕒 {LB_RETURN}: {t} · {_format_day_month_year(ret.date())}"


def format_price_for_display(
    base_price: str | None, currency: str | None, *, missing_placeholder: str
) -> str:
    if base_price is None or not str(base_price).strip():
        return missing_placeholder
    cur = (currency or "").strip()
    s = str(base_price).strip()
    d: Decimal | None
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return f"{s} {cur}".strip() if cur else s
    dec_str = _decimal_trim(d)
    return f"{dec_str} {cur}".strip() if cur else dec_str


def _decimal_trim(d: Decimal) -> str:
    """Drop unnecessary trailing zeros: 2000.00 -> 2000, 199.5 -> 199.5."""
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


def format_route_pretty(boarding_places_text: str | None) -> str | None:
    if not (boarding_places_text or "").strip():
        return None
    t = " ".join(str(boarding_places_text).split())
    # Light readability: lists with commas/semicolons -> arrows (grounding only; no new places)
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


def build_grounding_debug_json(
    *,
    departure_iso: str,
    return_iso: str,
    sales_mode: str,
    payment_mode: str,
) -> dict[str, str]:
    """Audit: raw values for debugging; not for public Telegram copy."""
    return {
        "departure_iso": departure_iso,
        "return_iso": return_iso,
        "sales_mode": sales_mode,
        "payment_mode": payment_mode,
    }


# Avoid ISO-like substrings in user-facing marketing blocks (safety check / normalize copy)
_RE_ISOish = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)


def strip_iso_timestamps_for_display(s: str) -> str:
    """Replace any accidental ISO instants in a string with a short hint (defensive)."""
    if not s:
        return s
    return _RE_ISOish.sub("[datetime — use formatted lines above]", s)


def _clip(s: str, n: int) -> str:
    t = s.strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def build_telegram_post_draft(
    *,
    title: str,
    description: str,
    dep: datetime,
    ret: datetime,
    price_line: str,
    seats_line: str,
    sales_mode: str,
    payment_mode: str,
    route: str | None,
    included: str | None,
    excluded: str | None,
) -> str:
    """Assemble a human-readable Telegram-style block (admin preview)."""
    dr = format_date_range_pretty(dep, ret)
    body: list[str] = [
        f"**{title}**",
        "",
        f"🗓 {dr}",
        format_departure_time_line(dep),
        format_return_time_line(dep, ret),
        f"💶 {LB_PRICE}: {price_line}",
        f"👥 {LB_SEATS}: {seats_line}",
    ]
    if route:
        body.append(f"🚍 {LB_ROUTE}: {route}")
    body.append(f"🛂 {format_sales_and_payment_pretty(sales_mode, payment_mode)}")
    body.append("")
    body.append(_clip(strip_iso_timestamps_for_display(description), 1500))
    if (included or "").strip():
        body.extend(["", f"✅ {LB_INCLUDES}: {included.strip()}"])
    if (excluded or "").strip():
        body.extend(["", f"❌ {LB_NOT_INCLUDED}: {excluded.strip()}"])
    return "\n".join(body)
