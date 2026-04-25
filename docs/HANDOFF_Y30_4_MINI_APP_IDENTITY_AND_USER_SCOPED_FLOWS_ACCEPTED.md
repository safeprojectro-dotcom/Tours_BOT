Tours_BOT Y30.4 Mini App identity/user-scoped flow is now accepted.

Critical result:
- Telegram WebApp identity now resolves in production.
- User-scoped Mini App flows work:
  My bookings, My requests, Settings, custom request creation, reservation, payment-entry, mock payment completion, booking-status.

Root cause:
- Mini App was opened/bootstrapped without reliable Telegram WebApp SDK/initData path.
- External Telegram SDK load failed in Telegram WebView.
- Some Mini App screens still used dev_telegram_user_id instead of runtime-resolved Telegram identity.

Final production-safe solution:
- assets/telegram-web-app.js local pinned SDK.
- assets/index.html injects tg_bridge_user_id before Flet python.js starts.
- mini_app/main.py uses /app/assets.
- user-scoped screens use runtime resolved identity.
- fail-closed preserved.

Do not reopen identity bridge unless production regression appears.
Next work can continue from docs/CHAT_HANDOFF.md.