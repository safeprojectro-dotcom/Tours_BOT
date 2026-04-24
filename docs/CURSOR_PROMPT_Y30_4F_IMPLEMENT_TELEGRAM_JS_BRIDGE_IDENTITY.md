Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- current codebase
- completed diagnosis that Mini App currently does NOT read Telegram WebApp JS bridge directly
- confirmed live issue: catalog works, but /bookings, /my-requests, /settings fail closed in real Telegram mobile runtime

This step is IMPLEMENTATION, not another diagnosis.
Do not stop at analysis.
Do not only restate current code behavior.
You must implement the narrowest safe runtime fix.

## Confirmed diagnosis
Current Mini App runtime reads identity only from Flet/page surfaces:
- page.route query
- page.url query
- page.url fragment query
- page.query mapping
- nested tgWebAppData/init_data only if already present there

It does NOT directly read:
- `window.Telegram.WebApp.initDataUnsafe.user.id`
- `window.Telegram.WebApp.initData`

This is the confirmed missing live-runtime identity source.

## Goal
Implement safe Telegram JS bridge identity extraction for real Telegram Mini App runtime and wire it into app-level resolved identity used by user-scoped screens.

## Required implementation outcome
When Mini App is opened from real Telegram mobile runtime:
- read Telegram WebApp JS bridge directly
- extract `user.id`
- set/respect app-level `_resolved_telegram_user_id`
- propagate that identity to:
  - My bookings
  - booking detail
  - My requests
  - request detail
  - Settings save path
- preserve fail-closed if identity is truly absent
- do NOT reintroduce shared dev fallback
- do NOT weaken privacy isolation

## Scope
Narrow runtime fix only.
No redesign of Mini App.
No redesign of bookings/requests domain.
No supplier architecture changes.
No Layer A / RFQ / payment changes.

## Implementation guidance
1. Use the narrowest supported mechanism in the current Flet runtime to read Telegram WebApp JS bridge.
2. Prefer:
   - `window.Telegram.WebApp.initDataUnsafe.user.id`
3. If needed, optionally parse `window.Telegram.WebApp.initData`, but only if safe and necessary.
4. Preserve current precedence:
   - trusted existing runtime identity sources remain valid
   - JS bridge becomes an additional real runtime source
5. Store resolved identity at app/session level.
6. Re-apply identity to user-scoped screens after it is resolved.
7. Keep missing identity => fail-closed.

## Strong requirement
Do not return only with "Flet cannot do this" unless you have actually verified the supported runtime options in the existing app context and attempted the narrowest compatible implementation path.

## Before coding
Output briefly:
1. exact implementation approach
2. likely files to change
3. risks
4. what user-visible behavior should change after deploy

## Required tests
Add/update focused tests for:
1. JS bridge identity path resolves user.id
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
5. what JS bridge runtime path was implemented
6. exact user-visible behavior restored
7. compatibility notes