Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for Admin/Ops read-only visibility over bookings/orders and custom requests/RFQ.

Read first:
- docs/CHAT_HANDOFF.md
- docs/ADMIN_OPS_VISIBILITY_GATE.md
- docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md

Goal:
Create separate admin/operator read-only visibility surfaces.
Do NOT use customer Mini App "My bookings" / "My requests" for all-user visibility.

Scope:
1. Admin/Ops bookings/orders list
2. Admin/Ops booking/order detail
3. Admin/Ops custom requests/RFQ list
4. Admin/Ops custom request/RFQ detail

Preferred first slice:
- Telegram admin/operator UI if existing admin workspace supports it.
- Otherwise admin API read endpoints only if already consistent with project direction.
- Keep it read-only.

Rules:
- No customer Mini App changes.
- No My bookings / My requests privacy changes.
- No booking/payment semantic changes.
- No execution-link semantic changes.
- No supplier/customer data leakage.
- No write actions: no close, resolve, reassign, cancel, refund, annotate.
- No migrations unless absolutely unavoidable.

Visibility:
Bookings/orders list should show:
- order id
- tour id/code/title if available
- customer telegram_user_id or safe customer summary
- seats_count
- booking/payment/cancellation lifecycle summary
- created_at
- reservation_expires_at if relevant

Custom requests/RFQ list should show:
- request id
- customer telegram_user_id or safe customer summary
- lifecycle/status
- request topic/route summary
- selected supplier/bridge state if already available
- created_at

Filters:
Implement only safe/minimal existing filters if easy:
- status/lifecycle
- tour_id
- request status
- limit/offset or page

Tests:
- admin list orders returns all matching records only for admin surface
- user-scoped Mini App bookings remain user-scoped
- admin custom requests list returns all matching records only for admin surface
- user-scoped My requests remain user-scoped
- detail endpoints/views are read-only
- auth/admin guard remains enforced

After coding report:
- files changed
- UI/API paths added
- filters implemented
- tests run
- confirmation customer self-service privacy unchanged
- postponed actions