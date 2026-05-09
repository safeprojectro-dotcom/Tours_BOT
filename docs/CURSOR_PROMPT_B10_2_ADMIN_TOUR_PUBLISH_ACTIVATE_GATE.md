You are continuing Tours_BOT after B10.1 smoke.

Goal:
B10.2 — Admin Tour Publish / Activate Gate.

Current state:
- B10 bridge works.
- Supplier offer #8 created Tour #4.
- Tour #4 has status=draft.
- Mini App catalog does not show draft tours.
- This is correct and safe.

Problem:
We need a separate explicit admin action to make a bridge-created Tour catalog-visible.
Bridge creation must remain separate from activation.

Goal:
Add explicit admin endpoint to activate/publish a draft Tour for Mini App catalog visibility.

Scope:
- Admin-only status transition.
- Tour draft → open_for_sale.
- Tests.
- No supplier offer mutation unless audit note already exists.
- No Telegram publish.
- No booking/payment/order creation.

Required API:
POST /admin/tours/{tour_id}/activate-for-catalog

Body optional:
{
  "activated_by": "...",
  "notes": "..."
}

Rules:
1. Only draft Tour can be activated.
2. Tour must have required customer-facing fields:
   - title_default
   - departure_datetime
   - return_datetime
   - base_price
   - currency
   - seats_total
   - sales_mode
3. If sales_mode == full_bus:
   - ensure it remains view_only / operator path in policy
   - do not change seats_available into per-seat availability semantics
4. Do not publish Telegram.
5. Do not create order/payment/reservation.
6. Do not mutate supplier offer lifecycle.
7. Idempotency:
   - if already open_for_sale, return current state with idempotent_replay=true
   - do not fail unless status is cancelled/archived/rejected if such statuses exist.
8. Catalog visibility follows existing Mini App status_scope ["open_for_sale"].

Tests:
- draft Tour activates to open_for_sale
- repeated activation is idempotent
- missing required fields fails
- full_bus activation does not enable per-seat self-service
- no orders/payments created
- no supplier offer lifecycle changed
- no Telegram fields changed
- Mini App catalog service/list predicate still relies on open_for_sale

Before coding:
1. summarize B10.1 smoke result
2. list files expected to change
3. explain why activation is separate and safe
4. state non-goals

After coding:
1. files changed
2. endpoint added
3. validation rules
4. tests run
5. confirm no Telegram/payment/order/supplier lifecycle changes
6. next safe step: smoke Tour #4 activation and Mini App catalog visibility check