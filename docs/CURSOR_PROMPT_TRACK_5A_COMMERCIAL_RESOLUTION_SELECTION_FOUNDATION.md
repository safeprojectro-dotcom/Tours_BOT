Implement **Track 5a — Commercial Resolution Selection Foundation** on top of accepted Tracks 0–4.

## Preconditions already completed
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 4 — Custom Request Marketplace Foundation

## Critical rule
This track must add **commercial resolution selection**, but must NOT create a booking/order bridge yet.

A custom request remains separate from:
- orders
- reservations
- payments
- TemporaryReservationService
- payment entry/reconciliation

## Goal
Allow central admin to:
- select a winning supplier response for a request
- record the commercial resolution type/status
- close or advance the RFQ commercially
- expose a minimal customer-visible status outcome

without creating a normal order and without touching Layer A booking/payment rails.

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required scope

### A. Resolution selection model
Add the minimum safe model needed to represent:
- selected supplier response
- resolution status
- resolution kind / ownership type

Preferred direction:
- `selected_supplier_response_id` on the request, nullable
- validation that selected response belongs to the same request
- narrow status/kind vocabulary only

### B. Resolution vocabulary
Introduce a minimal commercial resolution state model such as:
- `open`
- `under_review`
- `supplier_selected`
- `closed_assisted`
- `closed_external`

or an equivalent minimal model that fits the current schema and docs.

Do not overdesign.

### C. Admin-only actions
Allow central admin to:
- select the winning supplier response
- update resolution status/kind
- close the request commercially
- add or preserve admin note/context as needed

### D. Customer-visible status foundation
Expose only a minimal customer-facing read/status layer, such as:
- request under review
- supplier selected
- team will contact you
- request closed

Do not expose a full multi-supplier quote-comparison UI in this track.

### E. Supplier/admin read updates
Update request detail/list outputs where needed so admin and suppliers can see:
- whether a response was selected
- whether the request is still open or commercially resolved

## Strong constraints
Do NOT implement:
- request -> order bridge
- order creation from RFQ
- reservation holds
- payment session creation
- checkout integration
- customer self-selection among responses
- first-response-wins automation
- auction/ranking engine
- broad auth rewrite
- broad handoff rewrite
- broad group assistant redesign

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current reservation semantics
- current Mini App booking routes
- current private bot booking routes
- current `sales_mode` behavior
- current assisted full-bus path
- current supplier publication flow
- current RFQ request/response foundation from Track 4
- current migrate -> deploy -> smoke discipline

## Modeling rule
Track 5a must stop at **selection + resolution recording**.
No hidden bridge into Layer A services is allowed.

## Testing scope
Add focused tests for:
- selecting a supplier response
- invalid selection rejection when response belongs to another request
- admin resolution status updates
- customer/admin read visibility of resolution status
- no regression in Track 4 request/response flows
- no regression in Track 2/3 supplier/publication flows where relevant

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. the exact minimum status/kind model you will add
4. what remains explicitly postponed after Track 5a

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current commercial resolution behavior now supported
6. compatibility notes against Tracks 0–4
7. postponed items