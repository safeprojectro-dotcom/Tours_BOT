Do not implement code yet.

Run a mini design/decision gate for **Track 5g.4a — Mode 2 whole-bus hold semantics**.

## Continuity
This gate comes after:
- accepted Track 5g design gate
- accepted Track 5g.1 classification
- accepted Track 5g.2 copy/policy separation
- accepted Track 5g.3 copy implementation
- accepted Track 5g.4 executable checkout gate

Accepted direction from 5g.4:
- Mode 2 (`supplier_route_full_bus`) should target **Model 1**
- reuse existing Layer A flow:
  - reservation/hold first
  - then existing payment-entry
- no second payment architecture
- no RFQ/bridge reuse for standalone catalog Mode 2

## Problem to solve
Before implementation starts, one product/technical sub-decision remains open:

For a ready-made full-bus catalog offer, what exactly does the temporary reservation hold represent in Layer A inventory terms?

This must be clarified before changing:
- `TourSalesModePolicyService`
- preparation flow
- `MiniAppBookingService`
- full-bus payment continuation

## Core question
When a customer reserves a **whole-bus catalog offer**, what exact inventory/seat semantics should be applied?

## Required decision areas

### A. Compare the candidate hold semantics
Compare at least these models:

#### Model A — reserve all currently available seats
`seats_count = seats_available` at the moment of hold.

#### Model B — reserve full configured capacity
`seats_count = seats_total` (or equivalent full configured bus capacity), regardless of current displayed available seats.

#### Model C — logical full-bus unit
Treat whole-bus as one logical unit instead of seat count, while still mapping into existing Layer A order/payment objects somehow.

#### Model D — full-bus hold only when full capacity is still untouched
Whole-bus self-serve is allowed only if `seats_available == seats_total`; otherwise assisted/manual only.

### B. Evaluate each model against current Layer A reality
For each model, analyze:
- compatibility with current `Order` / `TemporaryReservationService`
- inventory correctness
- oversell risk
- race/concurrency behavior
- clarity for operators/admin
- clarity for customer
- compatibility with existing payment-entry semantics
- whether it preserves “whole bus means no other seats should remain sellable”

### C. Decide the authoritative inventory rule
Choose one primary model for Mode 2 self-serve hold.

Be explicit:
- what `seats_count` should be written on the order
- what availability condition must be true before hold
- whether partial remaining inventory is compatible with whole-bus self-serve
- whether a previously partially sold/decremented tour can still be booked as full bus

### D. Define the blocking rule
Clarify when Mode 2 self-serve must be blocked and fall back to assisted/manual flow, for example:
- seats already partially sold
- active reservation exists
- seats_available < required full-bus quantity
- existing order/payment in progress
- sales window closed
- payment pending conflicts

### E. Customer-facing implication
Clarify what the customer should see when:
- full-bus self-serve is allowed
- full-bus self-serve is blocked because the bus is no longer fully available
- full-bus self-serve is blocked because the product remains assisted-only

Do not redesign copy broadly; just define the business meaning so implementation can map it later.

### F. Safe rollout recommendation
Recommend the smallest safe implementation after this gate.

Bias strongly toward:
- one clear seat/inventory rule
- reuse of existing Layer A hold/payment path
- strict blocking when inventory is ambiguous
- no second booking architecture
- no RFQ/bridge interaction

## Required output
Produce:
1. current problem summary
2. comparison of hold semantics models
3. final recommendation
4. exact inventory rule for Mode 2 hold
5. exact blocking/fallback rule
6. safe rollout order
7. must-not-break reminder

## Constraints
- no code
- no migrations
- no payment redesign
- no RFQ redesign
- no bridge redesign
- no reopening accepted 5f/5g work

## Before doing anything
Summarize:
1. what 5g.4 already decided
2. what exact hold/inventory question remains
3. which docs/code areas you will inspect

## After completion
Report:
1. final recommendation
2. whether implementation should start now
3. exact next safe implementation step