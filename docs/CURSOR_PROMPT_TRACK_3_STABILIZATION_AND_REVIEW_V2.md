Stabilize and review the completed **Track 3 — Supplier Offer Publication To Telegram Channel**.

Do not add new features.

## Context
Track 3 has already been implemented.
Now perform a strict compatibility and scope review before moving to Track 4.

## Goal
Confirm that the moderated supplier-offer publication layer is additive, controlled, and compatible with the frozen Layer A core and accepted Track 2 foundation.

## What must be reviewed carefully
Review all Track 3 changes, with extra attention to:
- publication state transitions
- moderation/approval enforcement
- Telegram publication path
- CTA/deep-link continuity
- whether any supplier bypass of platform moderation became possible
- whether any Layer A customer-facing behavior changed accidentally

## Required review tasks

### A. Scope creep review
Confirm Track 3 did NOT accidentally introduce:
- request marketplace
- supplier response/bidding logic
- direct whole-bus self-service
- customer checkout changes
- broad content-assistant rewrite
- broad group-bot redesign
- broad auth rewrite

### B. Layer A compatibility review
Confirm Track 3 preserves:
- current tours/order/payment semantics
- current Mini App routes
- current private bot routes
- current `sales_mode` behavior
- current assisted full-bus path
- current admin auth boundary
- current migrate → deploy → smoke rule

### C. Moderation enforcement review
Explicitly explain:
- whether suppliers can directly publish without approval
- whether central admin approval is truly mandatory
- whether rejected offers remain blocked from publication

### D. Docs update
Update the appropriate docs:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`
- optionally `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

### E. Baseline verification
Run the minimum focused checks necessary to support acceptance.

## Before doing anything
Summarize:
1. intended Track 3 scope
2. main compatibility risks
3. exact files/docs to inspect/update

## After completion
Report:
1. files changed
2. whether scope creep was found
3. whether moderation enforcement is correct
4. tests/checks run
5. final compatibility statement
6. exact next safe track