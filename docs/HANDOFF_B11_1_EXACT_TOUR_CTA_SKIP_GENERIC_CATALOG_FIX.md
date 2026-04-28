# HANDOFF_B11_1_EXACT_TOUR_CTA_SKIP_GENERIC_CATALOG_FIX

Project: Tours_BOT

## Current checkpoint

B11 Supplier Offer deep-link routing has been implemented and deployed.

Commit:

- b29d7e4 — feat: route supplier offer deep links to exact tours

Production smoke passed:

- Backend `/health` -> ok
- Backend `/healthz` -> ready
- Mini App UI -> HTTP 200

## What B11 implemented

`/start supoffer_<id>` no longer routes only to the generic catalog when a safe exact Tour target exists.

Current behavior:

- Published SupplierOffer is resolved.
- Active `supplier_offer_execution_links` row is used as the source of truth.
- If linked Tour is `OPEN_FOR_SALE` and customer-visible:
  - bot sends short supplier-offer intro;
  - bot provides exact Mini App WebApp CTA:
    `{TELEGRAM_MINI_APP_URL}/tours/{tour_code}`;
  - bot does **not** send generic catalog overview after exact Tour CTA.
- If no active execution link exists:
  - safe fallback remains.
- If linked Tour is draft / not open_for_sale / not customer-visible:
  - no exact Tour CTA is sent.
- Invalid/unpublished/rejected SupplierOffer keeps safe fallback behavior.

## B11.1 correction

B11.1 fixed the important UX issue:

- exact Tour CTA path now returns early;
- `_send_catalog_overview(...)` is skipped when `exact_tour_mini_app_url` and `linked_tour_code` are present;
- fallback cases still use generic catalog behavior.

## Source of truth

B11 routing uses:

- `supplier_offer_execution_links` active row

B11 does **not** infer routing from:

- `SupplierOfferTourBridge` alone
- B8 recurrence-generated Tours
- title/date matching
- AI packaging metadata
- latest Tour row

## Architecture preserved

- Telegram Bot remains router / consultant / entry point.
- Mini App remains execution truth and conversion.
- Supplier Offer remains source facts.
- Tour remains customer-facing sellable object.
- Admin remains final decision maker.
- AI does not create, activate, or route Tours.
- `visibility != bookability` remains preserved.

## Not changed

B11 did not implement:

- Telegram channel publishing
- channel post editing
- media/photo posting
- sendPhoto/sendMediaGroup
- B7.4/B7.5/B7.6 media storage/render/publish
- B10.6 full bot router redesign
- B12/B13 template/channel adapters
- SupplierOfferTourBridge creation
- Tour activation
- booking/payment/order/reservation changes
- Mini App UI changes
- B8 recurrence changes

## Tests passed

- `tests/unit/test_supplier_offer_bot_start_routing_b11.py`
- `tests/unit/test_private_entry_supoffer_start_hotfix.py`
- `python -m compileall app alembic -q`

## Next safe options

Choose explicitly:

1. B10.6 — Telegram bot router/consultant redesign.
2. B12/B13 — marketing template library / channel adapters.
3. B7.4 — object storage / Telegram getFile design if media becomes priority.
4. B7.3C — admin read visibility for `publish_safe` metadata.
5. B11.2 — supplier-offer fallback landing polish if real UX testing shows gaps.

Do not start next step automatically.