Do not implement code yet.

Run a design/decision gate for **Track 5g.4 — Mode 2 executable checkout path (booking vs direct payment)**.

## Continuity
This gate comes after:
- accepted Track 5g design gate (3 commercial modes)
- accepted Track 5g.1 read-side classification
- accepted Track 5g.2 full-bus catalog policy/copy gate
- accepted Track 5g.3 full-bus catalog copy separation

Accepted model so far:
- Mode 1 = supplier_route_per_seat = ready-made catalog offer sold by seat
- Mode 2 = supplier_route_full_bus = ready-made catalog offer sold as the whole bus
- Mode 3 = custom_bus_rental_request = customer-defined RFQ / marketplace request

Important:
- Mode 2 is not RFQ by default
- Mode 2 is a ready-made supplier catalog product
- therefore the primary customer CTA for Mode 2 should eventually lead to a real executable path, not a vague support-only dead end, if the product allows that path

## Problem to solve
Current Mode 2 UX has been corrected to avoid RFQ leakage, but the main CTA still behaves like a support/handoff placeholder.

This is insufficient for a ready-made catalog product.

For a published full-bus catalog offer, the primary CTA should ultimately be one of:
- start booking / create reservation
- continue to payment
- direct payment
- or, only if truly required by product/policy, assisted/manual only

The system needs an explicit decision on which executable path Mode 2 is allowed to use, and what determines that path.

## Core question
For **supplier_route_full_bus** ready-made catalog offers:

1. should the customer be able to create a booking/reservation?
2. should the customer be able to go directly to payment?
3. should the path depend on supplier-defined conditions?
4. if assisted-only remains possible, when exactly does that apply?

## Must preserve
Do not redesign or break:
- Layer A order/payment truth
- existing payment-entry semantics
- existing RFQ bridge/payment/hub flows
- accepted Track 5f v1
- accepted Mode 2 vs Mode 3 separation
- current service-layer ownership of business rules

This is design only.

## Required decision areas

### A. Clarify the product nature of Mode 2
Restate explicitly:
- Mode 2 is a ready-made full-bus catalog offer
- the supplier/admin already defined route, date/time, price, departure point, and conditions
- the customer is not creating a custom request
- therefore Mode 2 should not default to a support-only pseudo-flow unless product/business rules truly require that

### B. Define the allowed executable paths for Mode 2
Compare at least these models:

#### Model 1 — Reservation first, then payment
Customer creates a reservation/order for the whole-bus catalog offer, then proceeds to payment.

#### Model 2 — Direct payment without prior reservation
Customer pays directly for the full-bus offer without a reservation-hold step.

#### Model 3 — Supplier-defined path
Supplier/admin config for the ready-made full-bus offer determines whether the customer:
- books first
- pays directly
- or uses assisted/manual completion

#### Model 4 — Assisted-only
All Mode 2 offers remain assisted/manual only for now.

Compare pros/cons carefully in terms of:
- product clarity
- consistency with Layer A
- payment truth
- inventory/hold semantics
- operator burden
- customer expectation
- implementation risk

### C. Decide what object/path should remain authoritative
Clarify for Mode 2:
- what object anchors the journey (`Tour`, `Order`, reservation hold, payment session, etc.)
- whether the normal Layer A booking flow can/should be reused
- whether payment-entry can/should be reused
- whether whole-bus booking should still create an `Order`
- whether seat count / capacity semantics need special treatment or can remain based on existing `Tour` / inventory rules

### D. Supplier-defined conditions
Decide whether Mode 2 executable path should be driven by supplier-defined conditions and, if yes:
- where those conditions should live conceptually
- whether current data model already supports this enough
- whether a later explicit field / policy is needed
- whether product can first choose a simple default path before a richer supplier-defined model exists

Important:
Do not conflate RFQ supplier-declared response policy with catalog Mode 2 unless explicitly justified.

### E. Primary CTA logic
For Mode 2 only, define which primary CTA should exist under each approved state:
- booking path enabled
- payment path enabled
- assisted-only path
- existing active reservation/order
- payment pending
- payment confirmed

Make explicit when the CTA should be:
- `Book this charter`
- `Reserve charter`
- `Continue booking`
- `Continue to payment`
- `Pay now`
- `Contact us to complete booking`

### F. Relationship to current architecture
Explain exactly how this should relate to:
- `Tour.sales_mode`
- `TourSalesModePolicyService`
- `TemporaryReservationService`
- `PaymentEntryService`
- existing Layer A booking/payment/order objects
- Mode 3 bridge flows (which must stay separate)

### G. Safe rollout strategy
Recommend the smallest safe rollout order after this gate.

Bias strongly toward:
1. one explicit product decision first
2. reuse existing Layer A mechanics where possible
3. avoid second payment architecture
4. keep Mode 2 separate from RFQ
5. ship in narrow slices

Example rollout patterns to evaluate:
- decision -> booking-only implementation -> later payment continuation
- decision -> direct payment only
- decision -> assisted default with a real later execution slice
- decision -> supplier-defined path in a later schema change

## Required output
Produce:
1. current problem summary
2. comparison of Mode 2 executable path models
3. final recommendation
4. what should be the authoritative path/object model
5. whether supplier-defined conditions are required now or later
6. primary CTA matrix for Mode 2
7. safe rollout order
8. must-not-break reminder

## Constraints
- no code
- no migrations
- no payment redesign
- no RFQ redesign
- no bridge redesign
- no reopening accepted 5f/5g separation work

## Before doing anything
Summarize:
1. what current Mode 2 UX/policy already solved
2. what real checkout/execution gap remains
3. which docs/code areas you will inspect

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. exact next safe implementation step