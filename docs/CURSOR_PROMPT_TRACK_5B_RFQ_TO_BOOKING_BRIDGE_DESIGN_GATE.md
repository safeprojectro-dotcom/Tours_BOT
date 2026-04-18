Do not implement new application code yet.

Run a design/decision gate for **Track 5b — RFQ to Layer A Booking Bridge**.

## Context
The following are already completed and accepted:
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 3.1 — Romanian showcase template / photo-first polish
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- smoke-tour stabilization exists and booking smoke passes on future smoke tours

The system now supports:
- supplier-owned offers
- moderated publication into Telegram showcase
- custom request intake from Mini App and private bot
- supplier responses to requests
- admin winner selection / commercial resolution
- existing Layer A booking/order/payment rails remain intact

## Critical rule
This step must decide **how a winning RFQ can move into Layer A booking/payment semantics** without silently collapsing:
- RFQ lifecycle
- commercial resolution lifecycle
- normal order/reservation/payment lifecycle

This is a design gate only, not implementation.

## Goal
Determine the minimum safe bridge model between:
- a commercially resolved RFQ (Track 5a)
and
- Layer A order / reservation / payment flows

Main question:
**What should the system create, and when, after an RFQ has a selected winning supplier response?**

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required decision areas

### A. Bridge trigger
Decide what event is allowed to trigger the bridge:
- admin selects winning supplier response?
- admin explicitly presses “create booking/order draft”?
- customer accepts a selected proposal?
- ops/handoff confirms manually?

This must not happen implicitly.

### B. Bridge target
Decide what the bridge should create first:
- a normal Layer A order directly
- a separate RFQ booking bridge record
- an operator draft / booking draft
- a generated Tour-like sellable object first
- no creation yet, only manual handoff

Choose one recommended direction.

### C. Eligibility rules
Clarify what must be true before a bridge can happen:
- selected supplier response exists
- response has commercial fields required for execution
- booking mode/sales mode is compatible
- capacity/date/boarding points are sufficiently known
- customer identity/contact is sufficient
- admin confirms the bridge

### D. Payment ownership
Clarify who owns payment after bridge:
- platform checkout only
- supplier-assisted/manual payment
- external recorded closure only
- configurable by selected supplier/payment mode

This must be explicit and must not blur Track 5a resolution with actual payment execution.

### E. Layer A compatibility
State clearly:
- whether the bridge should reuse existing order/reservation/payment services
- whether it should create a controlled draft before reservation/hold/payment
- whether new bridge logic must remain outside `TemporaryReservationService` until execution time

### F. Customer experience
Decide what the customer sees:
- “your request is accepted, continue to booking”
- “our team will contact you”
- “complete payment now”
- “booking draft created”
- etc.

### G. Failure / fallback model
Decide what happens if:
- selected proposal becomes unavailable
- customer does not proceed
- supplier drops out
- capacity/date changes before booking execution

## Required output
Produce a concise but concrete design result that includes:

1. **Current state summary**
   - what Track 5a solves
   - what exact bridge gap remains

2. **Bridge options**
   Compare at least 2–3 realistic bridge models, such as:
   - direct order creation
   - explicit RFQ bridge record / booking draft
   - operator-mediated manual transition
   - generated execution object first

3. **Recommendation**
   Choose one recommended Track 5b direction for this project now.

4. **Explicit trigger rule**
   State exactly what action/event should trigger the bridge.

5. **Execution boundary**
   State exactly where Track 5b should stop.
   Example:
   - create draft only
   - no payment session yet
   - or create order but do not reserve/pay yet
   - etc.

6. **Minimum safe rollout order**
   If implementation is later approved, outline a safe order, e.g.:
   - bridge record / draft
   - admin confirmation
   - customer-visible continue step
   - only later reservation/hold/payment invocation

7. **Must-not-break reminder**
   Reconfirm that Layer A booking/order/payment semantics remain the source of truth.

## Constraints
- do not modify application code
- do not add migrations
- do not refactor services
- do not redesign marketplace from scratch
- do not broaden auth
- keep this as a design gate only

## Before doing anything
Summarize:
1. what Tracks 4 and 5a already solved
2. what exact bridge problem remains
3. which docs you will use/reference

## After completion
Report:
1. final recommendation
2. whether Track 5b implementation should start now or not
3. what object/action should be created first
4. whether payment should be in or out of the first bridge slice
5. exact next safe implementation step if approved