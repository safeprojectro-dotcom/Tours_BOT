# HANDOFF_B12_B13_1_BRANDED_TELEGRAM_SHOWCASE_TEXT_TEMPLATE_TO_NEXT_STEP

Project: Tours_BOT

## Current checkpoint after B12/B13.1

**Implemented** (see **`app/services/supplier_offer_showcase_message.py`**, tests **`tests/unit/test_supplier_offer_showcase_ro.py`**, **`tests/unit/test_supplier_offer_track3_moderation.py`**):

- **Branded Romanian HTML layout:** emoji-led sections (`🚌` title, optional prose hook from description; **`📍 Ruta`** from boarding / **`short_hook`** / first line of **`marketing_summary`**; **`📅 Perioada`** with Bucarest-format departure–return en-dash; **`💰 Preț`**, **`🚐 Transport`**, **`👥 Capacitate`** with **`TourSalesMode.FULL_BUS`** vs **`PER_SEAT`**-safe wording in Romanian italic snippets).

- **Include / Nu include:** prefers **`included_text`** / **`excluded_text`** bullets when present; otherwise **`SupplierServiceComposition`** defaults plus standard exclusions.

- **Disclaimer:** **`🔎`** + existing italic availability line (**„în aplicație și prin bot”**).

- **CTA:** separate **`👉`** bot (**„Deschide în bot”**, **`supoffer_<id>`**) and **`📲`** Mini App (**„Vezi în aplicație`** … **`/supplier-offers/{id}`**); no pipe-joined bold links row.

- **Unchanged:** **`photo_url=None`**; **`send_showcase_publication`** text-only; **`POST …/publish`** orchestration; no **`/tours/{code}`** in channel text.

Previously (**before B13.1**): channel body looked flat/database-like; that cosmetic gap is addressed by this slice without weakening Track 3 safety rules.

## Original goal (reference)

Marketing-style channel post with emoji structure, deterministic fields only, no invented data, no media pipeline.

## Boundaries (still respected)

No changes to:

- media/photo publishing, **sendPhoto**/sendMediaGroup, Telegram getFile/download
- object storage, card rendering (B6/B7)
- automatic publish; admin remains final publisher for channel
- direct **`/tours/{code}`** channel URL
- booking/payment/order/reservation, Mini App UI (beyond existing supplier-offer landing link)
- B11 routing, B10.6 bot behavior
- AI as final publisher

## Still future

- B7.4 object storage / Telegram getFile  
- B7.5 real rendered card asset  
- B7.6 Telegram sendPhoto/sendMediaGroup under explicit admin publish  
- admin preview endpoint  
- multilingual templates  
- channel post edit/repost workflow  
