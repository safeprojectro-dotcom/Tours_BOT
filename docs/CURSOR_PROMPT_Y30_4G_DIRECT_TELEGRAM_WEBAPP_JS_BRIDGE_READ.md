Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and multiple completed runtime identity investigations.

This is a narrow implementation step.
Do NOT return another diagnosis-only answer.
Implement the narrowest direct runtime read of Telegram WebApp JS bridge identity in the current Flet Mini App.

## Confirmed current state
The following approaches were already tried and are NOT sufficient in live Telegram mobile runtime:
- page.route query parsing
- page.url query parsing
- page.url fragment parsing
- page.query mapping parsing
- nested tgWebAppData/init_data parsing if surfaced through page objects
- QueryString normalization

Live behavior still remains:
- catalog works
- user-scoped screens fail closed:
  - /bookings
  - /my-requests
  - /settings

## Confirmed diagnosis
Current Python-side Mini App runtime still does not reliably receive Telegram identity through Flet page surfaces in real mobile Telegram runtime.

Therefore the next required step is:
read Telegram identity directly from the Telegram WebApp JS bridge in the browser/webview runtime.

## Goal
Implement direct Telegram WebApp JS bridge identity extraction and wire it into the Mini App session identity used by user-scoped screens.

## Required identity source
Prefer direct read from:
- `window.Telegram.WebApp.initDataUnsafe.user.id`

Optionally, only if needed:
- parse `window.Telegram.WebApp.initData`

## Required behavior
When Mini App is opened from real Telegram:
- read Telegram WebApp JS bridge directly at runtime
- extract current Telegram user id
- set app-level resolved Telegram identity
- propagate to:
  - My bookings
  - booking detail
  - My requests
  - request detail
  - Settings save path
- keep fail-closed if identity truly absent
- do NOT reintroduce shared dev fallback
- do NOT weaken privacy isolation

## Implementation constraints
1. Use the narrowest compatible mechanism available in current Flet runtime:
   - JS eval / web bridge / page-level JS execution / supported runtime callback
2. Do not redesign Mini App broadly.
3. Do not change booking/request domain logic.
4. Do not touch supplier architecture.
5. Do not disable fail-closed protection.

## Strong requirement
Do not stop with “cannot be accessed” unless you have explicitly verified the concrete Flet runtime capability available in this app and shown why it cannot work.
If a direct bridge read is possible, implement it.

## Safe tracing
If temporary tracing is needed:
- log only whether Telegram WebApp object exists
- whether user.id was found
- which source branch resolved identity
Do NOT log raw initData or full payload values.

## Before coding
Output briefly:
1. exact Flet-compatible mechanism you will use to read JS bridge
2. likely files to change
3. risks
4. expected user-visible change after deploy

## Required tests
Add/update focused tests for:
1. direct JS bridge identity path resolves user.id
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
5. exact JS bridge mechanism implemented
6. what user-visible behavior should now work
7. whether any temporary instrumentation remains or was removed
8. compatibility notes