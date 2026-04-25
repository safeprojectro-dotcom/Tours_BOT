# HANDOFF_Y32_9_OPERATOR_LINK_TOUR_SELECTION_ACCEPTED

## Scope
Y32.9 — Telegram admin compatible tour selection UI for supplier_offer_execution_links.

## What was implemented
Telegram admin flow now supports compatible tour selection for execution link create/replace:

/admin_published -> offer detail -> Execution link -> Create/Replace execution link

## Verified behavior

### Compatible list
- Replace execution link opens a compatible tour list.
- List filters by supplier_offer.sales_mode.
- Candidate card shows:
  - tour id
  - tour code
  - title
  - status
  - sales_mode
  - departure
  - seats available/total
  - Mini App CTA warning

### Selection
- Selecting compatible tour opens confirmation screen.
- Confirmation screen shows offer/tour sales_mode, target tour status, seats, and CTA warning.

### Replace
- Confirm replace succeeds.
- Previous active link is closed as replaced.
- Exactly one active link remains.
- Status/history refresh correctly.

### Regression fixed
- BUTTON_DATA_INVALID was fixed by compact callback_data:
  - el:list:{offer_id}:{mode}:{page}
  - el:pick:{offer_id}:{mode}:{tour_id}
  - el:manual:{offer_id}:{mode}

## Safety preserved
- No auto-tour creation.
- supplier_offer != tour.
- One active link per offer.
- sales_mode compatibility remains enforced.
- Mini App remains read-only consumer of execution truth.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No migrations.

## Manual smoke evidence
- Offer #5 active link to tour #3.
- Compatible list displayed tour #3.
- Selecting tour #3 opened confirmation.
- Confirm replace succeeded.
- UI showed active link and history after replace.

## Postponed
- Bounded search by tour code/title/date.
- Better operator filtering.
- Multi-page stress test with more tour candidates.

## Status
ACCEPTED — safe to proceed to Y33 bounded search/refinement.