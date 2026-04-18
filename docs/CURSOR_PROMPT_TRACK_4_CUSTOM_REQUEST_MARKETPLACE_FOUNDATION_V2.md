Implement **Track 4 — Custom Request Marketplace Foundation** on top of the accepted Tracks 0–3.

## Preconditions already completed
- Track 0 completed: frozen core documented in `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- Track 1 completed: design package aligned and accepted
- Track 2 completed and accepted: Supplier Admin Foundation
- Track 3 completed and accepted: moderated supplier-offer publication to Telegram showcase
- current Layer A customer flows must remain stable

## Critical rule
This track must introduce a **request marketplace layer**, not replace the existing booking/order lifecycle.

A custom request is not the same thing as a normal booking order.

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Goal
Add the first structured custom-request marketplace layer:
customer creates a request -> request is visible to relevant suppliers -> suppliers can respond -> central admin can intervene.

## Required scope

### A. Custom request model
Add a minimum viable request model for:
- customer identity/context
- request type
- date or date range
- direction / destination / route notes
- group size
- special conditions
- source channel
- status

### B. Request intake
Allow request creation from:
- private bot
- Mini App support/request path

Keep this narrow and structured.

### C. Supplier visibility / response foundation
Allow suppliers to:
- list relevant requests
- open request detail
- respond in a minimal structured way
- accept / decline / submit response

### D. Central admin oversight
Allow platform admin to:
- view requests
- view supplier responses
- intervene or monitor when needed

## Strong constraints
Do not implement yet:
- auto-auction
- complex ranking
- direct whole-bus self-service
- advanced negotiation engine
- new payment rails
- replacement of current order lifecycle
- broad auth rewrite
- broad redesign of handoff
- broad redesign of group assistant

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current Mini App routes
- current private bot routes
- current `sales_mode` behavior
- current assisted full-bus path
- current supplier offer publication flow
- current migrate → deploy → smoke discipline

## Modeling rule
Do not force custom requests into `orders` if that distorts existing booking logic.
Requests must remain a separate lifecycle unless there is an explicit bridge later.

## Testing scope
Add focused tests for:
- request creation
- supplier visibility
- supplier response creation
- admin oversight visibility
- no regression in current ready-made tour flows

## Before coding
First summarize:
1. why custom request must remain separate from normal booking/order lifecycle
2. exact files/modules you plan to touch
3. whether migrations are needed
4. what remains explicitly postponed after Track 4

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current marketplace request behavior now supported
6. compatibility notes against Track 0–3
7. postponed items