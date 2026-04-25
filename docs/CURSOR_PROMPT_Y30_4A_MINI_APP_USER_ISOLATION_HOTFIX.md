Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and handoff.

Это узкий hotfix step.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не трогать Design 1 / supplier conversion bridge work шире необходимого.
Исправить только подтверждённый баг изоляции пользовательских данных в Mini App.

## Confirmed bug
During live testing with two different Telegram accounts, the Mini App sections:
- `My bookings`
- `My requests`

showed the same data for different users.

This means user-specific data isolation is currently broken or bypassed.
This is a high-severity privacy/data-isolation bug.

The likely issue is that Mini App identity resolution is leaking/shared/falling back incorrectly
(e.g. shared dev user context, incorrect telegram user propagation, bad fallback behavior, or missing per-user filtering).

## Goal
Fix Mini App user isolation so that:
- each Telegram user sees only their own `My bookings`
- each Telegram user sees only their own `My requests`
- no shared or leaked cross-user visibility is possible

## Scope
Inspect and fix only the identity resolution / user isolation chain required for:
- Mini App settings/session/user context
- My bookings
- My requests

## What to inspect
1. How Mini App resolves the current Telegram user identity
2. Whether any dev fallback (e.g. `MINI_APP_DEV_TELEGRAM_USER_ID` or equivalent) is leaking into real Telegram runtime
3. How `telegram_user_id` is propagated from Mini App into backend requests
4. How backend endpoints for bookings/requests resolve/filter current user
5. Whether any shared/global/cached user context is reused across sessions
6. Whether any endpoint defaults to a shared user when identity is missing
7. Whether auth/init-data parsing is bypassed or optional in production/runtime paths

## Expected behavior after fix
- User A sees only User A bookings/requests
- User B sees only User B bookings/requests
- If user identity cannot be safely resolved, endpoint/UI must fail closed or show safe empty/error state
- No shared fallback user is allowed in real runtime path

## Constraints
Do NOT:
- redesign the booking domain
- redesign requests domain
- redesign supplier flows
- redesign Mini App conversion bridge
- broaden into unrelated cleanup
- silently keep unsafe fallback identity behavior for real user-facing runtime

## Likely files
Likely:
- Mini App identity/session/client code
- backend Mini App endpoints for bookings/requests/settings
- maybe config/env handling around dev user fallback
- focused tests for multi-user isolation

## Before coding
Output briefly:
1. likely root cause(s)
2. likely files to change
3. risks
4. why this is a narrow high-priority hotfix

## Required tests
Add/update focused tests for:
1. user A and user B see different bookings when data differs
2. user A and user B see different requests when data differs
3. missing/unsafe identity does not leak shared data
4. dev fallback does not affect real runtime path
5. existing bookings/requests functionality remains intact for a valid single user

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. root cause confirmed
6. what was fixed
7. compatibility notes