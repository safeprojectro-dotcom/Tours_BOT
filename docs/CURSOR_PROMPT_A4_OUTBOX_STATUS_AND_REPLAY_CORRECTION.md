# CURSOR_PROMPT_A4_OUTBOX_STATUS_AND_REPLAY_CORRECTION

You are continuing the existing Tours_BOT project.

This is a correction to A4 before commit/push.

A4 implemented Supplier Clarification Outbox Foundation, but review found possible deviations from the A4 product contract.

## Goal

Verify and correct A4 so the internal supplier clarification outbox has:

1. Business-specific statuses.
2. No duplicate active drafts for the same supplier_offer.
3. Clear MVP scope if source_type/source_id generalization is deferred.

## Current A4 implementation report

Implemented:
- model supplier_clarification_outbox_items
- supplier_offer_id FK CASCADE
- workflow_status = open | done | dismissed
- draft_snapshot JSONB
- created_by_telegram_user_id
- API POST/list/detail
- Telegram save/list buttons
- migration 20260610_31_supplier_clarification_outbox.py

## Required correction

### 1. Status values

Replace generic workflow_status values:

- open
- done
- dismissed

with A4-specific statuses:

- draft
- ready_for_review
- cancelled
- sent_externally_later

Initial created item status must be:

- draft

For this A4 block, no send is implemented. `sent_externally_later` is only a future/manual bookkeeping status, not used by any send operation.

If changing the DB column enum/check is too invasive, report why. But prefer making this correction now before commit/push.

### 2. Replay existing active draft

The create service must not create duplicates.

For same supplier_offer_id, if an existing item has status:

- draft
- ready_for_review

then POST/save should return/replay that existing item.

Cancelled/sent_externally_later should not block creating a new draft.

If current code already does this, add/confirm tests.

### 3. Response should reveal replay

API and/or service should expose whether the item was replayed if project style allows.

Acceptable options:

- return wrapper with `item` + `replayed_existing`
- or include service result object with item/replayed_existing used by API/Telegram

Telegram confirmation:
- if newly created:
  `💾 Ciornă salvată pentru clarificare furnizor`
- if replayed:
  `ℹ️ Există deja o ciornă activă pentru această ofertă.`

### 4. MVP scope documentation

Because implementation uses supplier_offer_id FK instead of source_type/source_id, document explicitly in handoff:

- A4 MVP supports supplier_offer only.
- Future general source_type/source_id outbox can be added later if needed.
- This is acceptable because A4 button is only shown on supplier-offer cards.

Do not add tour/custom_request support in this correction.

## Safety boundaries

Do NOT:
- send messages
- publish Telegram channel messages
- add scheduler
- call AI
- call external providers
- change Layer A
- change B11
- mutate supplier offers/tours/orders/payments/reservations
- execute prepare_conversion_chain

Only internal outbox persistence/status/replay/API/Telegram copy/tests/docs.

## Expected files

Likely:
- app/models/supplier_clarification_outbox.py
- alembic/versions/20260610_31_supplier_clarification_outbox.py
- app/schemas/supplier_clarification_outbox.py
- app/services/supplier_clarification_outbox_service.py
- app/repositories/supplier_clarification_outbox.py
- app/api/routes/admin.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/messages.py
- tests/unit/test_supplier_clarification_outbox_api.py
- tests/unit/test_automation_cockpit_telegram.py
- docs/HANDOFF_A4_SUPPLIER_CLARIFICATION_OUTBOX_FOUNDATION.md

## Tests

Add/update tests:

1. POST creates status draft.
2. Second POST for same supplier_offer_id replays active draft, does not create duplicate.
3. Existing ready_for_review also replays.
4. Existing cancelled does not block new draft.
5. Existing sent_externally_later does not block new draft.
6. Telegram save callback shows replay message if active item exists.
7. No Send/Publish/Schedule buttons.

Run:

```bash
python -m compileall app tests
python -m pytest tests/unit/test_supplier_clarification_outbox_api.py -q
python -m pytest tests/unit/test_automation_cockpit_telegram.py -q
python -m pytest tests/unit/test_admin_automation_cockpit.py -q