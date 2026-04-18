Implement **Track 2 — Supplier Admin Foundation** from the approved supplier marketplace design package.

## Preconditions already completed
- Track 0 completed: frozen core documented in `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- Track 1 completed: design package aligned and accepted
- current core booking/payment/Mini App/private-bot flows must remain stable

## Critical rule
This track is an **additive extension layer**.
It must not replace or silently redefine the current Core Booking Platform Layer.

Everything in Layer A remains protected.

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

## Goal
Introduce the first real supplier-admin foundation so suppliers can begin forming offers/products inside the platform without breaking existing customer-facing booking flows.

## Required scope

### A. Supplier domain foundation
Add the minimum safe supplier-side model needed for future marketplace work.

This should cover:
- supplier entity
- supplier account / ownership relationship
- supplier-owned offer/tour relation or equivalent safe ownership model

Preferred rule:
- preserve existing core tours behavior
- do not force a destructive rewrite of current `tour` usage
- if current `tour` must be extended, do it minimally and compatibly
- if a separate supplier-owned wrapper/offer structure is cleaner, prefer that

### B. Supplier-admin surface
Add the first protected supplier-admin API/backend layer for:
- list own supplier-owned offers
- view own offer detail
- create own offer
- update own offer
- manage draft/publish-readiness state

### C. Supplier-side offer formation fields
Support the minimum viable supplier configuration for:
- title / description / program
- departure / return timing
- transport or vehicle metadata
- capacity metadata
- service composition
- sales mode
- payment mode
- draft/publish-readiness

Do this in the narrowest safe way.

### D. Compatibility and ownership rules
Must enforce:
- supplier can manage only own supplier-side objects
- central admin visibility remains possible where needed
- current admin/tour/customer flows remain intact
- future publication track can use the resulting supplier-owned objects

## Strong constraints
Do not implement yet:
- request marketplace
- request broadcast to suppliers
- supplier response bidding
- whole-bus direct self-service booking
- new payment execution logic
- replacement of current order lifecycle
- replacement of current `tour` catalog by supplier objects
- broad auth rewrite
- broad refactor of old Phase 7 grp_followup_* logic

## Must-not-break rules
You must explicitly preserve:
- current per-seat booking semantics
- current payment semantics
- current reservation timer semantics
- current Mini App routes and stable expectations
- current private bot routes and CTA behavior
- current assisted full-bus path
- current sales_mode semantics
- current migration/deploy safety rule: migrate → deploy → smoke

## Migration rule
Migrations are allowed only if truly necessary for this track.
If you introduce migrations:
- keep them minimal
- explain why they are required
- keep backward compatibility explicit
- do not create schema churn without clear need

## Testing scope
Add focused tests for:
- supplier entity / ownership basics
- supplier can create/update/list own offers
- supplier cannot modify another supplier’s objects
- central admin compatibility where relevant
- current customer-facing per-seat/full-bus assisted behavior not broken

Prefer focused tests over broad unrelated regressions.

## Before coding
First summarize:
1. how Track 2 fits on top of Track 0 and Track 1
2. exact files/modules you plan to touch
3. whether migrations are needed
4. what remains explicitly postponed after Track 2

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. compatibility notes against Track 0
6. postponed items