Продолжаем ЭТОТ ЖЕ проект Tours_BOT.

Нужен узкий hotfix.
Не трогай booking/payment core.
Не трогай RFQ/bridge semantics.
Не делай новый дизайн.
Не расползайся beyond fixing the crashing request detail screen.

## Problem
Mini App route `/my-requests/{id}` crashes in production.

Observed Flet error:
ValueError: at least icon or content (string or visible Control) must be provided

Trace points to:
- `mini_app/app.py`
- `handle_route_change`
- request detail route rendering

`/my-requests` list works, but opening a specific request detail crashes.

## Goal
Fix the request detail UI so it does not construct any Flet control with empty/None content.

## Likely cause
One of the recently added request-detail sections or rows is rendering a control like ListTile / Chip / Banner / similar with:
- empty title
- empty subtitle
- no visible content
- or a conditional block that still instantiates the control even when all fields are missing

Recent likely areas:
- activity preview / current update block
- prepared customer lifecycle message block
- lifecycle/status captions
- any new detail section added in U2 / W2 / W3 / request-detail-related work

## What to do
1. Audit request detail rendering in `mini_app/app.py`
2. Find every control on `/my-requests/{id}` that requires text/content/icon
3. Add safe guards so the control is only created when it has valid visible content
4. If data is missing, either:
   - skip that row/block entirely, or
   - render a safe fallback text
5. Keep the fix minimal and local to the crashing screen

## Must not change
- API contracts
- booking/payment logic
- RFQ/bridge semantics
- notification logic
- supplier/admin workflows
- broad Mini App redesign

## Preferred fix style
- minimal route-level hotfix
- fail-safe conditional rendering
- no fake placeholder semantics
- no empty controls

## Files likely to touch
- `mini_app/app.py`
- maybe tiny helper used by request-detail rendering
- tests if feasible

## Tests required
Add focused tests only if practical:
1. request detail renders when optional blocks are absent
2. activity/message/preview blocks are skipped safely when empty
3. `/my-requests` and `/my-requests/{id}` both remain stable

If Flet UI tree tests are too heavy, keep fix minimal and explain exactly which block was crashing.

## Before coding
Output briefly:
1. likely root cause
2. exact files to change
3. risk
4. what stays out of scope

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests run
4. result
5. exact crashing block found
6. compatibility notes