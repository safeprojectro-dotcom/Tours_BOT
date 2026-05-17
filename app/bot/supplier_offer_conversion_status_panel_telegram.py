"""Format ``conversion_status_panel`` (C2B11A) for Telegram admin offer cards — plain text only."""

from __future__ import annotations

from typing import Callable

from app.bot.automation_cockpit_telegram import humanize_admin_text
from app.schemas.supplier_admin import AdminSupplierOfferConversionStatusPanelRead


def _row_key(layer: str, status: str) -> str:
    return f"admin_conversion_panel_{layer}_{status}"


def format_conversion_status_panel_for_telegram(
    panel: AdminSupplierOfferConversionStatusPanelRead,
    *,
    language_code: str | None,
    translate_fn: Callable[..., str],
    max_chars: int = 900,
) -> str:
    """Compact five-line panel — same semantics as HTTP ``conversion_status_panel``."""

    layers = (
        ("showcase", panel.showcase),
        ("tour_bridge", panel.tour_bridge),
        ("catalog", panel.catalog),
        ("booking_link", panel.booking_link),
        ("customer_action", panel.customer_action),
    )
    lines: list[str] = [translate_fn(language_code, "admin_conversion_panel_header")]
    for layer, row in layers:
        key = _row_key(layer, row.status)
        line = translate_fn(language_code, key)
        if row.detail:
            detail_h = humanize_admin_text(language_code, row.detail)
            line = f"{line}\n  · {detail_h}"
        lines.append(line)

    footer = translate_fn(language_code, "admin_conversion_panel_footer")
    body = "\n".join(lines)
    cap = max_chars - len(footer) - 2
    if len(body) > cap:
        body = body[: max(cap - 16, 0)].rstrip() + "\n…"
    return body + "\n\n" + footer


__all__ = ["format_conversion_status_panel_for_telegram"]
