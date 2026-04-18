Do not implement new application code yet.

Run a design/decision gate for **Track 5b.2 — RFQ Bridge to Layer A Execution**.

## Context
The following are already completed and accepted:
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 3.1 — Romanian showcase/template polish
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- smoke-tour stabilization exists and booking smoke passes on future smoke tours
- expired tours are hidden from customer-facing catalog/read paths

Current system now supports:
- supplier-owned offers
- moderated publication in channel
- RFQ intake
- supplier responses
- admin winner selection
- booking bridge intent record
- optional tour linkage on the bridge
- Layer A remains source of truth for booking/payment execution

## Critical rule
This step must decide **how and when a bridge record is allowed to invoke real Layer A execution semantics**:
- prepare
- hold / temporary reservation
- order creation
- payment entry / checkout

without collapsing:
- RFQ lifecycle
- bridge lifecycle
- Layer A booking/payment lifecycle

This is a design gate only, not implementation.

## Goal
Define the minimum safe execution entrypoint from Track 5b.1 bridge into existing Layer A booking/payment rails.

Main question:
**What exact action should be allowed to start real booking execution, and what object/path should it call first?**

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required decision areas

### A. Execution trigger
Decide what event is allowed to start Layer A execution:
- admin presses “start booking execution”
- customer presses “continue to booking”
- operator/handoff confirms
- another explicit workflow step

Reject implicit execution on:
- supplier_selected
- bridge creation alone
- bridge patch alone

### B. First execution call
Choose the first real Layer A action:
- call existing prepare/reservation-preparation flow first
- create draft Order first
- invoke TemporaryReservationService first
- open payment first
- another controlled entrypoint

Pick one recommended direction and explain why.

### C. Bridge -> Tour -> User contract
State what must be present before execution can start:
- active bridge
- valid linked Tour
- valid User/customer identity
- compatible sales_mode
- capacity and boarding availability
- policy checks

### D. sales_mode policy
Clarify how Track 5b.2 must interact with:
- `per_seat`
- `full_bus`
- Phase 7.1 sales_mode logic
- assisted full-bus path
- `TourSalesModePolicyService`

This is critical.
Do not allow silent whole-bus self-serve execution unless explicitly approved.

### E. Customer experience
Decide what customer sees in the first execution slice:
- “continue to booking”
- “complete reservation details”
- “our team will contact you”
- “payment now”
- etc.

Clarify whether customer should be able to act directly in v1 or whether execution remains admin/operator-assisted.

### F. Payment ownership and timing
Clarify:
- whether payment belongs in the first execution slice
- whether hold should happen before payment
- whether payment should remain entirely inside existing Layer A flows
- whether assisted/external closures should never enter checkout

### G. Failure / rollback model
Define what happens if:
- linked Tour becomes unavailable
- bridge exists but sales window closes
- customer never continues
- full_bus path is selected but not self-serve eligible
- payment or hold later fails

### H. State boundary
State clearly what Track 5b.2 should stop at.
Examples:
- open existing prepare flow only
- create a hold only
- open booking draft only
- or stop before payment

Choose a safe boundary.

## Required output
Produce a concise but concrete design result that includes:

1. **Current state summary**
   - what 5b.1 solved
   - what exact execution gap remains

2. **Execution entry options**
   Compare at least 2–3 realistic models, such as:
   - customer continue -> existing prepare flow
   - admin-triggered draft order -> existing hold flow
   - operator-only execution
   - bridge remains non-executing until another product gate

3. **Recommendation**
   Choose one recommended Track 5b.2 direction now.

4. **Explicit execution trigger**
   State exactly what event/action is allowed to begin execution.

5. **Execution boundary**
   State exactly where 5b.2 should stop:
   - before hold
   - after hold
   - before payment
   - etc.

6. **Policy interaction**
   State explicitly how `TourSalesModePolicyService` / `sales_mode` affects eligibility.

7. **Minimum safe rollout order**
   Outline the smallest safe rollout sequence if implementation is later approved.

8. **Must-not-break reminder**
   Reconfirm that Layer A remains source of truth for paid/hold/order semantics.

## Constraints
- do not modify application code
- do not add migrations
- do not refactor services
- do not redesign marketplace from scratch
- do not broaden auth
- keep this as a design gate only

## Before doing anything
Summarize:
1. what Track 5b.1 already solved
2. what exact execution problem remains
3. which docs you will use/reference

## After completion
Report:
1. final recommendation
2. whether Track 5b.2 implementation should start now or not
3. what first Layer A execution call should be
4. whether payment belongs in the first slice
5. exact next safe implementation step if approved