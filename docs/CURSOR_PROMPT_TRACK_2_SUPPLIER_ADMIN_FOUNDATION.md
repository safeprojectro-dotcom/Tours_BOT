Implement **Track 2 — Supplier Admin Foundation** from the approved supplier marketplace design package.

## Context
The current Tours_BOT core must remain stable:
- existing tours/reservations/orders/payments/handoffs remain valid
- existing per-seat booking flows must not break
- existing Mini App and private bot flows must not break
- existing Phase 7.1 `sales_mode` implementation must remain compatible

This is a large vertical implementation pack.
Do not split it into micro-slices unless absolutely necessary.

## Goal
Introduce the foundational supplier-side model and supplier-admin surface needed for supplier-owned offer formation.

## Required scope
Implement the minimum viable supplier-admin foundation covering:

### A. Supplier domain model
Add foundational entities or equivalent structures for:
- supplier
- supplier account / supplier admin ownership
- supplier-owned offer/tour relation

Do this in the safest way that preserves current core tour behavior.

### B. Supplier-scoped offer formation
Support supplier-side configuration for at least:
- title / description / program
- departure / return timing
- transport / vehicle metadata
- capacity metadata
- service composition
- sales mode
- payment mode
- publish readiness state / draft state

### C. Supplier admin API / surface
Add the first protected supplier-admin API or backend surface for:
- create supplier offer
- edit supplier offer
- list own offers
- view own offer detail
- change offer draft/publish readiness state

### D. Compatibility layer
Ensure that:
- existing central admin still works
- existing tours are not broken
- supplier-owned offers can later participate in publication flow
- no customer-facing flow is broken by this step

## Strong constraints
Do not implement yet:
- request marketplace flow
- broadcast to suppliers
- supplier response bidding
- direct whole-bus self-service booking
- payment execution changes
- major refactor of existing reservation engine
- replacement of existing tour catalog
- broad auth redesign beyond what is needed for safe supplier scoping

## Preferred implementation strategy
- extend current core safely
- avoid rewriting current `tour` flow from scratch
- keep business logic in services
- keep repositories persistence-oriented
- keep schemas explicit
- use migrations only if actually needed
- if new tables are required, keep them minimal and aligned with future publication/request layers

## Tests
Add focused tests for:
- supplier entity / ownership basics
- supplier can create and update own offer
- supplier cannot modify чужие offers
- current central admin and current tour flows are not broken
- current customer-facing per-seat/full-bus assisted behavior is not broken

## Before coding
First summarize:
1. approved design assumptions
2. exact files/modules you will touch
3. whether migrations are needed
4. what remains explicitly postponed after this track

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. compatibility notes
6. postponed items