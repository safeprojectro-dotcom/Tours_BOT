Do not implement new application code yet.

Run a design/decision gate for **Track 5e — Bridge Supersede / Cancel Lifecycle**.

## Context
The following are already completed and accepted:
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 — explicit bridge execution entry
- Track 5b.3a — supplier policy fields + effective commercial execution resolver
- Track 5b.3b — bridge payment eligibility + existing payment-entry reuse
- Track 5c — RFQ Mini App UX wiring
- Track 5d — Mini App My Requests / RFQ status hub

Current system already supports:
- RFQ intake and supplier responses
- admin winner selection
- bridge creation
- bridge execution entry
- hold/payment continuation through existing Layer A
- customer RFQ status hub and continuation CTAs

## Core principle
Bridge rows are orchestration artifacts.
Layer A orders/payments remain authoritative for booking/payment execution.
Supplier/admin policy remains authoritative for commercial intent.

## Critical rule
This gate must decide how a bridge can be:
- superseded
- cancelled
- made non-actionable
- safely replaced by a newer bridge or newer execution path

…without corrupting:
- RFQ/request truth
- Layer A order truth
- payment truth
- customer UX continuity

This is a design gate only, not implementation.

## Goal
Define the minimal safe lifecycle rules for bridge supersede/cancel so the system can handle stale bridges, replaced tours, changed supplier outcomes, or manually closed RFQ execution paths without leaving the Mini App in a confusing state.

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required decision areas

### A. Why bridges need lifecycle control
Explain the real cases this must solve, for example:
- admin chose a different tour after a bridge already existed
- selected supplier response changed
- supplier policy changed and self-service is no longer allowed
- bridge became stale while an order/hold exists
- customer should no longer continue via this bridge
- bridge was created too early and must be closed safely

### B. Supersede vs cancel
Define the difference clearly.

Examples:
- **superseded** = replaced by a newer valid bridge or newer execution path
- **cancelled** = bridge intentionally closed and should no longer be actionable

State whether both are needed and how they differ semantically.

### C. Relationship to request status
Clarify:
- does superseding/cancelling a bridge change RFQ request status?
- or is bridge lifecycle intentionally separate from request lifecycle?

This is important.
Avoid collapsing bridge state into request state.

### D. Relationship to Layer A orders
Clarify what happens if a bridge is superseded/cancelled while:
- no order exists
- hold exists
- payment is pending
- payment succeeded
- order expired
- order already became the main source of truth for the user

State what remains authoritative in each case.

### E. Customer-facing effect
Decide what the user should experience if a bridge is:
- superseded before hold
- superseded after hold
- cancelled before hold
- cancelled after hold
- no longer actionable because policy changed

Examples:
- hide continuation CTA
- show “booking path changed”
- show “open booking” if Layer A order exists
- show assisted-only message
- keep paid order visible even if bridge is dead

### F. Admin actions
Define what admin should be allowed to do:
- supersede bridge with another bridge
- cancel bridge
- block self-service continuation
- attach note/reason
- whether admin may do this when payment/hold already exists

Be explicit about what is safe now vs later.

### G. Minimal lifecycle model
Choose the minimal model needed now.

Possible directions:
- reuse existing bridge statuses only
- add explicit bridge status values like `superseded` / `cancelled`
- add reason fields only
- soft-close active bridge without expanding the state machine much

Pick one recommended direction.

### H. Read-side behavior
Define how bridge lifecycle should affect:
- bridge execution entry
- bridge payment eligibility
- My Requests hub CTAs
- RFQ Mini App detail
- admin RFQ detail

All read/action surfaces should fail closed consistently.

### I. Failure and edge cases
Decide what happens when:
- a new bridge replaces an old one
- old bridge still has a hold/order
- policy changed after hold but before payment
- a bridge is cancelled while the user is on the payment screen
- customer opens a stale deep link

### J. Safe rollout order
Define the minimum safe rollout if implementation is approved later.

## Required output
Produce a concise but concrete design result that includes:

1. **Current state summary**
   - what bridge lifecycle is missing today
   - where stale/obsolete bridge risk exists

2. **Lifecycle options**
   Compare at least 2–3 realistic models, such as:
   - minimal explicit statuses
   - soft-close with flags/reasons
   - full richer workflow
   - no lifecycle until later

3. **Recommendation**
   Choose one recommended direction for this project now.

4. **Supersede/cancel rule**
   State exactly:
   - what supersede means
   - what cancel means
   - when each is allowed
   - what they do to customer actionability

5. **Interaction with orders/payments**
   State clearly how bridge lifecycle affects:
   - no order
   - active hold
   - pending payment
   - paid order
   - expired order

6. **Customer UX rule**
   State what CTAs/messages should be shown after bridge close/supersede.

7. **Minimum safe rollout order**
   If implementation is approved later, outline a safe sequence.

8. **Must-not-break reminder**
   Reconfirm:
   - Layer A remains source of truth for orders/payments
   - supplier/admin policy remains source of truth for commercial intent
   - bridge lifecycle must not create a second order/payment truth

## Constraints
- do not modify application code
- do not add migrations
- do not redesign RFQ marketplace from scratch
- do not redesign payment architecture
- do not broaden auth/handoff
- keep this as a design gate only

## Before doing anything
Summarize:
1. what bridge layer already supports
2. what lifecycle/control gap remains
3. which docs you will use/reference

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. what lifecycle model should be added
4. how supersede/cancel should affect customer actionability
5. exact next safe implementation step if approved