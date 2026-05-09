# HANDOFF_B10_6B_START_TOURS_ROUTER_FIRST_TO_NEXT_STEP



Project: Tours_BOT



## Current checkpoint after B10.6B



**B10.6B implemented:** generic `/start`, `/tours`, and language-confirm-without-pending-deep-link now use **`_send_router_home`** (`router_home_body` + `send_or_edit_router_home`) instead of **`_send_catalog_overview`**.



- No automatic 1–3 in-chat catalog cards on those entry paths.

- Primary WebApp CTAs for Mini App catalog root + My bookings remain on **`build_private_home_keyboard`**; filters + **Browse tours** + language unchanged for explicit in-chat browsing.

- **`/` help/contact/human** referenced in **`router_home_body`** copy (handlers unchanged).

- **`transient_messages`:** `send_or_edit_router_home` / `register_router_home_singleton`; `send_or_edit_home_catalog_pair` clears router-only home before sending a full catalog pair (so **Browse tours** does not orphan banners).



**Still in place from earlier work:**



- B10.6 first slice: `/start tour_<code>` → exact Mini App `/tours/{code}` WebApp; prepare/assistance policy-gated.

- B11: `/start supoffer_<id>` exact Tour path; invalid/unpublished fallback still uses intro + **`_send_catalog_overview`**.

- **`grp_*` / legacy group CTAs:** intro + **`_send_catalog_overview`** unchanged after B10.6B.

- Mini App = execution truth; no booking/payment code changes in B10.6B.



**Tests:** `tests/unit/test_private_entry_router_first_b10_6b.py`, extended `test_transient_messages`, `test_bot_private_foundation` + supoffer hotfix updates. **Docs:** `docs/CHAT_HANDOFF.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md` (B10.6 / B10.6B).



## Original B10.6B intent (reference)



Router-first private entry for `/start` and `/tours`; explicit filtered browsing only when the user uses filters or **Browse tours**; no automatic duplicate catalog cards.



## Preserved boundaries (unchanged by B10.6B)



- `/start tour_<code>` exact Tour CTA.

- `/start supoffer_<id>` exact supplier-offer routing.

- booking/payment/order/reservation logic.

- Mini App UI.

- Telegram channel publishing.

- media/storage/render pipeline.

- SupplierOffer/Tour creation.

- Tour activation.

- group bot rewrite.

- B12/B13 template system.



## Follow-up options



Choose explicitly:



1. **B10.6C** — full_bus/per_seat copy audit across bot messages.

2. **B11.2** — supplier-offer fallback landing polish.

3. **B12/B13** — template library / channel adapters.

4. **B7.4** — object storage / Telegram getFile design.

5. **B10.7** — help/custom-trip entry refinement if product wants consultant behavior.

