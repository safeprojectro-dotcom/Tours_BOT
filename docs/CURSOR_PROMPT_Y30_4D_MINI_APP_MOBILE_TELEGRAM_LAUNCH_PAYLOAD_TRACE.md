Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and recent Mini App identity hotfixes.

Это narrow live-runtime tracing + fix step.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не трогать supplier conversion bridge шире необходимого.

## Confirmed live behavior
Mini App is opened from real Telegram mobile runtime.
Public catalog works.
But user-scoped screens still fail closed with:
"Unable to verify your Telegram identity for this session. Reopen the Mini App from Telegram."

Affected:
- /bookings
- /my-requests
- /settings

This means the previous identity extraction fixes still do not match the actual Telegram mobile launch/runtime payload path used by this deployed Mini App.

## Goal
Trace the actual mobile Telegram Mini App launch payload/runtime identity path and fix the real extraction/continuity source used in production mobile Telegram runtime.

## Required approach
Do NOT guess another branch only from unit tests.
Instrument or trace the actual runtime identity inputs used by Mini App startup and internal navigation in the narrowest safe way.

## What to inspect
1. In real Telegram mobile runtime, what identity-related data is actually available on initial app load?
   Check all practical inputs visible to Mini App shell / page runtime:
   - route/query params
   - page URL query
   - page.query mapping
   - Telegram WebApp init data equivalents
   - any JS bridge / launch param surface currently used by Flet/web runtime

2. Determine whether identity is:
   - absent on initial page load,
   - present but differently named,
   - present but encoded,
   - present only in one specific runtime field,
   - present on startup but lost after navigation.

3. Verify whether internal navigation to:
   - /bookings
   - /my-requests
   - /settings
   depends on route-local query only rather than app-level resolved startup identity.

4. Verify whether catalog works because it is public while user-scoped paths have no carried session identity.

## Strong requirement
Before changing behavior, identify the exact real runtime source or exact missing continuity path.
Do not stop at "tests passed" if live mobile Telegram path still fails.

## Safe instrumentation guidance
Use the narrowest safe non-sensitive instrumentation possible.
Do NOT log full Telegram init data or sensitive payloads verbatim.
It is acceptable to log/debug only:
- which source keys are present
- whether a user id was extracted
- which precedence branch was chosen
- whether identity was stored in session/app state
- whether identity is present when navigating to user-scoped routes

## Expected behavior after fix
When opened from real Telegram mobile runtime:
- Mini App resolves Telegram identity from the actual live source
- that identity is preserved for the active Mini App session
- /bookings works
- /my-requests works
- /settings works
- fail-closed remains only for genuinely unresolved identity
- no unsafe shared fallback is reintroduced

## Constraints
Do NOT:
- reintroduce shared dev fallback
- redesign Mini App broadly
- redesign bookings or requests domain
- do unrelated cleanup
- disable fail-closed safety

## Likely files
Likely:
- mini_app/app.py
- possibly mini_app/api_client.py if identity propagation is mixed there
- minimal runtime tracing/debug helper if needed
- focused tests, but tests must reflect the actual traced live path

## Before coding
Output briefly:
1. exact suspected remaining live-path mismatch
2. likely files to inspect/change
3. how you will trace the real runtime source safely
4. risks

## Required tests
Add/update the narrowest tests that match the discovered live path.
Also keep:
1. missing identity still fails closed
2. no shared cross-user leakage
3. valid single-user flows still work

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. exact live-path root cause confirmed
6. what runtime source/continuity path was fixed
7. whether any temporary instrumentation remains or was removed
8. compatibility notes