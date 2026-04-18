Do not implement code yet.

Run a design/decision gate for **Track 5g.2 — Full-bus catalog offer policy/copy separation**.

## Continuity
This gate comes after:
- accepted Track 5g design gate (3 commercial modes)
- accepted Track 5g.1 read-side classification

Current accepted model:
- `supplier_route_per_seat`
- `supplier_route_full_bus`
- `custom_bus_rental_request`

Important:
- Track 5f v1 remains accepted and must not be reopened
- Track 5g.1 remains read-only classification only
- this gate must not redesign RFQ execution/payment logic

## Problem to solve
The product now distinguishes Mode 2 (`supplier_route_full_bus`) from Mode 3 (`custom_bus_rental_request`) on read-side.

But customer-facing behavior/copy for Mode 2 is still unclear:
- Mode 2 risks being presented as if it were RFQ/custom request
- full_bus may still be treated as automatically “operator-only”
- the UI may use “Need help / team will contact you / request offer” language where the product is actually a ready-made supplier catalog offer

This gate must define the correct customer-facing policy/copy model for **Mode 2**.

## Core question
For a **ready-made supplier full-bus catalog offer**, what should be the correct:
- conceptual execution model
- default assisted/self-service interpretation
- CTA family
- customer-facing copy

without confusing it with RFQ Mode 3.

## Must preserve
Do not break or redesign:
- Layer A order/payment truth
- Track 5a–5e bridge/payment/hub flows
- Track 5f v1 RFQ customer summary slice
- Track 5g.1 classification
- existing RFQ/custom request semantics

This is design only.

## Required decision areas

### A. Re-state the difference between Mode 2 and Mode 3
Make explicit:
- Mode 2 is a ready-made supplier catalog offer
- Mode 3 is a customer-defined RFQ/custom rental request
- Mode 2 must not inherit RFQ wording by default

### B. Policy model for Mode 2
Clarify:
- whether `supplier_route_full_bus` is conceptually eligible for self-service at all
- whether it is assisted-only by default
- whether the answer depends on supplier-defined execution/payment policy
- whether “full bus” alone is enough to force operator/human flow

### C. CTA/copy matrix
Define the correct customer-facing CTA and copy families for Mode 2 under realistic states such as:
- ready-made full-bus offer, self-service allowed
- ready-made full-bus offer, assisted-only
- ready-made full-bus offer, policy unclear / blocked
- ready-made full-bus offer with payment allowed later
- ready-made full-bus offer where direct checkout is not yet implemented

Examples to evaluate:
- `Reserve bus`
- `Continue booking`
- `Continue to payment`
- `Request confirmation`
- `Need help`
- `Request offer`

Make explicit which labels belong to catalog Mode 2 and which belong only to RFQ Mode 3.

### D. Customer mental model
Clarify what the user should think they are doing in Mode 2:
- buying a ready-made product
- requesting a custom quotation
- awaiting operator confirmation
- entering a standard catalog checkout
- entering an assisted catalog flow

The answer must be precise and must avoid RFQ leakage.

### E. Interaction with current architecture
Explain how Mode 2 copy/policy should relate to:
- `Tour.sales_mode`
- `TourSalesModePolicyService`
- any future whole-bus self-service decision
- current Mini App catalog/tour detail
- current RFQ bridge/payment flows (which should stay Mode 3 only)

### F. Safe rollout order
Recommend the smallest safe rollout after this gate.
Bias strongly toward:
1. copy/presentation correction first
2. no execution changes in the same slice
3. separate gate later if whole-bus self-service execution is desired

## Required output
Produce:
1. current problem summary
2. clarified policy model for `supplier_route_full_bus`
3. customer mental model for Mode 2
4. CTA/copy matrix
5. final recommendation
6. safe rollout order
7. must-not-break reminder

## Constraints
- no code
- no migrations
- no payment redesign
- no bridge redesign
- no RFQ redesign
- no Layer A redesign
- no reopening Track 5f v1

## Before doing anything
Summarize:
1. what Track 5g and 5g.1 already solved
2. what Mode 2 ambiguity still remains
3. which docs/code areas you will inspect

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. exact next safe implementation step