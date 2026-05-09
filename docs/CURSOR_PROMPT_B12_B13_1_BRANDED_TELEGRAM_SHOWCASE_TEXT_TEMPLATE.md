# CURSOR_PROMPT_B12_B13_1_BRANDED_TELEGRAM_SHOWCASE_TEXT_TEMPLATE

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a focused B12/B13.1 implementation step.

---

## Problem

The previous B12/B13 first slice made showcase publication safer:

- text-first
- primary CTA = bot deep link `supoffer_<id>`
- secondary CTA = soft Mini App link
- no hard “Rezervă”
- no photo/media publish

But the actual Telegram channel post still looks like a dry database-style list.

That is not enough.

The Telegram Channel is the marketing showcase. The channel post must look like a branded, readable Telegram marketing post with emoji sections, while still respecting execution truth and safety.

---

## Current checkpoint

B12/B13 first slice is completed.

Current publication behavior:

- `build_showcase_publication(...)` creates text-only Telegram HTML.
- `photo_url=None`.
- `send_showcase_publication(...)` sends text message.
- CTA:
  - primary: `Deschide în bot` -> stable `supoffer_<id>` bot deep link
  - secondary: `Vezi în aplicație` -> Mini App supplier-offer landing
- Direct `/tours/{code}` channel URL is not used.
- B11 routes `supoffer_<id>` to exact Tour if active execution link exists.
- Admin remains final publisher.

Do not undo these safety decisions.

---

## Goal

Implement a branded Romanian Telegram showcase text template.

The output must look like a real Telegram marketing/channel post, not a raw database fact sheet.

It should have:

- clean title
- route/idea hook
- date/time
- price
- transport/capacity
- included/excluded
- full_bus/per_seat-safe wording
- soft availability disclaimer
- clear CTA line

Still:

- no photo
- no sendPhoto
- no media pipeline
- no automatic publish
- no direct `/tours/{code}` channel URL
- no hard booking claim unless actionability is explicitly known
- no AI invented data

---

## Source files to inspect

Inspect before editing:

- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_deep_link.py
- app/services/telegram_showcase_client.py
- app/services/supplier_offer_moderation_service.py
- app/models/supplier.py
- app/models/enums.py
- tests/unit/test_supplier_offer_showcase_ro.py
- tests/unit/test_supplier_offer_track3_moderation.py
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

If B6 branded preview/template docs exist, inspect them too:
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md
- any docs mentioning branded telegram preview / marketing template rules / B6

---

## Required template style

Replace the current dry list with a branded Romanian Telegram HTML template.

Example target shape, adapted to actual available fields:

```html
🚌 <b>{title}</b>

📍 <b>Ruta:</b> {route_or_destination}
📅 <b>Perioada:</b> {departure} – {return}
💰 <b>Preț:</b> orientativ de la {price} {currency}
🚐 <b>Transport:</b> {vehicle_or_transport}
👥 <b>Capacitate:</b> {capacity_or_group_note}

{sales_mode_safe_line}

✅ <b>Include:</b>
• transport
• ...

ℹ️ <b>Nu include:</b>
• bilete de intrare
• cheltuieli personale

🔎 <i>Disponibilitatea și pașii pentru rezervare se verifică în aplicație și prin bot.</i>

👉 <a href="{bot_deeplink}">Deschide în bot</a>
📲 <a href="{mini_app_offer_url}">Vezi în aplicație</a>

Abonează-te la canal pentru rute noi și oferte viitoare.