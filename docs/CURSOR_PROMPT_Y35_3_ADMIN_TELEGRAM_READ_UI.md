Continue Tours_BOT strict continuation.

Task:
Add Telegram admin/operator read-only UI for:
- bookings/orders
- custom requests/RFQ

Use existing admin API:
- GET /admin/orders
- GET /admin/orders/{order_id}
- GET /admin/custom-requests
- GET /admin/custom-requests/{request_id}

Goal:
Provide simple Telegram admin navigation to view:
1. list of orders
2. order detail
3. list of requests
4. request detail

Rules:
- Read-only only
- No mutations
- No booking/payment changes
- No Mini App changes
- No execution-link changes
- No FSM complexity explosion
- Keep callback payload small (<64 bytes)

UI:

Admin menu additions:
- 📦 Orders
- 📨 Requests

Orders list:
- order_id
- short tour info
- status
- customer_telegram_user_id (short)

Buttons:
- View order #ID
- Next / Prev page
- Back

Order detail:
- full info from admin API
- Back

Requests list:
- request_id
- short summary
- status
- customer id

Request detail:
- full info
- Back

Tests:
- admin-only access
- pagination works
- detail opens correctly
- no effect on user flows

After coding report:
- files changed
- handlers added
- callbacks added
- tests run