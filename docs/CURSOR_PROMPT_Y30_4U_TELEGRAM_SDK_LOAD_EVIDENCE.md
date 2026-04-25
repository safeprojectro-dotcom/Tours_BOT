Continue Tours_BOT strict continuation.

Current evidence after adding Telegram WebApp SDK:
Mini_App_UI still logs:
bridge_seen=0 bridge_webapp=0 bridge_init=0 bridge_user=0

This means assets/index.html bridge still cannot see window.Telegram.

Task:
Add narrow safe SDK-load evidence, without changing identity/business logic.

==================================================
RULES
==================================================

Do NOT:
- restore unsafe fallback
- change booking/payment/RFQ/supplier logic
- change backend contracts
- log raw initData
- load user-scoped data without identity

Allowed:
- assets/index.html only if possible
- add explicit script onload/onerror handling for:
  https://telegram.org/js/telegram-web-app.js
- set safe URL flags before Flet starts:
  tg_sdk_loaded=1/0
  tg_sdk_error=1/0
- preserve existing bridge flags:
  tg_bridge_seen/webapp/init/user
- no raw initData

==================================================
WHY
==================================================

We need to distinguish:
1. Telegram SDK script not loaded at all.
2. SDK loaded but window.Telegram still absent.
3. SDK loaded and Telegram exists but WebApp/initData absent.

==================================================
EXPECTED LOGS
==================================================

After deploy, Mini_App_UI mini_app_identity logs should include route/query with:
tg_sdk_loaded=1 or 0
tg_sdk_error=1 or 0
tg_bridge_seen=...
tg_bridge_webapp=...

If tg_sdk_error=1:
SDK failed to load in Telegram WebView.

If tg_sdk_loaded=1 but bridge_seen=0:
SDK loaded but global Telegram object absent.

If tg_sdk_loaded=1 bridge_seen=1 bridge_webapp=1:
continue to initData/user extraction.