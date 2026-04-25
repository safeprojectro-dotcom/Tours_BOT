Continue Tours_BOT strict continuation.

Task: final documentation sync after successful Mini App identity and user-scoped flow fixes.

Confirmed production evidence:
- Mini App identity bridge works with has_identity=True and source=route_query_user_id.
- Local pinned Telegram SDK asset is used: assets/telegram-web-app.js.
- My requests works after creating a custom request.
- My bookings works after reservation/payment completion.
- Successful flow observed:
  POST /reservations -> 200
  GET /orders/{id}/reservation-overview?telegram_user_id=... -> 200
  POST /orders/{id}/payment-entry -> 200
  POST /orders/{id}/mock-payment-complete -> 200
  GET /bookings?telegram_user_id=... -> 200
  GET /orders/{id}/booking-status?telegram_user_id=... -> 200

Update docs only:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md if needed

Document:
- root cause
- final fixed files/architecture
- evidence
- remaining non-blocking notes
- instruction that MINI_APP_DEBUG_TRACE must be False in production
- do not reopen identity bridge unless regression appears

Do not change runtime code.
Do not touch booking/payment/RFQ/supplier semantics.

Checks:
- git diff
- no tests needed unless docs tooling exists

Report files changed.