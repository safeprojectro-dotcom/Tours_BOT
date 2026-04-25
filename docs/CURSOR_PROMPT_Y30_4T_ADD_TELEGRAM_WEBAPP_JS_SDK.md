Continue Tours_BOT strict continuation.

Current confirmed evidence:
Mini_App_UI safe trace shows:
tg_bridge_seen=0
tg_bridge_webapp=0
tg_bridge_init=0
tg_bridge_user=0

This proves assets/index.html runs, but window.Telegram is missing in the page.
Even with Telegram WebApp button, the JS bridge cannot see Telegram.WebApp.

Root cause:
Telegram WebApp JS SDK is not loaded in assets/index.html before bridge execution.

Task:
Add Telegram WebApp JS SDK to assets/index.html and ensure bridge runs after SDK is available.

==================================================
RULES
==================================================

Do NOT:
- restore unsafe fallback
- change booking/payment/RFQ/supplier logic
- change backend contracts
- log raw initData
- load user-scoped data without verified/extracted identity

Allowed:
- modify assets/index.html only
- add official Telegram WebApp SDK script:
  https://telegram.org/js/telegram-web-app.js
- ensure bridge waits for Telegram.WebApp after SDK load
- keep existing safe bridge flags
- keep Flet startup after bridge attempt

==================================================
IMPLEMENTATION EXPECTATION
==================================================

In assets/index.html:
- load Telegram WebApp SDK before bridge code
- bridge should check window.Telegram and Telegram.WebApp after SDK is loaded
- call Telegram.WebApp.ready() if available
- read initDataUnsafe.user.id and initData user fallback
- set:
  tg_bridge_seen=1
  tg_bridge_webapp=1
  tg_bridge_init=1/0
  tg_bridge_user=1/0
  tg_bridge_user_id=<id> if found
- then start Flet/python.js

Outside Telegram:
- SDK may load but initData/user may be absent
- user-scoped pages remain fail-closed

==================================================
CHECKS
==================================================

Run:
python -m compileall mini_app

After deploy:
Open from Telegram WebApp button.

Expected logs:
- bridge_seen=1
- bridge_webapp=1
- if Telegram provides user:
  bridge_init=1
  bridge_user=1
  has_identity=True

If still failing:
logs must at least prove whether SDK is loaded:
bridge_seen=1 bridge_webapp=1 bridge_init=0 bridge_user=0