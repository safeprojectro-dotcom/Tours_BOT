# HANDOFF_B10_6C_BOT_COPY_BUTTONS_FULL_BUS_AUDIT_TO_NEXT_STEP



Project: Tours_BOT



## Current checkpoint after B10.6C



**B10.6C completed** (`app/bot/messages.py` + one test assertion; **no** handler / keyboard / routing changes).



**Router-home (`router_home_body`):** Every supported language now references the same **visible** **`open_catalog`** label where the user is pointed at the short in-chat list (e.g. RO **„Vezi tururi”**, DE **„Touren ansehen”**, EN **“Browse tours”**, etc.). Opens with welcome-style lines aligned with existing **`welcome`** where useful; removed mismatched phrases (e.g. RO no longer used a non-existent „Arată lista în chat”).



**Full_bus / assisted wording:** **`assisted_booking_detail_note`** (**en**, **ro**) reframed from “automated **per-seat** …” to **self-serve / charter or whole-vehicle (autocar complet) package** framing so full_bus is not read as “individual seat selection failed.” **`catalog_card_assisted_hint`** unchanged.



**Tests:** `test_format_tour_detail_message_includes_assisted_note_for_full_bus` updated for new English strings.



**Docs synced:** `docs/CHAT_HANDOFF.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md` (B10.6C bullets).



## Stack under this handoff (unchanged logic)



- B10.6B router-first **`/start`** / **`/tours`** still in place.

- **`/start tour_<code>`**, **`/start supoffer_<id>`** (B11), explicit browse/filters — **unchanged** by B10.6C.



## Boundaries (respected in B10.6C)



No changes to:



- booking/payment/order/reservation logic  

- Mini App UI  

- Tour/SupplierOffer lifecycle  

- Telegram channel publish  

- media/storage/render pipeline  

- B11 routing  

- B7.4/B7.5/B7.6  

- B12/B13  

- RAG/AI runtime  



## Original B10.6C intent (reference)



Polish **`router_home_body`** vs buttons; safer full_bus vs per_seat **copy** only.



## Next safe options



Choose explicitly:



1. **B11.2** — supplier-offer fallback landing polish.  

2. **B12/B13** — marketing template library / channel adapters.  

3. **B7.4** — object storage / Telegram getFile design.  

4. **B10.7** — help/custom-trip consultant entry refinement.  

5. **B10.6D** — explicit browse/filter UX thinning if still needed.

