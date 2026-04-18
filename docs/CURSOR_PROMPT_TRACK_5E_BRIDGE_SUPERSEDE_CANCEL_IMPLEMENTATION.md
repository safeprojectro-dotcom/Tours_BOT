Implement **Track 5e — Bridge Supersede / Cancel Lifecycle**.

Do not redesign RFQ, booking, or payment architecture.

## Preconditions already completed
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 — bridge execution entry
- Track 5b.3a — effective commercial execution resolver
- Track 5b.3b — bridge payment eligibility
- Track 5c — RFQ Mini App UX wiring
- Track 5d — Mini App My Requests / RFQ hub
- Track 5e design gate concluded:
  - bridge lifecycle is separate from request lifecycle
  - Layer A remains source of truth for orders/payments
  - existing bridge statuses `superseded` and `cancelled` should be used
  - bridge close must fail closed for customer execution/payment entry
  - order/payment rows must not be mutated by bridge close

## Core principle
Bridge rows are orchestration artifacts.
They may become non-actionable, replaced, or closed.
They must not become a second order/payment truth.

## Goal
Make bridge lifecycle operationally real by allowing:
- active bridge -> superseded
- active bridge -> cancelled

and ensuring all customer/action surfaces fail closed when a bridge is no longer active.

## Required scope

### A. Admin/service transitions
Implement the minimal service/API path to transition an active bridge to:
- `superseded`
- `cancelled`

Use existing enum values already present in the system.

Allow optional `admin_note`.

### B. Validation rules
Enforce conservative rules:
- only active bridges may transition to terminal bridge states
- terminal bridges should not transition back to active
- request status should not be implicitly changed
- order/payment rows must not be mutated
- bridge close must not imply refund/cancel of Layer A order

### C. Supersede/create safe path
Support the safe ops path:
- close old bridge
- then create a new bridge

If possible and appropriate in current architecture, make this safe against the “active bridge 409” window.
If not, keep it explicit and documented.

### D. Read/action fail-closed behavior
Update all bridge-dependent reads/actions so that superseded/cancelled bridges are no longer actionable.

This includes, where relevant:
- bridge preparation
- bridge reservation creation
- bridge payment eligibility
- My Requests hub CTA resolution
- bridge detail/status screens
- admin detail/read surfaces

### E. Customer UX behavior
When a bridge is superseded/cancelled:
- remove bridge execution/payment CTAs
- show neutral closed/path-changed messaging
- if an existing Layer A order still exists, continue to prefer order-based UX such as Open booking / Continue to payment through normal order logic

### F. Keep Layer A authoritative
Explicitly preserve:
- holds remain authoritative in Layer A
- payment remains authoritative in Layer A
- paid orders remain visible/usable according to existing Layer A logic
- bridge close does not cancel payment or booking state

## Strong constraints
Do NOT implement:
- request status redesign
- bridge-driven order mutation
- bridge-driven payment mutation
- refund logic
- superseded_by_bridge_id unless truly minimal and necessary
- auto-supersede on winner change
- broad audit redesign
- new payment flows
- new booking flows

## Must-not-break rules
Preserve:
- current request lifecycle
- current bridge creation behavior where still valid
- current effective policy behavior
- current bridge execution/payment eligibility behavior for active bridges
- current Layer A booking/payment semantics
- current Mini App catalog/booking/payment flow
- current My Requests hub behavior except where terminal bridges must now fail closed

## Testing scope
Add focused tests for:
- active bridge -> superseded
- active bridge -> cancelled
- terminal bridge cannot be used for preparation
- terminal bridge cannot be used for reservation creation
- terminal bridge cannot be used for payment eligibility
- request status remains unchanged
- order/payment rows remain unchanged
- close old -> create new bridge path works as intended
- My Requests / bridge CTA logic hides bridge continuation for terminal bridges
- no regression in Tracks 5b.2–5d

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. exact admin/service transitions you will add
4. what remains explicitly postponed after 5e

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current bridge supersede/cancel behavior now supported
6. how customer actionability changes after terminal bridge state
7. compatibility notes against Tracks 0–5d
8. postponed items