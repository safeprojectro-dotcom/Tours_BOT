Do not implement new application code yet.

Run a design/decision gate for **Track 5b.3 — Supplier-Defined Execution and Payment Policy Gate**.

## Core principle
For this project, the **supplier admin configuration is the source of truth** for how an offer/request can be commercially executed.

That means:
- supplier defines sale/execution mode
- supplier defines payment mode
- supplier defines whether self-service is allowed
- supplier defines whether closure is platform checkout, assisted, or external
- platform/bot/Mini App must not invent their own commercial execution rules

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
- Track 5b.2 — explicit bridge execution entry into existing preparation/hold for eligible tours
- smoke-tour stabilization exists and booking smoke passes on future smoke tours
- expired tours are hidden from customer-facing catalog/read paths

Current system already has:
- supplier-owned offers
- publication into channel
- RFQ requests/responses
- admin winner selection
- bridge intent record
- bridge execution entry
- TourSalesModePolicyService protecting self-service execution

## Critical rule
This gate must decide how **supplier-defined commercial policy** becomes the governing rule for:
- whether self-service execution is allowed
- whether platform checkout is allowed
- whether execution remains assisted only
- whether a bridge may proceed into Layer A hold/payment
- whether external closure blocks platform checkout

This is a design gate only, not implementation.

## Goal
Define the minimum safe policy model that makes supplier-admin configuration the source of truth for execution and payment behavior across:
- ready-made offers
- RFQ/commercial resolution
- bridge execution
- future payment entry

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required decision areas

### A. Supplier policy source of truth
Decide exactly where the governing execution/payment policy should live.

Possible candidates:
- supplier_offer fields
- supplier-level defaults + offer-level overrides
- future Tour materialization carrying normalized execution policy
- a dedicated supplier commercial policy object

Choose one recommended direction for this project now.

### B. Minimum policy vocabulary
Define the minimum commercial policy concepts the system needs.

At minimum, decide how to model:
- sale mode
- execution mode
- payment mode
- self-service allowed vs assisted only
- platform checkout allowed vs not allowed
- external closure allowed vs not allowed

Keep the vocabulary small and operationally clear.

### C. Relationship to existing fields
Clarify how this supplier-defined policy relates to:
- existing `sales_mode`
- existing `payment_mode`
- existing `TourSalesModePolicyService`
- Track 5a resolution kind/status
- Track 5b bridge lifecycle

State explicitly what remains source-of-truth and what is derived/runtime policy.

### D. Policy propagation
Decide how supplier-defined policy should flow downstream.

Required question:
How should supplier policy propagate into:
- published supplier offers
- RFQ winner selection outcome
- bridge creation
- bridge execution entry
- future Layer A payment entry

This propagation must be explicit, not ad hoc.

### E. Policy gating at execution time
Decide the exact rule for when bridge execution may proceed into:
- preparation
- hold
- payment

Examples:
- `per_seat` + supplier allows self-service + platform checkout allowed
- `full_bus` + assisted only
- external closure only
- manual supplier closure only

The system must not “upgrade” a supplier-assisted path into platform self-service on its own.

### F. Payment ownership
Decide the permitted payment ownership models:
- platform checkout
- supplier-assisted closure
- external/manual payment recorded outside platform
- hybrid model

State whether the first payment-facing bridge slice should support more than one, or should start with only one allowed mode.

### G. Admin role
Clarify what the platform admin is allowed to do when supplier policy exists:
- enforce stricter rules
- approve/reject publication only
- override supplier execution mode or not
- approve bridge execution or only observe
- block unsafe policy combinations

### H. Customer experience
Decide what customer-facing surfaces should do when supplier policy says:
- self-service allowed
- assisted only
- external closure
- no platform checkout

Customer surfaces must reflect supplier policy rather than inventing behavior.

### I. Layer A execution ownership
Decide whether Layer A should:
- receive normalized execution/payment policy from supplier configuration
- or continue using its own rules plus bridge-time checks
- or both

Clarify how `TourSalesModePolicyService` should evolve:
- remain the final execution guard
- be extended to include supplier payment/execution policy
- or coexist with a parallel supplier commercial policy resolver

### J. Failure / conflict cases
Decide what happens if:
- supplier config says assisted-only, but linked Tour appears self-service-capable
- RFQ is selected for a supplier whose payment mode conflicts with platform checkout
- old bridge points to a Tour with incompatible policy
- supplier changes policy after publication or after bridge creation

## Required output
Produce a concise but concrete design result that includes:

1. **Current state summary**
   - what existing tracks already support
   - what exact supplier-policy gap remains

2. **Policy model options**
   Compare at least 2–3 realistic models, such as:
   - offer-level source of truth
   - supplier default + offer override
   - dedicated execution policy object
   - normalized policy copied into Tour/bridge at execution time

3. **Recommendation**
   Choose one recommended direction for this project now.

4. **Policy propagation rule**
   State exactly how supplier-defined policy should flow into RFQ, bridge, and Layer A execution.

5. **Execution/payment gate rule**
   State exactly what supplier policy combinations allow:
   - self-service preparation
   - self-service hold
   - platform payment
   - assisted-only flow
   - external closure only

6. **Admin power boundary**
   State what admin may override and what remains supplier-owned.

7. **Minimum safe rollout order**
   If implementation is later approved, outline a safe sequence, for example:
   - normalize policy model
   - bridge execution gate by supplier policy
   - payment gate by supplier policy
   - only later richer override/UX flows

8. **Must-not-break reminder**
   Reconfirm:
   - supplier admin remains the source of truth
   - Layer A remains the source of truth for actual holds/orders/payments
   - customer surfaces reflect, but do not invent, execution rules

## Constraints
- do not modify application code
- do not add migrations
- do not refactor services
- do not redesign the marketplace from scratch
- do not broaden auth
- keep this as a design gate only

## Before doing anything
Summarize:
1. what the current system already decides via supplier/admin
2. what exact execution/payment-policy gap remains
3. which docs you will use/reference

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. what policy model should be the source of truth
4. how that policy should gate bridge execution and payment
5. exact next safe implementation step if approved