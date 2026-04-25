Continue Tours_BOT strict continuation.

Mini App identity issue is now fixed.

Confirmed evidence:
- tg_sdk_loaded=1
- tg_sdk_error=0
- tg_bridge_seen=1
- tg_bridge_webapp=1
- tg_bridge_init=1
- tg_bridge_user=1
- has_identity=True
- source=route_query_user_id
- /bookings, /custom-requests, /settings, /language-preference now receive telegram_user_id.

Task:
Production cleanup after successful Mini App identity fix.

Rules:
- Do NOT remove the working local Telegram SDK asset.
- Do NOT break assets_dir=/app/assets.
- Do NOT restore unsafe fallback.
- Do NOT change booking/payment/RFQ/supplier logic.
- Keep fail-closed when identity is absent.

Cleanup goals:
1. Keep required bridge behavior:
   - load local assets/telegram-web-app.js
   - extract Telegram WebApp user id
   - set tg_bridge_user_id before Flet starts

2. Remove or reduce temporary diagnostic flags from URL if safe:
   - tg_sdk_loaded
   - tg_sdk_error
   - tg_bridge_seen
   - tg_bridge_webapp
   - tg_bridge_init
   - tg_bridge_user

3. Keep MINI_APP_DEBUG_TRACE support but make logs production-safe and quiet by default.

4. Update docs/CHAT_HANDOFF.md:
   - root cause
   - final fix summary
   - verification evidence
   - reminder to set MINI_APP_DEBUG_TRACE=False in Railway after validation

5. Do not remove local SDK file.

Checks:
- python -m compileall app mini_app
- relevant focused tests if any

After coding report:
- Files changed
- Migrations: none
- Tests run
- What remains in production
- What debug flags were removed