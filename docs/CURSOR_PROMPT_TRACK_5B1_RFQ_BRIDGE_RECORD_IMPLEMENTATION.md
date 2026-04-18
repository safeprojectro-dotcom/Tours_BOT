Implement **Track 5b.1 — RFQ Booking Bridge Record Foundation**.

Do not implement reservation holds, payment sessions, or direct order creation in this track.

## Preconditions already completed
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 3.1 — Romanian showcase template / photo-first polish
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b design gate decided:
  - explicit admin-triggered RFQ bridge
  - bridge record first
  - no automatic order creation
  - no payment in first bridge slice
  - no TemporaryReservationService call in 5b.1

## Critical rule
This track must create an explicit persisted **bridge/intention layer** between:
- a commercially resolved RFQ
and
- future Layer A booking execution

But it must NOT itself execute Layer A booking/payment rails.

## Goal
Add the minimum safe bridge artifact and admin flow needed to say:

“This request now has an execution bridge toward Layer A, optionally linked to a Tour, but no reservation/payment has started yet.”

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required scope

### A. Bridge model
Add a dedicated bridge record/table for RFQ -> booking execution intent.

Recommended naming:
- `custom_request_booking_bridges`
or another equally explicit name

Minimum fields should cover:
- request_id
- selected_supplier_response_id
- user_id
- tour_id (nullable)
- bridge_status
- optional admin note/context
- timestamps

Do not overload `orders` or `custom_marketplace_requests` with this role.

### B. Bridge status model
Add a small, explicit bridge status vocabulary, for example:
- `pending_validation`
- `ready`
- `linked_tour`
- `customer_notified`
- `superseded`
- `cancelled`

Keep it small and understandable.

### C. Eligibility rules
Bridge creation must require at least:
- request has selected_supplier_response_id
- selected response belongs to the same request
- selected response is still valid for execution semantics
- user_id/customer context is present
- admin explicitly triggers creation

If `tour_id` is provided:
- validate the Tour exists
- validate the Tour is compatible enough for future execution
- but do NOT start reservation/hold

### D. Admin-only bridge creation
Add an admin-only route/service action to:
- create a bridge record
- optionally attach a Tour at creation time or via narrow update
- reject duplicate/invalid bridge creation according to a minimal idempotency rule

Admin trigger must be explicit.
No bridge creation as a side effect of Track 5a resolution endpoint.

### E. Read visibility
Expose the bridge record in admin request detail/read APIs where appropriate.

Keep customer/supplier visibility minimal in this slice.
It is acceptable if only admin can fully inspect the bridge in 5b.1.

### F. Narrow Tour linkage
If the project already has enough stable data to link a bridge to an existing Tour, support nullable `tour_id`.
Do not generate a new Tour automatically in this track.
Do not create catalog duplication logic.

## Strong constraints
Do NOT implement:
- order creation
- reservation/hold creation
- payment session creation
- checkout start
- `TemporaryReservationService` invocation
- customer “continue to checkout” execution
- full self-serve RFQ execution
- broad auth rewrite
- broad handoff rewrite
- marketplace redesign

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current reservation semantics
- current Mini App booking routes
- current private bot booking routes
- current supplier publication flow
- current Track 4 request/response logic
- current Track 5a resolution logic
- current migrate -> deploy -> smoke discipline

## Modeling rule
Track 5b.1 stops at:
- explicit bridge persistence
- validation
- admin trigger
- optional tour linkage
- admin read visibility

It must not execute booking.

## Testing scope
Add focused tests for:
- bridge creation succeeds only when request has a valid selected response
- invalid cross-request or missing-selection cases are rejected
- duplicate/idempotent behavior is controlled
- optional tour linkage works only with valid Tour
- no order/reservation/payment side effects occur
- Track 5a and Track 4 regressions still pass where relevant

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. the exact bridge table/status model you will add
4. what remains explicitly postponed after 5b.1

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current bridge behavior now supported
6. compatibility notes against Tracks 0–5a
7. postponed items