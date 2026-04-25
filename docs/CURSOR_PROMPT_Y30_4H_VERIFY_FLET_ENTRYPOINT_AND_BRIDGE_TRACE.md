Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase.

Это narrow verification/trace step.
Не делать новый speculative runtime fix.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не трогать supplier conversion bridge.

## Current situation
Multiple identity fixes were attempted, including a JS bridge bootstrap through `assets/index.html`, but live Telegram behavior still does not work for:
- /bookings
- /my-requests
- /settings

Catalog still works, so this appears to remain a narrow Mini App identity/runtime issue.

## Goal
Verify the actual live runtime path instead of guessing again.

Need to prove or disprove all of the following:
1. Is `assets/index.html` actually used by the deployed Flet Mini App entrypoint?
2. Does the bootstrap JS in that file actually execute in live Telegram runtime?
3. Is `window.Telegram.WebApp` available at that moment?
4. Is a Telegram user id found there?
5. Is `tg_bridge_user_id` actually injected into browser URL/history?
6. Does Python MiniAppShell ever see that injected key?

## Required approach
Use the narrowest safe instrumentation possible.
Do NOT log raw initData or sensitive payloads.
It is acceptable to log only:
- whether assets/index.html entrypoint is active
- whether bridge object exists
- whether user.id was found
- whether tg_bridge_user_id was injected
- whether Python saw tg_bridge_user_id
- which branch won

## Strong requirement
This step is verification-first.
Do not implement another speculative identity source unless the verification proves the current path is not used.

## Expected output
Before coding:
1. exact verification plan
2. likely files to change
3. risks
4. what evidence will confirm/refute the bootstrap path

After coding:
1. files changed
2. migrations none
3. tests run (if any)
4. what verification instrumentation was added
5. what exact runtime path was confirmed or disproved
6. whether assets/index.html is truly active in production Flet runtime
7. whether Python sees tg_bridge_user_id
8. compatibility notes