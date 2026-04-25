Continue Tours_BOT strict continuation.

Current evidence:
- Mini_App_UI now uses /app/assets.
- Logs show:
  Assets path configured: /app/assets
  Assets dir: /app/assets
- Safe trace works.
- But identity still fails:
  mini_app_identity context=startup route=/ has_identity=False source=none
  route=/bookings has_identity=False source=none
  route=/my-requests has_identity=False source=none

Task:
Verify and minimally fix Telegram JS bridge execution/timing.

Do NOT change booking/payment/RFQ/supplier logic.
Do NOT restore unsafe fallback.
Keep fail-closed.

Investigate:
1. assets/index.html content.
2. Whether Telegram bridge script runs before Flet app opens websocket/session.
3. Whether bridge modifies URL query/fragment before Flet runtime starts.
4. Whether Flet patched index preserves custom script.
5. Whether Telegram.WebApp.initDataUnsafe.user.id exists in JS runtime.
6. Whether bridge should write identity into URL fragment/query and reload/replaceState before Flet starts.

Allowed:
- adjust assets/index.html bridge timing
- ensure bridge runs before Flet bootstrap
- use safe URL param/fragment already supported by mini_app/app.py
- add temporary safe console/stdout-visible marker only if necessary, no raw initData

Not allowed:
- unsafe dev fallback
- backend contract changes
- user-scoped loading without identity
- logging raw initData

Expected:
When opened from Telegram:
mini_app_identity ... has_identity=True source=<bridge/query/initdata source>

When opened outside Telegram:
has_identity=False source=none