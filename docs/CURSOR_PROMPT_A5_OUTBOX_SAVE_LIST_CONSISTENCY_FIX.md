# CURSOR_PROMPT_A5_OUTBOX_SAVE_LIST_CONSISTENCY_FIX

You are continuing the existing Tours_BOT project.

This is a bugfix for A5 after Railway deployment and Telegram UAT.

## Observed UAT bug

In Telegram cockpit supplier-offer card:

1. Admin clicks:
   `💾 Salvează clarificare (outbox intern)`

2. Bot shows toast:
   `ℹ️ Există deja o ciornă activă pentru această ofertă.`

3. Admin clicks:
   `📋 Outbox clarificări (această ofertă)`

4. Bot shows:
   `Outbox clarificări — ofertă #1`
   `Încă nu există înregistrări.`

This is inconsistent.

If an active draft exists for this offer, the outbox list for the same offer must show it.

## Goal

Fix consistency between:

- Telegram save clarification callback
- Telegram outbox list callback
- repository/service list filtering
- API list if same issue exists

## Required behavior

For the same supplier_offer_id:

1. If save creates a new item:
   - outbox list must show that item.

2. If save replays an existing active item:
   - outbox list must show that existing item.

3. If outbox list says no records:
   - save must not claim an active draft exists for that same offer.

4. Save and list callbacks must encode/decode the same supplier_offer_id.

5. Tests must prove save/list consistency.

## Debug checklist

Inspect:

- app/bot/constants.py
- app/bot/automation_cockpit_telegram.py
- app/bot/handlers/automation_cockpit_admin.py
- app/services/supplier_clarification_outbox_service.py
- app/repositories/supplier_clarification_outbox.py
- app/api/routes/admin.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_supplier_clarification_outbox_api.py

Specifically verify:

1. Callback payload for save:
   - what exact supplier_offer_id is encoded?
   - callback prefix?
   - parser?

2. Callback payload for list:
   - what exact supplier_offer_id is encoded?
   - callback prefix?
   - parser?

3. Save handler:
   - what ID is passed to create/upsert?
   - is it supplier_offer_id or card/source id?

4. List handler:
   - what ID is passed to list?
   - does it filter by supplier_offer_id?
   - does it accidentally filter by workflow_status or source_id incorrectly?

5. Repository:
   - does list_by_supplier_offer include all statuses?
   - does it exclude draft/ready_for_review by mistake?

6. API:
   - does GET /admin/supplier-clarification-outbox?supplier_offer_id=1 return the item after POST?

## Expected likely fix

Do not guess. Inspect code first.

Possible fixes may include:

- unify callback payload source id
- ensure both callbacks use supplier_offer_id, not card.source_id if source type differs
- fix list repository filter
- fix status filter
- fix service replay query
- fix Telegram list handler

## Required tests

Add/extend tests:

### Telegram-level test

A supplier-offer card with clarification draft:

- renders save callback and list callback with same supplier_offer_id.
- save callback calls service with supplier_offer_id X.
- list callback calls list service/repository with supplier_offer_id X.

### API/service consistency test

- POST create/upsert for supplier_offer_id X.
- GET list?supplier_offer_id=X returns exactly that item.
- Second POST returns replayed_existing=true.
- GET list?supplier_offer_id=X still returns the same item.
- No duplicate active draft.

### Status list test

Ensure list for supplier_offer_id includes items in statuses:

- draft
- ready_for_review
- cancelled
- sent_externally_later

or if product decides to show only active statuses in Telegram, then the copy must clearly say active-only. Preferred for A5: show all items for this offer, newest first.

## Safety boundaries

Do NOT:
- send supplier messages
- publish Telegram channel messages
- schedule anything
- call AI
- call external providers
- change Layer A
- change B11
- change booking/payment/order/reservation logic
- create supplier execution links
- execute prepare_conversion_chain

This is only Telegram/API/repository/service consistency.

## Migration

Do not add migration unless absolutely necessary.
This should likely be code/test only.

## Tests to run

```bash
python -m compileall app tests
python -m pytest tests/unit/test_supplier_clarification_outbox_api.py -q
python -m pytest tests/unit/test_automation_cockpit_telegram.py -q
python -m pytest tests/unit/test_admin_automation_cockpit.py -q