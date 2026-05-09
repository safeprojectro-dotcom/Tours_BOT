# HANDOFF_B12_B13_4_ADMIN_SHOWCASE_PREVIEW_BEFORE_PUBLISH_TO_NEXT_STEP



Project: Tours_BOT



## Current checkpoint after B12/B13.4



**Implemented** (**`GET /admin/supplier-offers/{offer_id}/showcase-preview`**, **`AdminSupplierOfferShowcasePreviewRead`**, **`SupplierOfferModerationService.showcase_preview`**):



- **Read-only** preview of the exact **`caption_html`** produced by **`build_showcase_publication`** (same as **`POST …/publish`** Telegram body).

- Response includes **`publication_mode`** (**`text_only`** \| **`photo_with_caption`**), **`showcase_photo_url`** (currently always **`None`** for default B12 pipeline), **`disable_web_page_preview`** (**true** when text-only send matches **`telegram_showcase_client`**).

- **`cta_detalii_href`** → bot **`supoffer_<id>`**; **`cta_rezerva_href`** → Mini App **`/supplier-offers/{id}`** — aligned with channel CTA order/semantics (**B13.2**).

- **`preview_notice`** bilingual reminder: nothing sent to Telegram.



**Does not:** call Telegram, mutate DB, or change **`SupplierOffer`** lifecycle (**404** if offer missing). **`ADMIN_API_TOKEN`** gate unchanged.



Tests: **`tests/unit/test_supplier_offer_track3_moderation.py`** (`test_admin_showcase_preview_*`). Docs synced: **`CHAT_HANDOFF`**, **`OPEN_QUESTIONS_AND_TECH_DEBT`**, **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN`**.



**Before B13.4:** poor raw copy could only be caught after channel publish; admins can now inspect HTML + URLs before **`publish`**.



## Original goal (reference)



Same builder as publish; zero Telegram I/O; metadata for text vs photo vs link preview.



## Boundaries (still respected)



No changes to:



- **`POST …/publish`** semantics or retract flow

- booking / payment / order / reservation

- Mini App UI

- B11 routing, B10.6 bot behavior

- Telegram media / **`sendPhoto`** / **`sendMediaGroup`** / storage / rendering

- automatic translation, AI rewrite at publish time



## Still future



- dedicated **admin UI** consuming **`showcase-preview`**

- **forced** preview-before-publish policy (workflow)

- optional **RO / public copy normalization** (e.g. B12/B13.5+)

- media pipeline **B7.4** / **B7.5** / **B7.6**

- channel **post edit / repost** workflow

