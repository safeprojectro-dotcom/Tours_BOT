Implement **Track 5c — RFQ Mini App UX Wiring for Bridge Execution and Payment Continuation**.

Do not introduce new payment provider behavior, new booking engine logic, or a second payment architecture.

## Preconditions already completed
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 3.1 — Romanian showcase/template polish
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 — explicit bridge execution entry into existing preparation/hold for eligible tours
- Track 5b.3a — supplier policy on RFQ responses + EffectiveCommercialExecutionPolicyService
- Track 5b.3b — bridge payment eligibility + existing payment-entry reuse
- smoke-tour stabilization exists and booking smoke passes
- expired tours are hidden from customer-facing catalog/read paths

## Core principle
Supplier/admin policy determines whether self-service and platform checkout are allowed.
Layer A remains the only authority for holds, orders, payment sessions, and reconciliation.
Mini App must only wire the user through already-approved backend paths.

## Critical rule
This track is **Mini App UX wiring only** for RFQ bridge-backed execution.

It must NOT:
- invent a second reservation flow
- invent a second payment flow
- create new commercial logic in UI
- bypass EffectiveCommercialExecutionPolicyService
- bypass existing Layer A payment-entry
- enable self-serve full_bus
- widen assisted/external paths into platform self-service

## Goal
Allow a customer in the Mini App to continue an RFQ-backed journey through:
1. bridge preparation
2. bridge reservation/hold
3. bridge payment eligibility
4. existing payment-entry continuation

…using the already-implemented backend/API surfaces.

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required scope

### A. Bridge-backed Mini App entry/wiring
Wire the Mini App to support an RFQ bridge-backed execution path.

Use the already existing backend endpoints for:
- bridge preparation
- bridge reservation creation
- bridge payment eligibility
- existing order payment-entry

Keep the UX coherent and minimal.

### B. Preparation screen wiring
For a bridge-backed RFQ execution:
- load bridge preparation
- show normal preparation data if self-service is allowed
- show blocked/assisted envelope if self-service is not allowed

Required outcomes:
- if `self_service_available = true`, the user can continue
- if blocked, show a clear assisted message and do not expose reserve/pay CTAs

### C. Reservation/hold wiring
When preparation is self-service-eligible:
- use the existing bridge reservation endpoint
- reuse the same seat count / boarding point UX pattern already used for Mini App booking where possible
- after successful hold, keep the order reference/order_id available in Mini App state

Do not invent a second reservation model.

### D. Payment continuation wiring
After a successful bridge-backed hold:
- call bridge payment eligibility
- if `payment_entry_allowed = true`, expose a CTA that continues into the existing payment flow for that order
- actual payment session creation must still happen only through the existing `POST /mini-app/orders/{order_id}/payment-entry`

If blocked:
- show blocked reason / assisted message
- do not expose payment CTA

### E. Existing payment screen reuse
Prefer reusing the current Mini App payment screen/pattern for order-based payment.
Do not create a separate “RFQ payment engine” in UI.

If needed, bridge-specific context can be used only for navigation and messaging, not for alternate payment semantics.

### F. Clear customer messaging
Mini App must clearly distinguish:
- self-service available
- operator assistance required
- platform checkout allowed
- payment currently blocked
- reservation active but payment unavailable
- expired/invalid state

Blocked/assisted/external states must be explicit and user-friendly.

### G. Minimal state handling
Mini App may keep only the minimum RFQ execution state needed for continuity, such as:
- request_id
- order_id after hold
- latest bridge preparation/payment eligibility result

Do not add a large client-side workflow engine.

## Strong constraints
Do NOT implement:
- new backend payment behavior
- new payment provider integrations
- new payment session models
- new booking engine logic
- bridge-owned payment execution
- customer quote comparison UI
- broad supplier/admin portal redesign
- broad auth rewrite
- broad handoff rewrite

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current PaymentEntryService behavior
- current reservation/payment services
- current standard Mini App booking/payment flow
- current private bot booking/payment flow
- current Track 5a resolution behavior
- current Track 5b.1 bridge persistence behavior
- current Track 5b.2 bridge execution behavior
- current Track 5b.3a effective policy behavior
- current Track 5b.3b payment eligibility behavior
- current migrate -> deploy -> smoke discipline

## UX expectations
Align with `docs/MINI_APP_UX.md`:
- mobile-first
- one dominant CTA at a time
- blocked states explicit
- no fake urgency
- no fake operator promise
- clear next step

### Expected CTA behavior
- self-service allowed + no hold yet → `Confirm Reservation`
- hold succeeded + payment allowed → `Continue to Payment`
- hold succeeded + payment blocked → assisted/blocked message, no pay CTA
- non-self-service path from the start → assisted/blocked message, no reserve/pay CTA

## Testing scope
Add focused tests for:
- Mini App bridge flow renders/handles preparation allowed vs blocked
- successful bridge hold stores/uses order_id correctly
- payment continuation uses payment eligibility first
- payment CTA appears only when `payment_entry_allowed = true`
- blocked assisted/external paths show safe non-payment behavior
- no regression in standard Mini App catalog/booking/payment flow
- no regression in Tracks 5b.2 / 5b.3a / 5b.3b integration assumptions

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. the exact Mini App screens/state/CTA wiring you will add
4. how existing payment screen/flow will be reused
5. what remains explicitly postponed after 5c

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current RFQ Mini App UX wiring now supported
6. how payment continuation is wired
7. compatibility notes against Tracks 0–5b.3b
8. postponed items