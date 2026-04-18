Implement **Phase 7.1 / Sales Mode / Step 2** as a narrow backend/service-layer policy slice.

This step comes strictly after completed Step 1:
- `tour.sales_mode` already exists as source of truth
- Step 1 was admin/source-of-truth only
- do not reopen or modify old Phase 7 followup/operator chain

## Goal
Introduce backend/service-layer interpretation of `tour.sales_mode` while keeping customer-facing behavior unchanged for now.

## Important constraints
This is a backend policy step, not a UI step.

Do not implement:
- Mini App customer behavior changes
- private bot booking flow changes
- direct whole-bus booking flow
- operator-assisted full-bus flow
- payment changes
- seat decrement logic changes
- availability semantics changes unless strictly needed for backend policy shape
- “many seats” => “whole bus”

## What Step 2 should do
Create a narrow backend policy layer that can answer, in one place, how a tour should be treated commercially.

Add service-layer structures/helpers that:
- read `tour.sales_mode`
- expose a normalized policy/read model for downstream consumers
- keep policy owned by backend, not UI

The policy must initially support:
- `per_seat`
- `full_bus`

## Recommended shape
Prefer adding a small dedicated service/module such as:
- `app/services/tour_sales_mode_policy.py`
or equivalent narrow module

This policy layer may provide read-only outputs like:
- effective sales mode
- whether per-seat self-service is allowed
- whether direct customer booking should be blocked/deferred
- whether operator path is required

But keep it narrow and internal.

## Very important
Do not yet wire these policy decisions into Mini App or private bot UI behavior.
This step should make the backend ready for those later slices.

## Safe implementation ideas
- add a dedicated schema/read model for sales-mode policy if useful
- add service methods that return policy for a tour
- optionally expose a backend-internal/admin-safe read endpoint only if needed for testing or future adaptation
- keep all logic factored into one service boundary

## Must NOT change
- no changes to reservation creation flow
- no changes to payment entry/reconciliation
- no changes to current customer-visible reserve/pay paths
- no direct booking block in existing customer surfaces yet
- no operator/handoff workflow changes

## Tests
Add focused unit tests for:
- `per_seat` policy output
- `full_bus` policy output
- no accidental fallback from large seat count to whole-bus mode
- existing tours with default `per_seat`
- regression safety for unchanged existing booking semantics

Do not add broad Mini App/bot tests yet.

## Before coding
Summarize:
1. what Step 1 already completed
2. why Step 2 is backend-only
3. exact files you will touch
4. what remains postponed

## After coding
Report:
1. files changed
2. policy shape introduced
3. tests run
4. results
5. what is still postponed