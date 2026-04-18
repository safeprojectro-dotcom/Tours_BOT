Implement **Track 5b.2 — RFQ Bridge Execution Entry (Preparation + Existing Hold for Eligible Tours)**.

Do not introduce new payment behavior or parallel booking semantics.

## Preconditions already completed
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 3.1 — Romanian showcase/template polish
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 design gate decided:
  - execution must be explicit
  - first Layer A entry should reuse existing preparation flow
  - TourSalesModePolicyService is mandatory
  - `full_bus` must not silently become self-serve
  - no new payment path in the first slice

## Critical rule
This track may connect an RFQ bridge to **existing Layer A preparation and temporary reservation behavior** only for execution-eligible tours.

It must NOT:
- create a new payment path
- bypass TourSalesModePolicyService
- silently start execution on winner selection or bridge creation
- enable self-serve full-bus execution

## Goal
Allow an explicit RFQ bridge execution entry that:
- validates bridge + user + linked Tour
- applies TourSalesModePolicyService
- for eligible `per_seat` self-service paths, reuses existing preparation + temporary reservation behavior
- for non-self-service paths (including `full_bus`), returns assisted/blocked execution behavior without hold/payment

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required scope

### A. Explicit execution entry
Add one explicit execution entrypoint for a bridge.

Recommended direction:
- customer-facing or customer-context execution entry from an active bridge
- must not run as a side effect of Track 5a or 5b.1 create/patch actions

You may use one or both of:
- bridge read/continue route
- bridge-based preparation route
- bridge-based reservation creation route

But keep the scope minimal and coherent.

### B. Bridge eligibility validation
Before execution begins, require:
- active bridge exists
- bridge has a linked `tour_id`
- request / selected response / bridge still valid
- bridge user/customer context resolves correctly
- Tour still passes execution-time checks
- no hidden fallback to stale/invalid Tour

### C. Mandatory sales_mode policy gate
Before any hold/reservation call:
- call `TourSalesModePolicyService` (or the exact approved equivalent already used in the project)
- if self-service is allowed (`per_seat` path), continue
- if self-service is NOT allowed (including `full_bus`), do NOT create hold/reservation

For blocked paths, return a safe assisted/blocked result consistent with current product rules.

### D. Reuse existing preparation behavior
For eligible self-service execution:
- reuse existing preparation logic rather than inventing a second preparation model
- boarding points / seat options / summary should behave consistently with existing Layer A flow

### E. Reuse existing temporary reservation behavior
For eligible self-service execution:
- after valid preparation, reuse the existing temporary reservation path
- do not fork a second reservation engine
- do not create payment sessions in this track

### F. Minimal bridge status progression
If needed, add only the minimum bridge status/progress update required to reflect that execution was entered or prepared.
Do not invent a large workflow engine.

### G. Customer-facing UX result
For eligible self-service per-seat bridge:
- customer can continue into booking preparation
- and then create a temporary reservation via the existing path

For blocked/non-self-service bridge:
- customer receives an assisted/blocked message/result
- no hold is created
- no payment session is opened

## Strong constraints
Do NOT implement:
- new payment provider flow
- new payment session creation outside existing Layer A path
- automatic execution on bridge create/patch
- customer self-selection among supplier responses
- `full_bus` self-serve checkout
- auto-generated Tour creation
- broad auth rewrite
- broad handoff rewrite
- marketplace redesign

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current reservation/payment services
- current Mini App booking routes
- current private bot booking routes
- current supplier publication flow
- current Track 4 request/response behavior
- current Track 5a resolution behavior
- current Track 5b.1 bridge persistence behavior
- current migrate -> deploy -> smoke discipline

## Modeling rule
Track 5b.2 must still treat Layer A as source of truth.
Marketplace code may orchestrate into Layer A; it must not reimplement Layer A booking semantics.

## Testing scope
Add focused tests for:
- explicit execution entry requires active bridge + valid linked Tour
- bridge without linked Tour is rejected
- invalid/stale Tour is rejected
- `per_seat` + self-service allowed path reaches existing preparation/temporary reservation behavior
- `full_bus` / blocked path does NOT create hold/reservation
- no payment session or payment-entry side effects occur
- Track 5a / 5b.1 regressions still pass where relevant
- no regression in normal customer booking flow

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. the exact execution entrypoint(s) you will add
4. whether hold is included in this slice or whether you stop at preparation
5. what remains explicitly postponed after 5b.2

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current bridge execution behavior now supported
6. compatibility notes against Tracks 0–5b.1
7. postponed items