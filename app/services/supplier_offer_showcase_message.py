"""HTML text for moderated supplier-offer showcase posts (Telegram channel)."""

from __future__ import annotations

import html
from app.core.config import Settings
from app.models.supplier import SupplierOffer
from app.services.supplier_offer_deep_link import private_bot_deeplink


def format_supplier_offer_showcase_html(offer: SupplierOffer, settings: Settings) -> str:
    """Build channel message: facts + CTAs (bot deep link + Mini App). No booking execution."""
    title = html.escape(offer.title.strip() or "Offer")
    desc = html.escape((offer.description or "").strip()[:800])
    dep = offer.departure_datetime.strftime("%Y-%m-%d %H:%M UTC")
    ret = offer.return_datetime.strftime("%Y-%m-%d %H:%M UTC")
    price_line = ""
    if offer.base_price is not None and (offer.currency or "").strip():
        price_line = f"<b>From</b> {html.escape(str(offer.base_price))} {html.escape(offer.currency.strip())}\n"
    seats = f"<b>Capacity</b> {offer.seats_total}\n" if offer.seats_total else ""
    mode = html.escape(offer.sales_mode.value)

    lines = [
        f"<b>{title}</b>",
        "",
        desc,
        "",
        f"<b>Departure</b> {html.escape(dep)}",
        f"<b>Return</b> {html.escape(ret)}",
        price_line,
        seats,
        f"<b>Sales mode</b> {mode}",
        "",
    ]
    text = "\n".join(line for line in lines if line is not None)

    cta: list[str] = ["<b>Book or browse</b>"]
    uname = (settings.telegram_bot_username or "").strip().lstrip("@")
    if uname:
        url = html.escape(private_bot_deeplink(bot_username=uname, offer_id=offer.id))
        cta.append(f'• <a href="{url}">Open bot</a>')
    mini = (settings.telegram_mini_app_url or "").strip()
    if mini:
        safe_mini = html.escape(mini.rstrip("/"))
        cta.append(f'• <a href="{safe_mini}">Mini App (catalog)</a>')
    text += "\n" + "\n".join(cta)
    return text
