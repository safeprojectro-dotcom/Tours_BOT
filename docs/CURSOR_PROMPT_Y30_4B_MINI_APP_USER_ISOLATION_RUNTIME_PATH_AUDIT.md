Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and handoff.

Это узкий runtime/code-path audit + hotfix step.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не трогать supplier conversion bridge шире необходимого.
Нужно проверить реальный кодовой путь Mini App user isolation, потому что после предыдущего hotfix live behavior still appears unchanged.

## Confirmed problem
After the previous Mini App user-isolation hotfix, live testing still shows that different Telegram users can see the same data in:
- `My bookings`
- `My requests`

Expected behavior is still NOT achieved in real runtime.

So the previous fix was either:
- incomplete,
- not applied to the real runtime path,
- or another shared identity path still exists.

## Goal
Audit the actual code path used by Mini App runtime for user-scoped screens and eliminate any remaining shared/fallback identity leakage.

## What must be verified in code
Check end-to-end identity flow for real runtime, not just tests:

1. How Mini App determines current Telegram identity on startup
2. How route/query/init-data identity is parsed
3. Where `MINI_APP_DEV_TELEGRAM_USER_ID` or equivalent fallback can still leak
4. Whether `My bookings` screen uses the same identity source as `My requests`
5. Whether booking detail / request detail use the same source
6. Whether settings / language save path can overwrite or pin a shared identity
7. Whether cached page/session/global state survives across users
8. Whether any API client defaults to a shared telegram_user_id
9. Whether any backend endpoint still accepts missing identity and returns shared data
10. Whether actual real runtime path differs from the tested path

## Required audit output
Before changing code, explicitly identify:
- the exact runtime path for `My bookings`
- the exact runtime path for `My requests`
- all places where telegram_user_id can be sourced, cached, defaulted, or overridden
- the exact remaining leakage point(s), if found

## Expected behavior after fix
- User A sees only A bookings/requests
- User B sees only B bookings/requests
- missing identity fails closed
- no shared dev fallback is used in real runtime user-scoped screens
- no page/session/global cached identity causes cross-user leakage

## Constraints
Do NOT:
- redesign bookings domain
- redesign requests domain
- redesign Mini App broadly
- change supplier architecture
- do unrelated cleanup
- keep any unsafe real-runtime fallback behavior

## Likely files
Likely:
- `mini_app/app.py`
- `mini_app/config.py`
- `mini_app/api_client.py`
- user-scoped Mini App screen wiring
- backend Mini App endpoints only if a remaining unsafe path exists there
- focused tests

## Strong requirement
If the bug cannot be reproduced in unit tests, add the narrowest test(s) that capture the actual failing runtime path.
Do not stop at "tests pass" if real runtime path still leaks.

## Before coding
Output briefly:
1. suspected remaining leakage path(s)
2. likely files to inspect/change
3. why previous fix may not have covered the real runtime path
4. risks

## Required tests
Add/update focused tests for:
1. My bookings isolation across two users in the actual runtime identity path
2. My requests isolation across two users in the actual runtime identity path
3. no shared cached/default identity across screens
4. missing identity fail-closed
5. valid single-user behavior still works

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. exact root cause confirmed
6. what code path was fixed
7. compatibility notes