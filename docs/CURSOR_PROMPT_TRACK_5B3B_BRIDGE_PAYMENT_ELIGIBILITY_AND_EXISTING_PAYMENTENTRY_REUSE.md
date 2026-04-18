Implement **Track 5b.3b — Bridge Payment Eligibility + Existing Layer A PaymentEntry Reuse**.

Do not introduce a new payment provider flow, new payment session model, or parallel payment architecture.

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
- Track 5b.3b design gate concluded:
  - bridge-backed payment must be gated by effective policy
  - payment anchor remains the existing Layer A Order
  - actual payment session creation must continue to use existing PaymentEntryService / existing payment-entry route
  - bridge is context, not wallet
  - no implicit payment opening from resolution, bridge create/patch, or preparation without valid hold

## Core principle
Supplier/admin configuration determines whether platform checkout is allowed.
Layer A Order / PaymentEntry / reconciliation remain the only payment authority.
Bridge code may gate and orchestrate into existing payment-entry, but must not create a second payment architecture.

## Critical rule
This track must add **bridge-scoped payment eligibility** and reuse the existing Layer A payment-entry path only.

It must NOT:
- create a new payment flow
- create a bridge-owned payment session
- create parallel payment rows
- bypass PaymentEntryService
- allow payment when effective policy blocks platform checkout

## Goal
Allow a bridge-backed customer with a valid held order to continue into payment only when:
- effective policy allows platform checkout
- active bridge exists and aligns with request/tour/user/order
- Layer A order is still valid for payment

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required scope

### A. Bridge payment eligibility read
Add a thin bridge-scoped payment eligibility read that answers:
- may this bridge-backed customer pay right now?
- what order_id is the payment anchor?
- if blocked, why?

Recommended direction:
- a new read route under the bridge/custom-request context
or
- additive fields on an existing bridge detail/read route

The read should return at least:
- `payment_entry_allowed`
- `order_id` (nullable when blocked)
- `effective_execution_policy`
- `blocked_code`
- `blocked_reason`

Keep the shape minimal and clear.

### B. Payment gate validation
The bridge payment gate must require all of:
- active bridge exists
- bridge is aligned with the same request
- linked `tour_id` exists and still aligns
- selected response / request / bridge are consistent
- effective policy says `platform_checkout_allowed = true`
- a valid existing held order exists
- order belongs to the same user/customer
- order.tour_id matches bridge.tour_id
- request/resolution is not external-only
- explicit customer-driven payment continuation

Fail closed if any condition does not hold.

### C. Existing Layer A payment-entry reuse
Do NOT build a second payment engine.

Recommended path:
- eligibility read returns `order_id`
- client then uses the existing:
  `POST /mini-app/orders/{order_id}/payment-entry`
- actual payment session creation stays inside existing `MiniAppBookingService.start_payment_entry` / `PaymentEntryService`

Optional delegate wrapper is acceptable only if it is a thin pass-through to the same payment-entry service path, but prefer no extra POST wrapper unless truly needed.

### D. Order selection rule
Define and implement one safe order resolution rule.

Recommended direction:
- use the explicit held order created from the bridge execution path
- do not guess among multiple orders unless the system already has a safe unambiguous mapping
- if ambiguity exists, block with a clear reason rather than guessing

Keep this conservative.

### E. No payment-side state invention
Do not create new bridge-authoritative payment states.

If needed, bridge read may expose informational hints, but:
- Order / PaymentEntry / payment rows remain authoritative
- no new bridge payment lifecycle should compete with Layer A

### F. Customer-facing behavior
For eligible bridge-backed paths:
- customer can retrieve payment eligibility
- then proceed to existing payment-entry path

For blocked paths:
- return blocked envelope / message
- no payment session is opened

Keep customer UX wiring minimal in this slice.

## Strong constraints
Do NOT implement:
- new payment provider behavior
- new payment session schema
- bridge-owned payment rows
- automatic payment open after hold
- payment initiation on bridge create/patch
- assisted/external paths entering platform payment
- broad RFQ UI redesign
- broad auth rewrite
- broad handoff rewrite

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current PaymentEntryService behavior
- current reservation/payment services
- current standard Mini App booking routes
- current private bot booking routes
- current supplier publication flow
- current Track 4 request/response behavior
- current Track 5a resolution behavior
- current Track 5b.1 bridge persistence behavior
- current Track 5b.2 bridge execution entry behavior
- current Track 5b.3a effective policy behavior
- current migrate -> deploy -> smoke discipline

## Modeling rule
Bridge payment eligibility is an orchestration/read concern.
Actual payment execution remains a Layer A concern.

Do not let bridge code become a second payment system.

## Testing scope
Add focused tests for:
- payment eligibility allowed only when effective policy allows platform checkout
- assisted/external/incomplete policy blocks payment eligibility
- missing/expired/unaligned order blocks payment eligibility
- order/user/tour/bridge alignment is enforced
- eligibility returns correct `order_id` only in safe cases
- existing `POST /mini-app/orders/{order_id}/payment-entry` remains the actual payment path
- no payment session is created by eligibility read alone
- no regression in Tracks 5b.2 / 5b.3a
- no regression in normal customer payment flow

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. the exact payment eligibility route/read shape you will add
4. how order resolution will work
5. what remains explicitly postponed after 5b.3b

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current bridge payment eligibility behavior now supported
6. how existing payment-entry is reused
7. compatibility notes against Tracks 0–5b.3a
8. postponed items