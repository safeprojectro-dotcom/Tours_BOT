Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and recent Mini App runtime identity hotfixes.

Это узкий session continuity hotfix step.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не трогать supplier conversion bridge шире необходимого.

## Confirmed live behavior
Mini App is opened from real Telegram successfully.
Public/read-only catalog surfaces work.

But user-scoped screens still fail closed with:
"Unable to verify your Telegram identity for this session. Reopen the Mini App from Telegram."

Affected screens include:
- My bookings
- My requests
- Settings

This means the issue is no longer shared dev fallback leakage.
The remaining bug is that resolved Telegram identity is not surviving / propagating correctly through the live Mini App session and internal navigation.

## Goal
Fix Telegram identity session continuity inside Mini App so that when Mini App is opened from Telegram:
- the resolved Telegram user identity is preserved for the active Mini App session
- My bookings works
- My requests works
- Settings save path works
- fail-closed remains only for truly unresolved identity cases

## What to inspect
1. How Telegram identity is first resolved on Mini App startup in real Telegram runtime
2. Whether Telegram init data / launch params are read correctly on first load
3. Whether resolved identity is stored in page/session/app state after initial resolution
4. Whether internal route navigation to:
   - /bookings
   - /my-requests
   - /settings
   loses the resolved identity
5. Whether these screens incorrectly depend only on route/query params instead of session-resolved identity
6. Whether catalog route works because it is public, while user-scoped routes have no continuity source
7. Whether page reload / navigation path differs between Telegram mobile and tests

## Expected behavior after fix
When Mini App is opened from Telegram:
- resolved Telegram identity is established once
- user-scoped screens reuse the same session identity
- My bookings shows the correct current user's data
- My requests shows the correct current user's data
- Settings can read/save for the correct current user
- missing identity still fails closed
- no unsafe shared fallback is reintroduced

## Constraints
Do NOT:
- re-enable unsafe shared dev fallback in live runtime
- redesign the Mini App broadly
- redesign bookings or requests domain
- change supplier architecture
- do unrelated refactors

## Likely files
Likely:
- mini_app/app.py
- mini_app/api_client.py
- mini_app/config.py if strictly needed
- maybe minimal user-context/session helper if already aligned with current architecture
- focused tests for live-like session continuity

## Strong requirement
Do not stop at route/query identity only.
If real Telegram runtime resolves identity only once at startup, preserve that identity across internal Mini App navigation safely.

## Before coding
Output briefly:
1. exact suspected continuity break
2. likely files to change
3. why catalog works while user-scoped screens fail
4. risks

## Required tests
Add/update focused tests for:
1. Telegram-resolved identity persists across internal navigation to bookings
2. Telegram-resolved identity persists across internal navigation to my-requests
3. Telegram-resolved identity persists across settings save path
4. missing identity still fails closed
5. no shared cross-user leakage is reintroduced

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. exact root cause confirmed
6. what continuity path was fixed
7. compatibility notes