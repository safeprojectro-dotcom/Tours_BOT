# CURSOR_PROMPT_B16B_OPS_DASHBOARD_FILTERS_LIMITS_CODE_FIRST

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `b0f11e2 docs: design guarded ops automation`
- `6d4a911 feat: add admin ops dashboard read view`

B16 Step 1 already implemented:

`GET /admin/ops-dashboard`

Current response sections:
- summary
- attention_items
- recent_orders
- upcoming_tours
- recent_publications
- conversion_links
- audit_hint

Current boundaries:
- read-only endpoint
- admin auth required
- no order/payment/reservation mutation
- no Telegram send/publish/retry
- no Layer A changes
- no Mini App routing changes

## Goal

Implement B16B as a code-first read-only extension for `/admin/ops-dashboard`.

Add query parameters so the operator can control dashboard scope.

## Required query parameters

Add these parameters to `GET /admin/ops-dashboard`:

- `days_ahead`
  - default: 30
  - min: 1
  - max: 366

- `recent_days`
  - default: 7
  - min: 1
  - max: 366

- `orders_limit`
  - default: 20
  - min: 1
  - max: 100

- `tours_limit`
  - default: 15
  - min: 1
  - max: 100

- `publications_limit`
  - default: 20
  - min: 1
  - max: 100

- `conversion_links_limit`
  - default: 20
  - min: 1
  - max: 100

- `attention_limit`
  - default: 20
  - min: 1
  - max: 100

- `include_sections`
  - optional comma-separated string
  - allowed:
    - `summary`
    - `attention_items`
    - `recent_orders`
    - `upcoming_tours`
    - `recent_publications`
    - `conversion_links`
  - if omitted: return all sections
  - if provided: excluded list sections should return empty lists; summary can remain populated for schema stability
  - invalid section should return 422 or a clear validation error

## Response change

Add additive response metadata if easy:

```json
"filters": {
  "days_ahead": 30,
  "recent_days": 7,
  "orders_limit": 20,
  "tours_limit": 15,
  "publications_limit": 20,
  "conversion_links_limit": 20,
  "attention_limit": 20,
  "include_sections": [
    "summary",
    "attention_items",
    "recent_orders",
    "upcoming_tours",
    "recent_publications",
    "conversion_links"
  ]
}