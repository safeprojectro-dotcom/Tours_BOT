Implement **Track 0 — Freeze And Preserve Current Core** from `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`.

Do not implement supplier marketplace features yet.

## Context
The project now has:
- original core Tours_BOT implementation
- Phase 7.1 sales mode work already completed
- new design package:
  - `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
  - `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
  - `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

Before starting supplier-admin and marketplace implementation, we must explicitly freeze the current stable core and define compatibility boundaries.

## Goal
Create a clear compatibility baseline for the already implemented Core Booking Platform Layer so future supplier-marketplace tracks do not break it.

## Required scope
This is a documentation + verification + guardrail step.

### A. Define the frozen core
Explicitly document the current stable core, including:
- existing tours catalog flow
- current per-seat booking flow
- temporary reservation lifecycle
- payment entry / reconciliation baseline
- Mini App current stable behavior
- private bot current stable behavior
- current `sales_mode` support
- assisted full-bus path
- structured full-bus assistance path
- production migration dependency already learned from Railway incident

### B. Define compatibility contracts
Document what future tracks must preserve:
- current per-seat booking semantics
- current payment semantics
- current reservation timer semantics
- current Mini App routes and basic expectations
- current private bot route/CTA expectations
- current admin-side baseline behavior where already implemented

### C. Define must-not-break checklist
Produce a compact but explicit must-not-break list for:
- booking core
- payment core
- Mini App
- private bot
- handoff baseline
- migrations/deploy expectations

### D. Define baseline smoke checks
Document the minimum local/staging/production smoke checklist that must pass before and after each future supplier-marketplace track.

### E. Update project continuity docs
Update the docs that should now reflect the freeze baseline, likely:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- optionally `COMMIT_PUSH_DEPLOY.md` if deploy-critical notes need tightening

## Constraints
- do not add new features
- do not add new DB tables
- do not refactor current code broadly
- do not reopen old Phase 7 chain
- do not start supplier admin implementation yet

## Before doing anything
Summarize:
1. what is currently part of the frozen core
2. what recent incidents prove must be guarded (for example migration/schema drift)
3. which docs you will update

## After completion
Report:
1. files changed
2. frozen core summary
3. must-not-break checklist created
4. baseline smoke checks documented
5. exact next safe track after Track 0