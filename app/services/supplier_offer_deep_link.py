"""Deep links for published supplier offers (private bot /start payload)."""

from __future__ import annotations

START_PAYLOAD_SUP_OFFER_PREFIX = "supoffer_"


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
