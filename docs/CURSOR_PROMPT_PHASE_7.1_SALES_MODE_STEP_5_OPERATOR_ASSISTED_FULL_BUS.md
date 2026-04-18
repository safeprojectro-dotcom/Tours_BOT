Implement **Phase 7.1 / Sales Mode / Step 5** as a narrow operator-assisted full-bus path.

Current confirmed continuity:
- Step 1 completed: `tour.sales_mode` is the source of truth
- Step 2 completed: backend/service-layer sales mode policy exists
- Step 3 completed: Mini App read-side adaptation exists
- Step 4 completed: private bot read-side adaptation exists
- production schema drift incident was already fixed by applying the Railway migration
- do not reopen old Phase 7 followup/operator chain broadly

## Goal
Make the `full_bus` path explicit and operationally structured through an assisted/operator-oriented flow, while keeping it fully separate from direct self-service whole-bus booking.

## What already exists
Right now:
- `per_seat` keeps normal self-service behavior
- `full_bus` avoids misleading self-service booking
- `full_bus` already routes into the existing assistance/contact/handoff path

This step should improve that assisted path so it carries clearer structure and context.

## Safe scope
You may implement only the narrowest slice needed to make operator-assisted full-bus handling cleaner and more explicit.

Allowed scope:
1. add explicit structured handoff/support reason/category for full-bus sales mode
2. preserve tour context in the assistance path
3. preserve sales-mode context in the assistance path
4. improve existing handoff/contact payload so operator-side handling can distinguish:
   - regular support/help
   - full-bus commercial request
5. reuse existing handoff/contact surfaces carefully instead of inventing a separate operator system

## Preferred outcome
For a `full_bus` tour:
- the user reaches an assistance/operator-oriented path
- the assistance request carries enough context so the operator does not need to rediscover basic tour context manually
- the system clearly knows this is a full-bus commercial path, not a standard per-seat self-service request

## Must NOT implement
Do not implement:
- direct whole-bus reservation creation
- whole-bus self-service payment
- duplicate tour records as a workaround
- full-bus pricing engine
- `full_bus_price`
- `bus_capacity`
- broad rewrite of old Phase 7 handoff/operator chain
- broad refactor of reservation engine
- modifications to `TemporaryReservationService` unless absolutely unavoidable
- modifications to `reservation_creation.py` unless absolutely unavoidable
- any logic that interprets “many seats” as “whole bus”

## Important production guardrail
Do not introduce changes that require a new DB migration unless truly necessary for this narrow slice.
If a migration becomes necessary, explain why before finalizing.
Prefer reusing existing metadata/context fields if possible.

## Files to prefer
Touch only the files truly needed for this slice.
Prefer existing boundaries around:
- handoff/contact creation
- private bot support routing
- Mini App support routing if already involved
- structured metadata/context passed into handoff/support records

## Tests
Add focused tests only:
- full-bus assisted path creates/uses the correct structured reason/context
- per-seat flows remain unchanged
- existing support/handoff behavior for non-full-bus paths is not broken
- no misleading self-service path is exposed for full-bus tours

## Before coding
First summarize:
1. what Steps 1–4 already completed
2. what exact operator-assisted gap still remains
3. exact files you plan to touch
4. whether you can avoid a migration
5. what remains explicitly postponed after this step

## After coding
Report:
1. files changed
2. whether a migration was needed
3. what full-bus assisted behavior was added
4. tests run
5. results
6. what remains postponed