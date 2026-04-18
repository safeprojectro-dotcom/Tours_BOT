Implement **Track 5b.3a — RFQ Supplier Policy Fields + Effective Commercial Execution Resolver**.

Do not implement payment entry, new checkout flows, or customer-facing payment UX in this track.

## Preconditions already completed
- Track 0 — frozen core baseline
- Track 1 — design package alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication
- Track 3.1 — Romanian showcase/template polish
- Track 4 — Custom Request Marketplace Foundation
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 — explicit bridge execution entry into existing preparation/hold for eligible tours
- Track 5b.3 design gate concluded:
  - supplier admin configuration is the source of truth for commercial intent
  - supplier policy must propagate into RFQ response / bridge / execution
  - Layer A remains source of truth for actual hold/order/payment semantics
  - effective execution/payment policy must be a composed runtime result, not ad hoc route logic

## Core principle
For this project:
- supplier defines commercial intent
- platform moderates and orchestrates
- Layer A executes only allowed paths
- customer surfaces reflect allowed paths, but do not invent them

## Critical rule
This track must add:
1. supplier-declared execution/payment fields on RFQ responses
2. a single effective execution/payment policy resolver

But it must NOT:
- create payment sessions
- add new checkout behavior
- widen customer self-service on its own
- bypass TourSalesModePolicyService
- silently upgrade assisted/external flows into self-service

## Goal
Make RFQ response-level supplier policy explicit and reusable across the system, so execution/payment gating can be driven by one composed policy decision.

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Required scope

### A. Supplier policy fields on RFQ responses
Add the minimum supplier-declared commercial policy fields to `SupplierCustomRequestResponse`.

Recommended minimal direction:
- supplier_declared_sales_mode
- supplier_declared_payment_mode
- optionally a narrow explicit execution mode field if needed
or another equally minimal schema, but keep it small and clear

The response row should become the source of supplier commercial intent for RFQ cases.

Do not overdesign.

### B. Validation rules
On supplier response creation/update:
- validate allowed combinations of the new policy fields
- reject inconsistent or unsafe combinations
- do not allow future-only/unsupported combinations unless explicitly needed now

Examples of things to reason about:
- `full_bus` + `platform_checkout`
- `assisted_closure` + self-service flags
- external-like combinations that should never expose platform checkout

Keep validation conservative.

### C. Effective commercial execution/payment resolver
Add one clear resolver/read model that composes:
- Tour policy (`TourSalesModePolicyService`)
- supplier-declared response policy
- Track 5a resolution kind/status
- platform invariants

This resolver should produce an **effective execution/payment policy read** that can answer at least:
- self_service_preparation_allowed
- self_service_hold_allowed
- platform_checkout_allowed
- assisted_only
- external_only
- blocked_reason / code where useful

Use names that fit the codebase, but keep the concept unified.

### D. Admin/read exposure
Expose the supplier-declared RFQ response policy and the effective/composed policy in the appropriate admin reads.

Minimum acceptable:
- admin custom-request detail includes enough data to inspect selected response policy
- bridge/admin detail can surface effective policy read where relevant

Customer/supplier exposure can remain narrow if needed in this slice.

### E. Integrate resolver into 5b.2 execution gate
Update bridge execution entry logic so that it uses the new effective resolver in addition to / instead of the current narrower tour-only decision.

Required outcome:
- execution and hold are allowed only when the **effective** policy allows them
- assisted/external supplier intent must block self-service even if tour mechanics look per-seat capable

### F. Keep payment out of scope
Do not add:
- payment entry creation
- bridge-specific payment route
- payment UI
- payment session generation

This track only prepares the policy layer that later payment-facing slices will use.

## Strong constraints
Do NOT implement:
- new payment behavior
- customer quote comparison UI
- customer self-selection among responses
- broad supplier portal redesign
- broad auth rewrite
- broad handoff rewrite
- marketplace redesign
- automatic policy snapshot/versioning unless truly minimal and necessary

## Must-not-break rules
You must explicitly preserve:
- current tours/order/payment semantics
- current reservation/payment services
- current standard Mini App booking routes
- current private bot booking routes
- current supplier publication flow
- current Track 4 request/response behavior
- current Track 5a resolution behavior
- current Track 5b.1 bridge persistence behavior
- current Track 5b.2 bridge execution entry behavior where still valid
- current migrate -> deploy -> smoke discipline

## Modeling rule
Supplier-declared RFQ policy is the source of truth for RFQ commercial intent.
Layer A tour policy is the source of truth for execution mechanics.
Effective runtime policy must be the composition of both, plus request resolution/platform rules.

Do not let route handlers invent these rules ad hoc.

## Testing scope
Add focused tests for:
- supplier RFQ response policy field validation
- effective resolver output for key combinations
- per-seat self-service allowed only when both supplier and tour allow it
- assisted/external supplier intent blocks self-service even on per-seat-capable tour
- platform checkout allowed only when effective policy allows it
- Track 5b.2 execution path now uses the effective resolver
- no regression in Tracks 5a / 5b.1 / 5b.2
- no regression in normal customer booking flow

## Before coding
First summarize:
1. exact files/modules you plan to touch
2. whether migrations are needed
3. the exact response fields and effective resolver shape you will add
4. what remains explicitly postponed after 5b.3a

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current supplier-declared RFQ policy behavior now supported
6. current effective resolver behavior now supported
7. compatibility notes against Tracks 0–5b.2
8. postponed items