Continue the already started work for `CURSOR_PROMPT_PHASE_7.1_SALES_MODE_STEP_1`, but narrow and correct the implementation before proceeding further.

This is still **Phase 7.1 / Sales Mode / Step 1** only.

## Context
The previous prompt for Step 1 has already been launched.
Do **not** restart the slice from scratch.
Do **not** broaden scope.
Do **not** move into Step 2.

Treat this message as a correction and tightening of Step 1 scope.

## Current track
- active track: **Phase 7.1 — tour sales mode**
- old Phase 7 followup/operator track is considered closed enough for staging/MVP
- do not reopen old Phase 7 micro-slices unless explicitly requested

## Step 1 goal
Implement only the **admin/source-of-truth field layer** for tour sales mode.

The primary source of truth is:
- `tour.sales_mode`

Initial supported values:
- `per_seat`
- `full_bus`

## Critical correction to prior plan
The safest Step 1 is primarily about introducing and exposing `sales_mode`.

Do **not** accidentally turn Step 1 into:
- booking policy implementation
- pricing policy implementation
- availability policy implementation
- Mini App adaptation
- private bot adaptation
- operator-assisted full-bus flow
- direct whole-bus booking flow

## What to implement now
Implement only the minimum safe Step 1 slice:

1. Add a `TourSalesMode` enum with:
   - `per_seat`
   - `full_bus`

2. Add `sales_mode` to the `Tour` model
   - default must be compatible with existing tours
   - existing tours must safely land on `per_seat`

3. Expose `sales_mode` through admin-facing read/write surfaces:
   - ORM
   - migration
   - admin schemas
   - admin create/update payloads
   - admin list/detail read models

4. Keep validation narrow:
   - valid enum values only
   - backwards-compatible default behavior for existing tours

## Important narrowing on `full_bus_price`
If the earlier in-progress code already started touching `full_bus_price`, handle it carefully:

- prefer the narrowest safe implementation
- do **not** make Step 1 depend on commercial policy beyond source-of-truth needs
- do **not** introduce customer-facing use of `full_bus_price`
- do **not** introduce booking/payment logic based on `full_bus_price`

Preferred approach:
- either keep Step 1 to `sales_mode` only
- or, if `full_bus_price` is already partially introduced and removing it would create churn, keep it as a **nullable admin-only field** with no downstream behavior

If `full_bus_price` remains in Step 1:
- it must stay optional / non-blocking unless the design doc explicitly requires hard enforcement
- it must not be used by Mini App, private bot, booking, or payment flows yet

## What must NOT change
Do not change:
- public booking behavior
- payment behavior
- Mini App behavior
- private bot booking behavior
- operator handoff/followup code
- availability calculations
- seat logic
- reservation semantics
- payment semantics
- old Phase 7 group/operator chain

Do not implement:
- “many seats” => “whole bus”
- any direct whole-bus booking flow
- any UI-only ad hoc policy
- any service-layer booking policy beyond narrow admin validation for Step 1

## File discipline
Touch only the files actually required for this slice.
Do not expand into unrelated refactors.
Do not modify test infrastructure like `tests/unit/base.py` unless strictly required.

## Testing scope
Keep tests focused and narrow:
- migration/default compatibility for existing tours
- admin read exposure of `sales_mode`
- admin create/update persistence of `sales_mode`
- if `full_bus_price` remains, verify admin read/write compatibility only
- confirm existing related admin behavior is not regressed

Do not add broad tests for customer flows.

## Before coding
First print a short correction summary:
1. what the earlier Step 1 plan got right
2. what is being narrowed now
3. exact files you will touch
4. what remains explicitly postponed

## After coding
Report:
1. files changed
2. migrations added/updated
3. tests run
4. results
5. explicitly postponed items