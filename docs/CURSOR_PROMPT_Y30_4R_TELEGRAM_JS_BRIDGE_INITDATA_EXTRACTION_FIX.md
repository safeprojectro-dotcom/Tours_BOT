Continue Tours_BOT strict continuation.

Current confirmed evidence:
- Mini_App_UI uses /app/assets.
- Telegram private bot button was converted from url= to web_app=WebAppInfo(...).
- User deleted chat history, ran /start again, and opened via new button.
- Telegram now shows Mini App start dialog, so WebApp launch is at least partially active.
- But Mini_App_UI logs still show:
  mini_app_identity ... has_identity=False source=none
  on /, /bookings, /my-requests, /settings.

Conclusion:
Flet Python runtime still receives no identity.
Next narrow target: assets/index.html Telegram JS bridge extraction and handoff to Flet-readable URL/query surface.

==================================================
STRICT RULES
==================================================

Do NOT:
- restore unsafe fallback
- load user-scoped data without identity
- change booking/payment/RFQ/supplier logic
- change backend contracts
- log raw initData
- add broad debug noise

Allowed:
- modify assets/index.html only unless absolutely necessary
- add temporary safe bridge evidence visible to Flet URL/query only
- add safe bridge status params:
  tg_bridge_seen=1/0
  tg_bridge_webapp=1/0
  tg_bridge_init=1/0
  tg_bridge_user=1/0
  tg_bridge_user_id=<id> ONLY if it is already the intended trusted WebApp runtime path
- use URL fragment/query already parsed by mini_app/app.py
- remove temporary evidence after confirmation in a later cleanup step

==================================================
TASK
==================================================

Fix or instrument the JS bridge so we can distinguish:

1. window.Telegram missing
2. Telegram.WebApp missing
3. initData missing
4. initDataUnsafe.user.id missing
5. user id found but URL not updated before Flet starts

Bridge must:
- wait briefly for window.Telegram.WebApp
- call Telegram.WebApp.ready() if available
- read both:
  Telegram.WebApp.initDataUnsafe.user.id
  Telegram.WebApp.initData with URLSearchParams fallback
- if user id found, put it into existing supported param:
  tg_bridge_user_id=<id>
- ensure location.replaceState/URL update happens BEFORE loading python.js / Flet bootstrap
- then start Flet

==================================================
EXPECTED AFTER FIX
==================================================

In Mini_App_UI logs, after opening from Telegram WebApp button:

Preferred:
mini_app_identity ... has_identity=True source=<bridge/query source>

If still false, route/url should at least contain safe bridge status params proving:
- webapp present or not
- initData present or not
- user present or not

Outside Telegram:
has_identity=False remains allowed.

==================================================
FILES LIKELY TO CHANGE
==================================================

Expected:
- assets/index.html

Only if needed:
- mini_app/app.py to include safe bridge status in existing debug trace, no logic change

Do NOT change:
- app/bot/keyboards.py unless evidence says WebAppInfo did not deploy
- backend APIs
- booking/payment/RFQ/supplier services

==================================================
CHECKS
==================================================

Run:
- python -m compileall mini_app

After deploy:
- open only via new Telegram WebApp button
- check Mini_App_UI logs for mini_app_identity
- check whether source becomes non-none