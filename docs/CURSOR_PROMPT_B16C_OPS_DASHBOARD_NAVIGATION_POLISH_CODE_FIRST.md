# CURSOR_PROMPT_B16C_OPS_DASHBOARD_NAVIGATION_POLISH_CODE_FIRST

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `a3f100 feat: add ops dashboard filters and limits`
- `b0f11e2 docs: design guarded ops automation`
- `6d4a911 feat: add admin ops dashboard read view`

B16 Step 1 implemented:

`GET /admin/ops-dashboard`

B16B implemented filters/limits/time-window controls:

- days_ahead
- recent_days
- orders_limit
- tours_limit
- publications_limit
- conversion_links_limit
- attention_limit
- include_sections
- filters response metadata
- invalid include_sections -> 422

Tests from B16B:
- `tests/unit/test_admin_ops_dashboard.py` — 8 passed
- with `tests/unit/test_admin_publishing_console.py` — 16 passed

Current dashboard sections:
- summary
- filters
- attention_items
- recent_orders
- upcoming_tours
- recent_publications
- conversion_links
- audit_hint

## Goal

Implement B16C as code-first navigation polish for `/admin/ops-dashboard`.

The dashboard should help the operator move from a summary/attention row to the correct admin detail/read surface.

This is still read-only.

## Required behavior

Add or normalize navigation fields so every dashboard row has useful paths.

Use internal admin API paths, not public URLs, unless an existing Mini App URL helper is already safely available.

## Target navigation semantics

### attention_items

Each attention item should have, where applicable:

- `admin_path`
- `related_order_id`
- `related_tour_id`
- `related_supplier_offer_id`

Rules:
- payment/order related item -> `/admin/orders/{order_id}`
- tour related item without order -> `/admin/tours/{tour_id}`
- supplier offer / publish related item -> `/admin/supplier-offers/{offer_id}/review-package`
- fallback -> relevant list path, such as `/admin/ops-dashboard`

If `admin_path` already exists, make it consistent.

### recent_orders

Each order row should expose a detail path.

If `AdminOrderListItem` already has an equivalent field, reuse it.

If not, add an additive field if safe:

- `admin_path`: `/admin/orders/{order_id}`

Do not break existing `AdminOrderListItem` behavior outside this dashboard. If modifying shared schema is risky, wrap/enrich recent order rows inside the ops dashboard schema instead.

### upcoming_tours

Each tour row should include:

- `admin_path`: `/admin/tours/{tour_id}`
- `mini_app_path` or `mini_app_url` only if already safe and currently used elsewhere

Prefer `admin_path` as mandatory, Mini App path as optional.

### recent_publications

Each publication row should include:

- `admin_path`: `/admin/supplier-offers/{supplier_offer_id}/review-package` when supplier_offer_id exists
- optionally `channel_message_ref` or existing message id fields remain unchanged

Do not create Telegram links unless already supported safely.

### conversion_links

Each conversion link row should include:

- `supplier_offer_admin_path`: `/admin/supplier-offers/{supplier_offer_id}/review-package`
- `tour_admin_path`: `/admin/tours/{tour_id}`
- optional generic `admin_path` can point to the supplier offer review package

## Response compatibility

Keep existing fields backward-compatible.

Additive fields only.

Existing calls to `/admin/ops-dashboard` must continue to work.

## Safety

Do NOT:
- mutate orders
- mutate payments
- expire holds
- change seats
- send Telegram messages
- publish/retry
- create supplier execution attempts
- create execution links
- change Layer A
- change Mini App routing
- create migrations

## Implementation notes

Likely files:
- `app/schemas/admin_ops_dashboard.py`
- `app/services/admin_ops_dashboard_service.py`
- `tests/unit/test_admin_ops_dashboard.py`

Only touch `app/api/routes/admin.py` if necessary.

Avoid large abstractions.

Keep this as a small navigation polish slice.

## Tests

Update:

`tests/unit/test_admin_ops_dashboard.py`

Required test cases:

1. recent_orders rows expose `/admin/orders/{id}` path.

2. upcoming_tours rows expose `/admin/tours/{id}` path.

3. recent_publications rows expose supplier offer review-package path when supplier_offer_id is present.

4. conversion_links rows expose:
   - supplier_offer_admin_path
   - tour_admin_path
   - admin_path or equivalent primary path.

5. attention_items:
   - payment pending item points to order detail.
   - failed publication item points to supplier offer review package if fixture exists.
   - if failed publication fixture is expensive, assert at least payment/order attention path and document publication path behavior in a small code comment/test helper.

Run:

```powershell
python -m pytest tests/unit/test_admin_ops_dashboard.py -q