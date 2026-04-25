Continue Tours_BOT strict continuation.

Confirmed runtime evidence:
MINI_APP_DEBUG_TRACE=True now works.

Mini_App_UI logs show:
- mini_app_identity context=startup route=/ has_identity=False source=none
- route=/bookings has_identity=False source=none
- route=/my-requests has_identity=False source=none
- route=/settings has_identity=False source=none

Also Flet logs show:
- Web root: /app/.venv/lib/python.../site-packages/flet_web/web
- assets_dir does not exist: /app/mini_app/assets

Conclusion:
Flet Python runtime is not receiving Telegram identity from route/page.url/page.query.
The existing assets/index.html bridge is likely not used by the deployed Flet web entrypoint.

Task:
Fix the Mini App Telegram WebApp bridge entrypoint so Telegram identity reaches Flet runtime.

==================================================
STRICT RULES
==================================================

Do NOT:
- restore unsafe shared fallback
- load user-scoped data without identity
- change booking/payment logic
- change RFQ/supplier logic
- change backend contracts
- add noisy debug probes
- log raw initData

Allowed:
- fix Flet web assets/index.html entrypoint usage
- ensure assets directory is packaged/deployed correctly
- configure mini_app/main.py to use the correct assets_dir / web renderer entrypoint if needed
- pass only safe identity material already expected by current Mini App runtime path
- keep MINI_APP_DEBUG_TRACE safe trace

==================================================
INVESTIGATE FIRST
==================================================

Inspect:
- mini_app/main.py
- mini_app/assets/
- assets/index.html
- pyproject / Railway start command / Docker/Railpack config
- Flet run/app call and assets_dir parameter
- current deployed file layout assumptions

Answer before coding:
1. Is assets/index.html actually used by Flet?
2. Why does Railway log say /app/mini_app/assets does not exist?
3. Where should custom index/bootstrap live for this Flet version?
4. What minimal change makes Telegram.WebApp initData/user available before Flet session starts?

==================================================
IMPLEMENTATION GOAL
==================================================

Make the deployed Mini_App_UI use a real Telegram WebApp bridge bootstrap.

Expected after fix:
- when opened from Telegram, bridge can access window.Telegram.WebApp
- it extracts safe user id / launch payload according to existing project contract
- it forwards identity into a Flet-readable surface:
  - URL query
  - URL fragment
  - or another already supported runtime surface
- MiniAppShell resolves identity
- logs show:
  mini_app_identity ... has_identity=True source=<bridge_source>

If opened outside Telegram:
- has_identity=False
- user-scoped pages still fail-closed

==================================================
TESTS / CHECKS
==================================================

Run:
- python -m compileall mini_app

If practical, add/adjust a focused test for bridge URL/query extraction only.
Do not add broad tests.

==================================================
AFTER CODING REPORT
==================================================

Report:
- Files changed
- Migrations: none
- What entrypoint was fixed
- Whether assets/index.html is now actually used
- Exact Railway log lines expected
- Why fail-closed remains safe
- What remains postponed