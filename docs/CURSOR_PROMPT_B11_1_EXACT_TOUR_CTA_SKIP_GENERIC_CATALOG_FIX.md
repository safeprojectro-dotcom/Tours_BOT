# B11 CORRECTION — exact Tour CTA must not be followed by generic catalog overview

You are continuing the B11 implementation.

Current issue found in review:
In app/bot/handlers/private_entry.py, `/start supoffer_<id>` now resolves exact Tour routing and sends a keyboard with exact Mini App `/tours/{code}` URL, but then still calls `_send_catalog_overview(...)`.

This weakens B11 because when an exact active linked Tour exists, Telegram Bot should act as router to the exact Mini App Tour, not duplicate the generic catalog.

## Required fix

In `app/bot/handlers/private_entry.py`:

- If `nav.exact_tour_mini_app_url` and `nav.linked_tour_code` are present:
  - send the exact Tour intro and keyboard
  - do NOT call `_send_catalog_overview`
  - return from the supoffer branch safely

- If no exact Tour URL is available:
  - keep safe fallback behavior
  - generic catalog overview may remain as before

Preserve:
- `/start` generic behavior
- `/start tour_<code>` behavior
- language-selection replay
- invalid/unpublished supoffer fallback
- no booking/payment/publish/media side effects

## Docs

Add short docs update if not already done:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md if it tracks B11

Document:
- B11 exact Tour CTA uses active supplier_offer_execution_link
- exact CTA does not send generic catalog overview
- fallback still uses safe generic catalog/offer landing

## Tests

Add/update focused tests if possible:
- active linked Tour case does not trigger generic catalog overview behavior, or at least routing service / handler test confirms exact CTA path
- existing supoffer hotfix tests still pass
- B11 routing tests still pass

Run:
python -m pytest tests/unit/test_supplier_offer_bot_start_routing_b11.py -v
python -m pytest tests/unit/test_private_entry_supoffer_start_hotfix.py -v
python -m compileall app alembic -q

## Final report

Report:
1. Files changed
2. Exact change in private_entry.py
3. Whether generic catalog overview is skipped for exact Tour CTA
4. Fallback behavior unchanged
5. Tests run
6. Docs updated