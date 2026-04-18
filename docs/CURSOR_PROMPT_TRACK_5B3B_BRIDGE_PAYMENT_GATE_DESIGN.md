Do not implement new application code yet.

Run a design/decision gate for **Track 5b.3b — Bridge-Scoped Payment Gate Using Existing Layer A Payment Path**.

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
- Track 5b.3a — RFQ supplier policy fields + EffectiveCommercialExecutionPolicyService
- smoke-tour stabilization exists and booking smoke passes
- expired tours are hidden from customer-facing catalog/read paths

Current system now supports:
- supplier-owned offers
- RFQ intake/responses
- admin winner selection
- bridge intent record
- bridge execution entry to preparation/hold
- effective execution/payment policy resolver
- Layer A remains source of truth for actual orders/reservations/payments

## Core principle
Supplier/admin configuration determines commercial intent.
Layer A determines real booking/payment execution semantics.
Customer surfaces must reflect allowed paths, not invent them.

## Critical rule
This gate must decide **how a bridge-backed flow is allowed to enter payment**, using the **existing Layer A payment-entry path only**, and only when the effective commercial policy permits platform checkout.

No new payment provider behavior should be invented here.

This is a design gate only, not implementation.

## Goal
Define the minimum safe bridge-scoped payment entry model after:
- a bridge exists
- an eligible self-service path exists
- a valid temporary reservation/hold has already been created in Layer A

Main question:
**How should a bridge-backed customer continue into payment, using existing Layer A payment mechanics, without creating a parallel payment architecture?**

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required decision areas

### A. Payment entry trigger
Decide what exact event is allowed to open payment for a bridge-backed path:
- customer explicit “continue to payment”
- automatic after successful hold creation
- admin/operator action only
- existing order/payment page reuse without a special bridge route

Reject implicit payment opening from:
- winner selection
- bridge creation
- bridge patch
- preparation alone without a valid hold

### B. Payment entry object
Decide what object should be used as the payment anchor:
- the existing Layer A Order created by hold
- a bridge-linked read context that resolves to an existing order
- a dedicated bridge payment wrapper that still calls existing payment-entry
- no new wrapper at all

Choose one recommended direction.

### C. Preconditions for payment
Clarify exactly what must be true before bridge-backed payment is allowed:
- active bridge
- valid linked Tour
- effective policy says `platform_checkout_allowed`
- a valid existing temporary reservation/order exists
- order belongs to the same user/customer
- bridge and order/tour are still aligned
- request is not `external_only`
- assisted-only paths are blocked

### D. Relationship to existing payment-entry
Decide how bridge payment should reuse the existing Layer A payment path:
- direct reuse of existing `payment-entry` route/service after resolving the held order
- bridge-specific route that only resolves context and then delegates to existing payment entry
- UI-only link to existing order payment page

Choose one recommended path.

### E. Bridge lifecycle impact
Clarify whether bridge state should change when:
- hold exists
- payment entry is opened
- payment succeeds
- payment fails
- hold expires

Decide whether bridge state should remain mostly informational or whether a minimal progression is needed.

### F. Assisted / external policy handling
Define strict rules for:
- `platform_checkout_allowed = false`
- `assisted_only = true`
- `external_only = true`

These cases must not be able to open platform payment.

### G. Customer UX
Decide what the customer should see after a successful hold in a bridge-backed flow:
- the same payment CTA as standard Layer A flow
- a bridge-specific “continue to payment” step
- assisted message instead of payment when blocked
- whether any new UX is actually needed

### H. Failure / reconciliation model
Decide what happens if:
- hold exists but policy changes before payment
- bridge exists but order expired
- payment fails
- payment succeeds
- supplier/admin policy changes after hold but before payment

The answer should keep Layer A reconciliation as source of truth.

## Required output
Produce a concise but concrete design result that includes:

1. **Current state summary**
   - what 5b.2 and 5b.3a already solved
   - what exact payment gap remains

2. **Bridge payment options**
   Compare at least 2–3 realistic models, such as:
   - direct reuse of existing order payment entry
   - bridge payment wrapper resolving order then delegating
   - no bridge-specific payment step at all
   - operator-assisted payment only

3. **Recommendation**
   Choose one recommended direction for this project now.

4. **Explicit payment gate rule**
   State exactly what combination of:
   - effective policy
   - valid hold/order
   - user identity
   - bridge alignment
   allows payment.

5. **Execution/payment boundary**
   State clearly whether Track 5b.3b should:
   - only expose payment entry
   - also mutate bridge status
   - or stop at read-only linking

6. **Minimum safe rollout order**
   If implementation is approved later, outline a safe sequence, for example:
   - bridge -> resolve held order
   - bridge payment gate
   - reuse existing payment-entry
   - bridge read/status update
   - no new payment engine

7. **Must-not-break reminder**
   Reconfirm:
   - supplier/admin policy decides whether platform payment is allowed
   - Layer A order/payment/reconciliation remains source of truth
   - no parallel payment architecture is introduced

## Constraints
- do not modify application code
- do not add migrations
- do not refactor services
- do not redesign payment architecture
- do not broaden auth
- keep this as a design gate only

## Before doing anything
Summarize:
1. what 5b.2 and 5b.3a already decide
2. what exact payment-entry problem remains
3. which docs you will use/reference

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. what object/path should anchor bridge-backed payment
4. what exact gate should permit payment
5. exact next safe implementation step if approved