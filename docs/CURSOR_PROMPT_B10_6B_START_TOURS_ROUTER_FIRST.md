# CURSOR_PROMPT_B10_6B_START_TOURS_ROUTER_FIRST

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a narrow B10.6B implementation step.

---

## Current checkpoint

B10.6 first slice is completed:

- `/start tour_<code>` now has primary exact Mini App CTA to `/tours/{tour_code}`.
- prepare/assistance behavior remains policy-gated.
- generic `/start` and `/tours` were intentionally not changed in the first slice.
- B11 `/start supoffer_<id>` exact routing remains implemented.
- B7 media and B8 recurrence lines remain closed/stable.

Recent relevant commits:
- b29d7e4 — feat: route supplier offer deep links to exact tours
- 72af8bc — docs: add B11 exact tour CTA handoff
- latest B10.6 first-slice commit should already be in main

Production smoke after B10.6 first slice passed:
- `/health` -> ok
- `/healthz` -> ready
- Mini App UI -> HTTP 200

---

## Business goal

Telegram Bot should be router / consultant / entry point, not a duplicate Mini App catalog.

Mini App remains execution truth and conversion.

This B10.6B slice should make only generic private entry points router-first:

- `/start`
- `/tours`

The bot should not automatically send the full in-chat catalog card overview for these generic entry points.

---

## Current behavior to change

Currently generic `/start` and `/tours` end in `_send_catalog_overview(...)`.

That sends:
- intro/home message;
- Mini App root button;
- in-chat filters;
- up to 3 catalog cards;
- tour callback buttons.

This duplicates Mini App catalog.

---

## Target behavior

For generic `/start` and `/tours`:

Send a short router-first message with:

1. Primary CTA: open Mini App catalog.
2. Secondary CTA: My bookings.
3. Secondary/support CTA: Help / contact / human if existing.
4. Language button may remain.
5. Optional filter buttons may remain only if already low-risk, but avoid sending tour cards automatically.

Important:

- Do not send automatic 1–3 tour card list after generic `/start`.
- Do not send automatic 1–3 tour card list after `/tours`.
- Do not break callback-based browsing if user explicitly clicks existing browse/filter buttons.
- Do not remove underlying catalog browsing handlers in this slice.
- Do not change `/start tour_<code>`.
- Do not change `/start supoffer_<id>`.

---

## Required scope

### Change only generic entry behavior

Allowed:
- introduce helper like `_send_router_home(...)`;
- or adjust `_send_catalog_overview(...)` with a flag;
- or add a separate router-first function for `/start` and `/tours`.

Preferred:
- avoid changing filtered catalog and callback browsing behavior.
- keep `_send_filtered_catalog_overview(...)` untouched unless absolutely required.

### Preserve these paths

Must remain unchanged or equivalent:

- `/start tour_<code>` exact Tour CTA from B10.6 first slice.
- `/start supoffer_<id>` exact supplier-offer routing from B11.
- language selection replay.
- invalid/unpublished supplier offer fallback.
- existing filtered catalog callbacks if user explicitly uses them.
- bookings/help commands.

---

## Copy requirements

Keep copy short and clear.

Suggested message semantics:

- “Open the Mini App to browse current tours and book safely.”
- “I can also help you find a tour or check your bookings.”
- Do not list live prices/seats in Telegram generic start.
- Do not invent availability.
- Do not create urgency.

Use existing translation system.

Add new keys only if needed.

---

## Full_bus / per_seat safety

Do not introduce full_bus/per_seat copy changes in this slice.

But ensure generic `/start` and `/tours` no longer auto-display stale or confusing full_bus catalog cards in chat.

---

## Non-goals

Do not implement:

- Mini App UI redesign
- booking/payment/order/reservation changes
- SupplierOffer/Tour creation
- Tour activation
- Telegram channel publish
- media/storage/render changes
- B7.4/B7.5/B7.6
- B12/B13 templates
- RAG/AI runtime
- group bot rewrite
- custom request marketplace redesign
- removing all catalog callbacks
- removing explicit filtered browse functionality

---

## Tests

Add/update focused tests.

Required tests:

1. Generic `/start` no longer sends automatic catalog card overview.
2. `/tours` no longer sends automatic catalog card overview.
3. Generic `/start` still sends Mini App catalog/home CTA.
4. `/tours` still sends Mini App catalog/home CTA.
5. `/start tour_<code>` exact Tour CTA still works.
6. `/start supoffer_<id>` B11 exact path still works.
7. Existing filtered catalog callback tests remain passing if present.

Run focused tests:

```bash
python -m pytest tests/unit/test_bot_private_foundation.py -v
python -m pytest tests/unit/test_private_entry_supoffer_start_hotfix.py tests/unit/test_supplier_offer_bot_start_routing_b11.py -v
python -m compileall app alembic -q