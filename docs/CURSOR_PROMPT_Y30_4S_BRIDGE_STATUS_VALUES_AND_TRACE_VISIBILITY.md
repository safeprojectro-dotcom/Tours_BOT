Continue Tours_BOT strict continuation.

Current evidence:
Mini_App_UI logs now show the JS bridge is executing because route contains:
?tg_bridge_seen&tg_bridge_webapp&tg_bridge_init&tg_bridge_user

But values are missing/empty and identity remains:
has_identity=False source=none

Task:
Fix bridge status params to explicit values and make MiniAppShell safe trace print them.

Do NOT change backend, booking/payment, RFQ, supplier logic.
Do NOT add unsafe fallback.
Do NOT log raw initData.

Allowed:
1. assets/index.html:
   - set explicit bridge status values:
     tg_bridge_seen=1/0
     tg_bridge_webapp=1/0
     tg_bridge_init=1/0
     tg_bridge_user=1/0
   - if user id is found, set existing:
     tg_bridge_user_id=<id>
   - ensure URL is updated before python.js starts.

2. mini_app/app.py:
   - when MINI_APP_DEBUG_TRACE=True, include safe bridge flags in mini_app_identity logs:
     bridge_seen
     bridge_webapp
     bridge_init
     bridge_user
   - no raw initData
   - no user payload
   - no business logic change

Expected after deploy:
If Telegram WebApp works:
route includes tg_bridge_webapp=1, tg_bridge_init=1, tg_bridge_user=1, tg_bridge_user_id=<id>
and MiniAppShell logs has_identity=True.

If still failing, logs must clearly show one of:
- bridge_seen=1 bridge_webapp=0
- bridge_seen=1 bridge_webapp=1 bridge_init=0
- bridge_seen=1 bridge_webapp=1 bridge_init=1 bridge_user=0

Run:
python -m compileall mini_app

Report:
- files changed
- exact expected log line
- no migrations
- no domain changes