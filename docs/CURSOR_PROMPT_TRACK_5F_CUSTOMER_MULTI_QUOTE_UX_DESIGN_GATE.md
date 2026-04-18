Do not implement application code yet.

Run a design/decision gate for **Track 5f — Customer Multi-Quote UX**.

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
- Track 5e — bridge supersede / cancel lifecycle

Current system already supports:
- RFQ intake
- supplier responses
- admin winner selection
- bridge creation
- bridge execution
- payment continuation through Layer A
- My Requests hub
- bridge lifecycle close/replace

## Core principle
Supplier/admin policy remains authoritative for commercial intent.
Layer A remains authoritative for booking/payment truth.
Customer UX must not invent commercial states or bypass admin/supplier governance.

## Critical rule
This gate must decide whether and how customers should see multiple supplier proposals in Mini App / customer-facing RFQ views.

This is a design gate only.
Do not implement code.

## Goal
Define the minimal safe customer-facing UX for multi-quote visibility, comparison, and continuation, if any, without:
- collapsing admin winner selection
- exposing unsafe or confusing supplier internals
- creating a fake “open marketplace bidding” UX
- creating a second execution/payment truth

## Mandatory docs to use
- docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md
- docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/MINI_APP_UX.md
- COMMIT_PUSH_DEPLOY.md

## Required decision areas

### A. Should customers see multiple quotes at all?
Compare realistic options:
- no multi-quote visibility
- summary only (“we received offers”)
- limited comparison cards
- full quote comparison UI

### B. Who remains decision-maker?
Clarify whether:
- admin still selects winner
- customer may choose among quotes
- customer sees quotes but cannot choose
- supplier proposals remain partially hidden

### C. Safe information exposure
Decide what customer may safely see:
- price
- route summary
- date range
- notes
- boarding assumptions
- sales/payment mode summary
- supplier identity or anonymized supplier label

### D. Relationship to existing 5a / 5b / 5e flows
Clarify how multi-quote UX would interact with:
- selected response
- booking bridge
- terminal bridge lifecycle
- My Requests hub
- active Layer A order

### E. UX entry points
Decide where multi-quote UX should appear, if approved:
- My Requests detail
- dedicated comparison screen
- RFQ detail only after admin review
- not in bridge flow

### F. CTA rules
Define allowed customer-facing actions:
- view offers
- request help
- continue booking
- continue payment
- choose offer
- no direct action

Make clear what is allowed now vs later.

### G. Risk controls
Address:
- stale quote risk
- mismatch between quote and selected bridge
- policy mismatch
- supplier identity exposure risk
- customer confusion if a quote exists but is not selected

### H. Minimum safe rollout order
If implementation is approved later, define the smallest safe rollout.

## Required output
Produce a concise but concrete design result including:

1. current state summary
2. comparison of 2–4 realistic UX models
3. final recommendation
4. customer visibility rule
5. CTA/actionability rule
6. interaction with current bridge/order/payment flows
7. minimum safe rollout order
8. must-not-break reminder

## Constraints
- no code
- no migrations
- no payment redesign
- no bridge redesign
- no broad marketplace rewrite
- keep this as design-only

## Before doing anything
Summarize:
1. what current customer RFQ UX already supports
2. what multi-quote gap remains
3. which docs you will use/reference

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. what customer should and should not see
4. how this should interact with bridge/actionability
5. exact next safe implementation step if approved