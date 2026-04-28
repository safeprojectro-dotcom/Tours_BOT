# HANDOFF_B12_B13_2_SHOWCASE_MARKETING_COPY_POLISH_TO_NEXT_STEP

Project: Tours_BOT

## Current checkpoint after B12/B13.2

**Implemented** (see **`app/services/supplier_offer_showcase_message.py`**, **`tests/unit/test_supplier_offer_showcase_ro.py`**, **`tests/unit/test_supplier_offer_track3_moderation.py`**):

- **Period + times:** compact calendar line **`📅`** (Bucharest) + **`🕘` Plecare · Întoarcere** (time-only), replacing the older single **Perioada** long-datetime row.
- **Ruta:** two boarding stops render as **`A → B`**; three+ still use **`•`**.
- **`program_text`:** when set, **`🗺️ Program:`** with bullet lines (supplier data only).
- **FULL_BUS + price:** **`Preț: {base_price} {currency} / grup`** (no **„orientativ de la”** for that mode when price+currency are present).
- **FULL_BUS:** **`🚌 Format:`** line (vehicle or default autocar/grup) + capacity copy + **`ℹ️`** *Locurile individuale nu se vând separat.*
- **PER_SEAT:** price line remains **orientativ de la**; **🚐 Transport** when vehicle/notes exist.
- **Excluded header:** **`❌ Nu include:`** (was **`ℹ️`**).
- **Upsell:** optional custom-request messaging **`🧭 … Cere o ofertă personalizată.`** replaces the generic availability disclaimer row (text-only; no deep link in this slice).
- **CTA (one line):** **`ℹ️ Detalii`** → bot **`supoffer_<id>`** **|** **`✅ Rezervă`** → Mini App supplier-offer landing (B11 unchanged).

**Before B13.2:** structure was already improved (B13.1), but full-bus pricing and channel CTA/copy were still weak; that gap is addressed in code above without changing publish orchestration.

## Original goal (reference)

Sales-oriented polish for fixed **FULL_BUS**; stronger CTAs; program visible when data exists; **no** invented facts.

## Boundaries (still respected)

No changes to:

- booking / payment / order / reservation logic
- Mini App UI (supplier-offer landing URL target unchanged)
- B11 routing, B10.6 bot behavior
- **text-only** channel send: **no** **sendPhoto** / **sendMediaGroup**, **no** Telegram getFile/download, **no** object storage, **no** card rendering, **no** automatic publish

## Still future

- **custom request flow link** (upsell text is present; actionable link to **`/custom_request`** / Mini App route when product defines URL)
- media pipeline **B7.4** / **B7.5** / **B7.6**
- admin preview endpoint
- multilingual templates
- channel post edit / repost workflow
