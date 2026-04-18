Implement **Track 5d — Mini App "My Requests" / RFQ Status Hub**.

Do not introduce new booking/payment domain behavior, new payment flows, or quote-comparison UI.

## Preconditions already completed
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 — explicit bridge execution entry
- Track 5b.3a — supplier policy + effective execution resolver
- Track 5b.3b — bridge payment eligibility + existing payment-entry reuse
- Track 5c — RFQ Mini App UX wiring for bridge execution and payment continuation

## Core principle
Mini App must present RFQ/custom-request state clearly using existing backend truth.
It must not invent new commercial logic, booking semantics, or payment semantics.

## Goal
Add a Mini App user-facing hub where a customer can:
- see their custom requests
- open a request detail/status view
- understand whether the request is under review, supplier-selected, assisted-only, external-only, or ready for self-service continuation
- continue booking/payment only when existing backend paths already allow it

## Required scope

### A. My Requests list
Add a Mini App screen for listing customer custom requests.

The list should show, at minimum:
- request type / short label
- date or route summary where available
- high-level status
- whether action is available
- CTA to open request detail

Use existing backend reads where possible.
Add minimal API/client glue only if needed.

### B. Request detail / status screen
Add a detail screen for a selected custom request.

The detail should show:
- request summary
- current RFQ/commercial status
- whether self-service continuation is available
- whether assisted/external path applies
- bridge-related continuation CTA only if allowed by existing backend truth

### C. CTA rules
Possible CTA outcomes:
- `Continue booking` if active bridge + self-service preparation path is available
- `Continue to payment` if hold exists and payment eligibility allows it
- `Open booking` if an existing booking/order state is the clearest next step
- no action CTA if assisted/external/review-only path applies

Do not invent new CTAs outside current backend capabilities.

### D. Reuse existing wiring
If a request is bridge-actionable:
- reuse the existing `/custom-requests/{id}/bridge` route/wiring from Track 5c
- reuse existing payment continuation behavior
- do not build a second RFQ continuation path

### E. Clear user-facing statuses
Translate backend/request/bridge/payment state into simple user-facing copy.

Examples:
- Under review
- Supplier selected
- Continue booking
- Reserved temporarily
- Continue to payment
- Assistance required
- Closed outside platform

Do not expose raw internal enum names directly.

### F. Minimal state only
Keep Mini App state light:
- request id
- selected request detail
- optional bridge actionable flag / order_id if already provided by existing reads

Do not add a client-side workflow engine.

## Strong constraints
Do NOT implement:
- customer multi-quote comparison
- bridge supersede/cancel
- new booking engine logic
- new payment logic
- new provider behavior
- broad backend redesign
- auth rewrite
- handoff workflow redesign

## Must-not-break rules
Preserve:
- existing catalog/booking/payment flows
- existing RFQ bridge flow
- existing effective policy behavior
- existing payment-entry reuse
- current backend truth as the single source of state

## Testing scope
Add focused tests for:
- My Requests list rendering / loading
- request detail rendering for actionable vs blocked states
- continue CTA appears only when backend/actionability supports it
- payment continuation CTA appears only when payment eligibility path already allows it
- no regression in Track 5c bridge flow
- no regression in standard Mini App catalog/payment flow

## Before coding
Summarize:
1. exact files/modules to touch
2. whether migrations are needed
3. exact screens/routes/state you will add
4. what remains postponed after Track 5d

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current My Requests / RFQ status hub behavior now supported
6. compatibility notes against Tracks 0–5c
7. postponed items