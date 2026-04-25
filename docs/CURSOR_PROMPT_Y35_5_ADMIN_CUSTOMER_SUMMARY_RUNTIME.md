Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for Admin/Ops customer summary layer.

Read first:
- docs/CHAT_HANDOFF.md
- docs/ADMIN_OPS_CUSTOMER_SUMMARY_GATE.md
- docs/ADMIN_OPS_VISIBILITY_GATE.md

Goal:
Replace weak raw customer display in admin read surfaces with safe customer summary, while preserving telegram_user_id.

Scope:
Admin/Ops read-only surfaces only:
- GET /admin/orders
- GET /admin/orders/{order_id}
- GET /admin/custom-requests
- GET /admin/custom-requests/{request_id}
- Telegram admin orders/requests UI

Rules:
- No migrations.
- No customer Mini App changes.
- No My bookings / My requests privacy changes.
- No booking/payment changes.
- No execution-link changes.
- No identity bridge changes.
- No write actions.
- No new external Telegram getChat calls.
- Do not put PII in callback_data.
- Phone is postponed unless already explicitly authorized in the gate.

Customer summary format:
- primary: display_name from first_name + last_name if available
- secondary: @username if available
- fallback: tg:{telegram_user_id}
- always keep raw customer_telegram_user_id in admin API response for traceability

Implementation recommendation:
- Add a shared helper/service method to build CustomerSummary from existing User fields.
- Add additive customer_summary field to admin order/request DTOs.
- Keep existing customer_telegram_user_id fields unchanged.
- Telegram UI should show a short summary line:
  customer: <display name or tg:id> [@username if available]

Tests:
- summary from first_name + last_name
- summary from username only
- fallback tg:{id}
- admin orders list/detail includes customer_summary
- admin custom requests list/detail includes customer_summary
- existing customer_telegram_user_id still present
- customer Mini App user-scoped privacy tests unchanged
- Telegram admin list/detail uses summary text
- no callback payload contains customer summary/PII

After coding report:
- files changed
- DTO fields added
- UI text changes
- tests run
- postponed items