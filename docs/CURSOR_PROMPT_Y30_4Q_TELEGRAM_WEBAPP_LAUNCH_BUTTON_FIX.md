Continue Tours_BOT strict continuation.

Current confirmed evidence:
- Mini_App_UI uses /app/assets.
- assets/index.html bridge is deployed.
- Safe trace works.
- But Telegram identity is still absent:
  mini_app_identity ... route=/ has_identity=False source=none
  mini_app_identity ... route=/my-requests has_identity=False source=none

This means Flet runtime receives no Telegram WebApp identity.
Most likely Mini App is opened as a normal URL button/link, not as Telegram WebApp button.

Task:
Verify and fix Telegram Mini App launch button wiring.

==================================================
RULES
==================================================

Do NOT:
- restore unsafe fallback
- change booking/payment logic
- change RFQ/supplier semantics
- change backend contracts
- load user-scoped data without identity

Allowed:
- inspect bot keyboards / menu button / CTA buttons
- replace normal URL buttons with Telegram WebAppInfo buttons where appropriate
- keep normal URL only for non-Telegram/public fallback if already needed
- update docs/CHAT_HANDOFF.md

==================================================
INVESTIGATE FIRST
==================================================

Search for:
- miniappui-production.up.railway.app
- WebAppInfo
- web_app=
- InlineKeyboardButton
- KeyboardButton
- url=
- open Mini App
- My bookings
- My requests
- Settings
- /bookings
- /my-requests
- /settings

Answer before coding:
1. Which buttons currently open Mini App?
2. Are they URL buttons or web_app buttons?
3. Which user entrypoint is used in private chat?
4. Does /start or menu button use Telegram WebAppInfo?
5. What minimal button change will make Telegram inject initData?

==================================================
IMPLEMENTATION GOAL
==================================================

Ensure private Telegram bot opens Mini App via Telegram WebApp button, not normal URL.

Expected aiogram pattern:
InlineKeyboardButton(
    text="Open Mini App",
    web_app=WebAppInfo(url=MINI_APP_URL)
)

or equivalent supported project pattern.

Expected result:
When opened from Telegram button:
- window.Telegram.WebApp is available
- initDataUnsafe.user.id is available
- bridge adds identity to supported runtime surface
- MiniAppShell logs:
  has_identity=True source=<telegram bridge/query source>

If opened by direct browser URL:
- has_identity=False
- user-scoped pages remain fail-closed

==================================================
FILES LIKELY TO CHANGE
==================================================

Likely:
- app/bot/keyboards*.py
- app/bot/handlers*.py
- app/core/config.py if MINI_APP_URL setting is missing
- docs/CHAT_HANDOFF.md

Do NOT change:
- mini_app identity logic unless absolutely necessary
- booking/payment services
- RFQ/supplier services
- backend Mini App endpoints

==================================================
TESTS / CHECKS
==================================================

Run:
- python -m compileall app mini_app

If bot keyboard tests exist, run focused tests.

==================================================
AFTER CODING REPORT
==================================================

Report:
- Files changed
- Migrations: none
- Which buttons changed from url to web_app
- How to open Mini App correctly for verification
- Expected Railway log lines
- What remains postponed