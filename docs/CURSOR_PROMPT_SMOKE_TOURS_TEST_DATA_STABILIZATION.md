Add a very small **test-data stabilization** slice for smoke tours.

Do not change booking/payment logic or marketplace logic.

## Goal
Prevent smoke tests from failing just because demo/test tours are in the past.

## Problem
Current test/smoke tours can expire by date, causing false negatives in Mini App booking smoke checks even when the system itself is healthy.

## Required scope
Introduce a minimal dev/staging support mechanism that ensures there are always a few future-dated smoke tours available.

## Preferred solution
Implement a small utility/script, not a broad product feature.

Preferred direction:
- create or refresh 1–2 dedicated smoke tours
- if they already exist but are outdated, move them into the future
- keep them bookable
- keep boarding points valid
- keep the change isolated from Layer A business rules

## Suggested smoke tour codes
Use stable codes like:
- `SMOKE_PER_SEAT_001`
- `SMOKE_FULL_BUS_001`

## Minimum guarantees
For each smoke tour:
- departure_datetime is in the future
- return_datetime is after departure
- sales_deadline is in the future
- status is a valid sale/open state
- at least one boarding point exists
- seats/capacity are valid for booking smoke

## Constraints
Do NOT:
- redesign admin UI
- redesign booking rules
- touch payment flows
- change marketplace logic
- add customer-facing functionality
- add broad seed framework unless truly minimal

## Acceptable implementation forms
One of:
- a small script such as `python -m app.scripts.ensure_smoke_tours`
- or an equally minimal internal utility

## Docs
Update only the minimum necessary docs/runbook so the team knows how to refresh smoke tours.

## Before coding
Summarize:
1. exact files to change
2. whether this will be a script or another minimal mechanism
3. what stays out of scope

## After coding
Report:
1. files changed
2. how to run the smoke-tour refresh
3. whether existing tours are updated or recreated
4. tests/checks run
5. result
