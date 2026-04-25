Continue Tours_BOT strict continuation.

Current confirmed evidence:
After adding dynamic SDK load from https://telegram.org/js/telegram-web-app.js, Mini_App_UI logs show:

tg_sdk_loaded=0
tg_sdk_error=1
tg_bridge_seen=0
tg_bridge_webapp=0
tg_bridge_init=0
tg_bridge_user=0

Root cause:
Telegram WebApp SDK external script fails to load in current Telegram WebView/runtime.

Task:
Vendor/pin Telegram WebApp JS SDK as a local asset and load it from /assets.

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
- add local SDK file under assets/
- update assets/index.html to load local SDK first
- keep safe SDK/bridge flags
- keep external SDK as optional fallback only if desired
- keep Flet startup after bridge attempt

==================================================
IMPLEMENTATION
==================================================

Add local file:
assets/telegram-web-app.js

This file should contain a copied/pinned Telegram WebApp SDK implementation from the official Telegram script used for Web Apps.

Then update assets/index.html:
- load /assets/telegram-web-app.js or relative asset path that Flet serves correctly
- set:
  tg_sdk_loaded=1 if local SDK loads
  tg_sdk_error=1 only if local SDK fails
- then bridge checks window.Telegram.WebApp
- then starts Flet

Important:
Do not log or expose raw initData.
Do not add user fallback.

==================================================
EXPECTED RESULT
==================================================

After deploy and opening via Telegram WebApp button:

At minimum:
tg_sdk_loaded=1
tg_sdk_error=0

If WebApp runtime is valid:
tg_bridge_seen=1
tg_bridge_webapp=1

If Telegram provides initData:
tg_bridge_init=1
tg_bridge_user=1
has_identity=True

If outside Telegram:
SDK may load, but initData/user can remain missing and user-scoped pages stay fail-closed.

==================================================
CHECKS
==================================================

Run:
python -m compileall mini_app

After deploy:
Open via Telegram WebApp button and check Mini_App_UI logs:
tg_sdk_loaded=
tg_sdk_error=
tg_bridge_seen=
tg_bridge_webapp=
tg_bridge_init=
tg_bridge_user=
has_identity=