"""Deep links for published supplier offers (private bot /start payload)."""

from __future__ import annotations

import re

START_PAYLOAD_SUP_OFFER_PREFIX = "supoffer_"
STARTAPP_TOUR_PREFIX = "tour_"

# Telegram ``startapp`` payload: letters, digits, ``_`` and ``-`` only (no raw ``/``).
_STARTAPP_TAIL_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Inline Mini App slug in ``t.me/{bot}/{short}?startapp=…`` (B15C5); same charset, no URL metacharacters.
_MINI_APP_SHORT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def normalize_telegram_mini_app_short_name_for_url(raw: str | None) -> str | None:
    """Return validated short name or ``None``.

    Invalid non-empty values are ignored (fall back to bare ``?startapp=``) so misconfiguration does not break CTAs.
    """
    s = (raw or "").strip()
    if not s:
        return None
    if not _MINI_APP_SHORT_NAME_RE.fullmatch(s):
        return None
    return s


def supplier_offer_start_payload(offer_id: int) -> str:
    return f"{START_PAYLOAD_SUP_OFFER_PREFIX}{int(offer_id)}"


def parse_supplier_offer_start_arg(raw_start: str | None) -> int | None:
    """Return offer id if ``raw_start`` is ``supoffer_<id>`` (Telegram /start arg)."""
    if raw_start is None:
        return None
    s = raw_start.strip()
    if not s.startswith(START_PAYLOAD_SUP_OFFER_PREFIX):
        return None
    tail = s.removeprefix(START_PAYLOAD_SUP_OFFER_PREFIX)
    if not tail.isdigit():
        return None
    return int(tail)


def private_bot_deeplink(*, bot_username: str, offer_id: int) -> str:
    uname = bot_username.strip().lstrip("@")
    if not uname:
        raise ValueError("bot_username is required")
    payload = supplier_offer_start_payload(offer_id)
    return f"https://t.me/{uname}?start={payload}"


def mini_app_supplier_offer_url(*, mini_app_url: str, offer_id: int) -> str:
    base = mini_app_url.strip().rstrip("/")
    if not base:
        raise ValueError("mini_app_url is required")
    return f"{base}/supplier-offers/{int(offer_id)}"


def mini_app_tour_detail_url(*, mini_app_url: str, tour_code: str) -> str:
    """B11: `{base}/tours/{tour_code}` — client-side Mini App route (align with `MiniAppTourDetailService`)."""
    base = mini_app_url.strip().rstrip("/")
    tc = (tour_code or "").strip()
    if not base:
        raise ValueError("mini_app_url is required")
    if not tc:
        raise ValueError("tour_code is required")
    return f"{base}/tours/{tc}"


def mini_app_tour_channel_startapp_url(
    *,
    bot_username: str,
    tour_code: str,
    mini_app_short_name: str | None = None,
) -> str:
    """B15C1 / B15C5: open the Mini App in Telegram WebApp context with a ``startapp`` payload.

    When ``mini_app_short_name`` is set (BotFather inline app slug), URL is
    ``https://t.me/{bot}/{short}?startapp=tour_{code}`` so clients open the app directly.
    Otherwise ``https://t.me/{bot}?startapp=tour_{code}``.

    Channel HTML cannot use ``WebAppInfo``; plain ``https`` Mini App host URLs stay as HTTPS fallback only.
    """
    uname = bot_username.strip().lstrip("@")
    tc = (tour_code or "").strip()
    if not uname or "/" in uname or "?" in uname or "&" in uname:
        raise ValueError("bot_username is required and must be a single safe path segment")
    if not tc:
        raise ValueError("tour_code is required")
    if not _STARTAPP_TAIL_RE.fullmatch(tc):
        raise ValueError("tour_code must match Telegram startapp charset (A-Z, a-z, 0-9, _, -)")
    base = f"https://t.me/{uname}"
    sn = (mini_app_short_name or "").strip()
    if sn:
        if not _MINI_APP_SHORT_NAME_RE.fullmatch(sn):
            raise ValueError("mini_app_short_name must match Telegram inline app charset (A-Z, a-z, 0-9, _, -)")
        base = f"{base}/{sn}"
    return f"{base}?startapp={STARTAPP_TOUR_PREFIX}{tc}"
