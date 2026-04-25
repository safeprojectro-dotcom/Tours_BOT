Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and recent Mini App identity/runtime tracing work.

Это narrow Telegram JS-bridge identity fix step.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не трогать supplier conversion bridge шире необходимого.

## Confirmed live behavior
Mini App opens from real Telegram mobile runtime.
Catalog works.
User-scoped screens still fail closed:
- /bookings
- /my-requests
- /settings

Previous fixes expanded URL/query/fragment/tgWebAppData parsing, but live behavior still shows unresolved identity.

## Strong working hypothesis
Real Telegram mobile runtime for this Mini App is exposing identity through Telegram WebApp JS bridge rather than through the Flet route/url/query surfaces currently relied upon.

Current code path still does not explicitly read:
- `window.Telegram.WebApp.initDataUnsafe`
- `window.Telegram.WebApp.initData`

## Goal
Add safe runtime identity resolution from Telegram WebApp JS bridge and use it as a first-class identity source for Mini App session continuity.

## Required behavior
When Mini App is opened from real Telegram:
- read Telegram WebApp bridge identity safely
- extract current Telegram user id from JS bridge payload
- establish app-level resolved Telegram identity
- reuse it for:
  - My bookings
  - My requests
  - Settings
- keep fail-closed when identity truly absent
- do NOT reintroduce shared dev fallback

## What to inspect and implement
1. Determine how Flet web runtime can safely access Telegram WebApp JS bridge in this app:
   - JS eval / page bridge / existing web runtime hook
   - the narrowest supported mechanism already compatible with current app

2. Read from:
   - `window.Telegram.WebApp.initDataUnsafe.user.id` when present
   - optionally fall back to parsing `window.Telegram.WebApp.initData` if needed and safe

3. Preserve precedence carefully:
   - if an existing trusted resolved runtime identity already exists, do not weaken it
   - JS bridge should become a supported identity source for real Telegram launch, not a broad unsafe override

4. Store the resolved identity at app/session level and apply it to user-scoped screens.

5. Keep:
   - fail-closed on unresolved identity
   - no shared dev fallback in production runtime
   - no cross-user leakage

## Safe tracing guidance
If temporary tracing is needed, keep it minimal and non-sensitive:
- log whether JS bridge exists
- whether user.id was found
- which identity source won
Do NOT log raw initData or full payload contents.

## Constraints
Do NOT:
- redesign Mini App broadly
- redesign bookings/requests domain
- change supplier architecture
- re-enable unsafe fallback
- disable fail-closed protection

## Likely files
Likely:
- mini_app/app.py
- possibly mini_app/config.py only if strictly needed for safe tracing toggle
- focused tests for JS bridge identity path
- maybe a tiny helper for runtime JS-bridge extraction if it fits current architecture

## Before coding
Output briefly:
1. exact plan to read Telegram JS bridge identity in current Flet runtime
2. likely files to change
3. risks
4. why previous URL/query-based fixes were insufficient

## Required tests
Add/update focused tests for:
1. JS bridge user.id identity path resolves correctly
2. resolved identity reaches /bookings
3. resolved identity reaches /my-requests
4. resolved identity reaches /settings
5. missing identity still fails closed
6. no shared cross-user leakage is reintroduced

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. exact root cause confirmed
6. what JS bridge path was added/fixed
7. whether any temporary instrumentation remains or was removed
8. compatibility notes