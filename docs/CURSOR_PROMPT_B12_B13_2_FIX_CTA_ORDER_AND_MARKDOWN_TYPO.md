# CURSOR_PROMPT_B12_B13_2_FIX_CTA_ORDER_AND_MARKDOWN_TYPO

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Это маленький correction step внутри B12/B13.2.

Не менять booking/payment/order/reservation logic.
Не менять Mini App UI.
Не менять B11/B10.6 routing.
Не менять media/photo/publish lifecycle.
Не менять sendPhoto/sendMediaGroup.
Не менять object storage / download / rendering.

## Current issue

B12/B13.2 implementation mostly looks correct, but review found two issues:

1. CTA links are reversed.

Current reported behavior:
- `ℹ️ Detalii` points to Mini App
- `✅ Rezervă` points to bot deep link

Required behavior:
- `ℹ️ Detalii` must point to bot deep link `supoffer_<id>`
- `✅ Rezervă` must point to Mini App supplier-offer landing

Expected HTML shape:

```html
ℹ️ <a href="{bot_deeplink}">Detalii</a> | ✅ <a href="{mini_app_offer_url}">Rezervă</a>