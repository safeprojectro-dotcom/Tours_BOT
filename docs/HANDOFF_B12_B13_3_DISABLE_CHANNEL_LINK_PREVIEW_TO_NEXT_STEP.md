# HANDOFF_B12_B13_3_DISABLE_CHANNEL_LINK_PREVIEW_TO_NEXT_STEP



Project: Tours_BOT



## Current checkpoint after B12/B13.3



**Implemented** (see **`app/services/telegram_showcase_client.py`**, **`tests/unit/test_supplier_offer_showcase_ro.py`**):



- **`send_channel_html_message`** passes **`disable_web_page_preview: True`** by default into Telegram **`sendMessage`** (was **`False`**, which caused an automatic web preview card under the post for URLs such as the Mini App landing).

- **`send_showcase_publication`** with **`photo_url=None`** (text-only showcase path) calls **`send_channel_html_message(..., disable_web_page_preview=True)`** explicitly.

- **HTML links** in the caption (CTA **`Detalii` / `Rezervă`**, etc.) are **unchanged** — only the preview card is suppressed.

- **`sendPhoto`** / photo branch **unchanged**; no new media pipeline.



**Before B13.3:** manual channel check showed an ugly Flet/Railway preview under the Mini App link; that visual issue is addressed via Bot API without changing CTA URLs or publish flow.



## Original goal (reference)



No automatic link preview under channel showcase posts; links stay clickable; no new media behavior.



## Boundaries (still respected)



No changes to:



- booking / payment / order / reservation logic

- Mini App UI

- B11 routing, B10.6 bot behavior

- CTA destinations (Detalii → bot **`supoffer_<id>`**, Rezervă → Mini App supplier-offer landing)

- **sendPhoto** / **sendMediaGroup** / object storage / rendering

- **`SupplierOffer`** lifecycle; admin **publish** orchestration



## Follow-up options



1. B12/B13.4 — normalize RO public copy and avoid Russian raw fields in showcase.

2. B12/B13.5 — route/destination quality pass.

3. B7.4 — object storage / Telegram getFile design.

4. B12/B13 admin preview endpoint.

