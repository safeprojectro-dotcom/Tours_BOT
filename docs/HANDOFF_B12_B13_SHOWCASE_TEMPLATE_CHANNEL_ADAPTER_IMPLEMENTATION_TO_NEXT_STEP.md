# HANDOFF_B12_B13_SHOWCASE_TEMPLATE_CHANNEL_ADAPTER_IMPLEMENTATION_TO_NEXT_STEP



Project: Tours_BOT



## Current checkpoint after B12/B13 first slice



**Implemented** (see **`CHAT_HANDOFF`**, **`app/services/supplier_offer_showcase_message.py`**):



- **`build_showcase_publication`:** refactored into **template facts** (`_template_fact_lines_html`), **CTA row** (`_cta_row_html`), **HTML assembly** (`_assemble_showcase_html`), **footer**.

- **Primary CTA:** **„Deschide în bot”** → stable **`https://t.me/<bot>?start=supoffer_<id>`** (`private_bot_deeplink`). **B11** unchanged; exact Tour routing remains in bot/Mini App.

- **Secondary CTA:** **„Vezi în aplicație”** → Mini App **`/supplier-offers/{id}`** (non-booking wording; replaces channel **„Rezervă”**).

- **Soft truth:** italic disclaimer row (availability/booking verified in app + bot); **`Preț:`** uses **„orientativ de la …”**.

- **Text-only channel send:** **`ShowcasePublication.photo_url`** is always **`None`** — **`send_showcase_publication`** therefore uses **`sendMessage`** only (**no** **`sendPhoto`** from **`showcase_photo_url`** this slice).

- **`POST /admin/supplier-offers/{id}/publish`** and **`retract_published`** orchestration unchanged (**`SupplierOfferModerationService`**).

- **Tests:** **`tests/unit/test_supplier_offer_showcase_ro.py`**, **`tests/unit/test_supplier_offer_track3_moderation.py`** updated.

- **Docs synced:** **`CHAT_HANDOFF.md`**, **`OPEN_QUESTIONS_AND_TECH_DEBT.md`**, **`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`**.



## Original goal (reference)



Safer deterministic **text-first** showcase; canonical **`supoffer_<id>`** router; no direct **`/tours/{code}`** in channel; no media expansion in slice 1.



## Boundaries (respected)



No changes to: booking/payment/order/reservation; Mini App UI; Tour activation; bridge creation semantics; **B11** routing; **B10.6** bot; **B7.4–B7.6** pipeline; automatic publication; AI final publishing.



## Still future



- **`publish_safe`**-gated **photos** / restored **`showcase_photo_url`** send when policy allows.

- B7.4 storage / Telegram getFile; B7.5 card asset; B7.6 channel media send under explicit rules.

- Direct channel → tour URL policy (product decision).

- Multilingual showcase templates.

- Admin **preview** read model before publish (**B12/B13.2** candidate).

- Channel message **edit/repost** workflow.



## Next safe options



Choose explicitly:



1. **B12/B13.2** — admin preview/read model for final channel post.

2. **B7.4** — storage/download design if media becomes priority.

3. **B7.5/B7.6** — only after storage and publish-safe asset policy.

4. **B11.2** — supplier-offer fallback landing polish.

5. **B10.7** — consultant/help/custom-trip refinement.

