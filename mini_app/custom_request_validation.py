"""Mini App: validate custom-request payload before POST and map FastAPI 422 to user copy."""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx


def validate_custom_request_form_local(
    *,
    travel_date_start: str,
    travel_date_end: str,
    route_notes: str,
    group_size_raw: str,
) -> str | None:
    """
    Returns a ui_strings shell key if invalid, else None.
    Aligns with app.schemas.custom_marketplace.MiniAppCustomRequestCreate.
    """
    start = travel_date_start.strip()
    if not start:
        return "custom_request_validation_start_date_required"
    try:
        ds = date.fromisoformat(start)
    except ValueError:
        return "custom_request_validation_start_date_invalid"
    end = travel_date_end.strip()
    if end:
        try:
            de = date.fromisoformat(end)
        except ValueError:
            return "custom_request_validation_end_date_invalid"
        if de < ds:
            return "custom_request_validation_date_order"
    route = route_notes.strip()
    if len(route) < 3:
        return "custom_request_validation_route_short"
    gs = group_size_raw.strip()
    if gs:
        try:
            n = int(gs)
        except ValueError:
            return "custom_request_validation_group_size_invalid"
        if n < 1 or n > 999:
            return "custom_request_validation_group_size_range"
    return None


def message_for_custom_request_422(exc: httpx.HTTPStatusError, lang: str | None) -> str:
    """Map FastAPI 422 response body to user-facing text (Romanian via shell)."""
    from mini_app.ui_strings import shell

    fallback = shell(lang, "custom_request_error_validation_generic")
    if exc.response is None:
        return fallback
    try:
        body = exc.response.json()
    except Exception:
        return fallback
    return format_fastapi_422_custom_request(body.get("detail"), lang)


def format_fastapi_422_custom_request(detail: Any, lang: str | None) -> str:
    """Map FastAPI/Pydantic 422 `detail` list to short user text."""
    from mini_app.ui_strings import shell

    fallback = shell(lang, "custom_request_error_validation_generic")
    if isinstance(detail, str):
        return detail
    if not isinstance(detail, list) or not detail:
        return fallback
    parts: list[str] = []
    for item in detail:
        if not isinstance(item, dict):
            continue
        loc = item.get("loc")
        loc_list: list[Any] = list(loc) if isinstance(loc, (list, tuple)) else []
        typ = str(item.get("type") or "")
        msg = str(item.get("msg") or "")
        key = _map_422_item_to_shell_key(loc_list, typ, msg)
        if key is not None:
            parts.append(shell(lang, key))
        elif msg:
            parts.append(msg)
    if not parts:
        return fallback
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return " ".join(out)


def _map_422_item_to_shell_key(loc: list[Any], typ: str, msg: str) -> str | None:
    """Return ui_strings key or None to use raw msg."""
    loc_s = [str(x).lower() for x in loc]
    joined = " ".join(loc_s)
    if "travel_date_start" in joined:
        if "missing" in typ:
            return "custom_request_validation_start_date_required"
        return "custom_request_validation_start_date_invalid"
    if "travel_date_end" in joined:
        return "custom_request_validation_end_date_invalid"
    if "route_notes" in joined:
        return "custom_request_validation_route_short"
    if "group_size" in joined:
        if "greater_than_equal" in typ or "less_than_equal" in typ:
            return "custom_request_validation_group_size_range"
        return "custom_request_validation_group_size_invalid"
    if "request_type" in joined:
        return "custom_request_validation_request_type_invalid"
    if "telegram_user_id" in joined:
        return "custom_request_validation_telegram_user_invalid"
    if loc_s == ["body"] or joined.strip() == "body":
        low = msg.lower()
        if "travel_date_end" in low and "before" in low:
            return "custom_request_validation_date_order"
        if "travel_date" in low and "before" in low:
            return "custom_request_validation_date_order"
    return None
