# HANDOFF_B10_6_BOT_ROUTER_CONSULTANT_IMPLEMENTATION_TO_NEXT_STEP

Project: Tours_BOT

## Current checkpoint before implementation

B10.6 design accepted.

Purpose:
Telegram Bot should act as router / consultant / entry point, not duplicate Mini App catalog.

## First implementation slice

`/start tour_<code>` now aligns with B11 router pattern.

Expected behavior after implementation:

- If user opens `/start tour_<code>` and the Tour is customer-visible:
  - bot shows Tour detail / short context as before;
  - bot provides a primary WebApp CTA to exact Mini App Tour detail:
    `{TELEGRAM_MINI_APP_URL}/tours/{tour_code}`;
  - existing policy-gated prepare/assistance behavior remains.
- Generic `/start` remains unchanged.
- `/tours` remains unchanged.
- `_send_catalog_overview` remains unchanged.
- B11 `/start supoffer_<id>` exact routing remains unchanged.

## Preserved boundaries

No changes to:

- booking/payment/order/reservation logic
- Mini App UI
- Telegram channel publish
- media/storage/render pipeline
- SupplierOffer/Tour creation
- Tour activation
- group bot rewrite
- B12/B13 templates

## Follow-up options

Choose explicitly after review:

1. B10.6B — router-first generic `/start` and `/tours` thinning.
2. B10.6C — full_bus/per_seat copy audit across bot messages.
3. B12/B13 — marketing template library / channel adapters.
4. B7.4 — object storage / Telegram getFile design.
5. B11.2 — supplier-offer fallback landing polish.