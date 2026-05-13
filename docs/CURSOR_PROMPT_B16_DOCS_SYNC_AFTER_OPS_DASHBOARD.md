# CURSOR_PROMPT_B16_DOCS_SYNC_AFTER_OPS_DASHBOARD

## Context

B16 Admin / OPS visibility read dashboard implementation is already done.

Current implementation changed/created:
- `app/api/routes/admin.py`
- `app/schemas/admin_ops_dashboard.py`
- `app/services/admin_ops_dashboard_service.py`
- `tests/unit/test_admin_ops_dashboard.py`

Focused tests passed:
- `python -m pytest tests/unit/test_admin_ops_dashboard.py -q`
- Result: `4 passed`

Also checked with publishing console tests:
- `test_admin_publishing_console.py`
- Combined result reported: `12 passed`

Current endpoint:
- `GET /admin/ops-dashboard`
- uses existing admin auth
- read-only

Current response sections:
- summary
- attention_items
- recent_orders
- upcoming_tours
- recent_publications
- conversion_links
- audit_hint

Current implementation notes:
- summary includes `open_handoffs_count`
- recent_orders reuse `AdminOrderListItem`
- attention items include payment pending, expired unpaid holds, open handoffs, recent failed showcase publish attempts
- upcoming tours are non-terminal future tours
- recent publications are latest showcase publish attempts
- conversion_links are newest supplier-offer execution links joined with tour code
- no mutation, no Telegram, no Layer A changes

## Goal

Complete B16 documentation sync only.

Do not change app behavior in this prompt.

## Required docs changes

Create:
- `docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`
- `docs/CURSOR_PROMPT_B16_DOCS_SYNC_AFTER_OPS_DASHBOARD.md`

Update:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP.md`

The original prompt file already exists:
- `docs/CURSOR_PROMPT_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`

Keep it and do not delete it.

## Required B16 doc contents

`docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md` must include:

1. Objective:
   - B16 starts Admin / OPS visibility after B15 publishing-console foundation.
   - It gives operators a read-only view of tours, orders/holds, publications, links, and attention items.

2. Endpoint:
   - `GET /admin/ops-dashboard`
   - protected by existing admin API token auth
   - read-only

3. Response sections:
   - `summary`
   - `attention_items`
   - `recent_orders`
   - `upcoming_tours`
   - `recent_publications`
   - `conversion_links`
   - `audit_hint`

4. Summary fields:
   - upcoming_tours_count
   - open_for_sale_tours_count
   - active_holds_count
   - pending_payment_orders_count
   - confirmed_orders_count
   - expired_or_closed_orders_count
   - recent_publications_count
   - open_handoffs_count
   - attention_items_count

Use actual implemented field names from schema.

5. Attention item semantics:
   - payment-pending holds
   - expired unpaid holds
   - open handoffs
   - failed showcase publish attempts
   - conservative read-only hints only

6. Source-of-truth policy:
   - dashboard aggregates existing order/tour/publication/link data
   - does not own business rules
   - does not compute independent payment truth beyond existing statuses/read services
   - does not trigger expiry/reconciliation

7. Safety boundaries:
   - no order mutation
   - no payment completion
   - no reservation expiry mutation
   - no seat changes
   - no Telegram send/publish/retry
   - no supplier execution attempt creation
   - no Layer A changes
   - no Mini App routing changes
   - no migrations

8. Tests:
   - `python -m pytest tests/unit/test_admin_ops_dashboard.py -q`
   - `4 passed`
   - publishing console regression checked: combined report `12 passed`

9. Relationship to existing admin overview:
   - `/admin/overview` remains coarse totals
   - `/admin/ops-dashboard` is richer ops-oriented visibility

10. Next steps:
   - B16B filters/pagination/time-window controls
   - B16C dashboard-to-detail navigation polish
   - B16D explicit OPS actions design-only
   - B16E notification/audit visibility read-only

## Update CHAT_HANDOFF

Add concise B16 bullet near top:

- B16 Step 1 done: `GET /admin/ops-dashboard` read-only OPS dashboard with summary, attention items, recent orders, upcoming tours, recent publications, conversion links.
- Admin auth required.
- Tests: `test_admin_ops_dashboard.py` — 4 passed; combined with publishing console — 12 passed.
- No mutation / no Telegram / no Layer A / no Mini App route changes.
- Next: B16B filters/pagination or B16C detail navigation.

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Mark B16 Step 1 as done.
Keep future rows:
- B16B filters/pagination/time-window controls
- B16C dashboard-to-detail navigation polish
- B16D explicit OPS actions design-only first
- B16E notification/audit visibility read-only

## Update handoff

Update:
`docs/HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP.md`

It must record:
- B16 Step 1 implemented
- endpoint path
- response sections
- tests passed
- safety confirmations
- next recommended options

## Non-goals

Do not change:
- app code
- tests
- schemas
- services
- migrations
- production data
- Telegram posts
- Layer A
- Mini App routing

## After completion report

Return:

1. Files changed.
2. Docs created/updated.
3. Confirmation that app code was not changed by this docs-sync prompt.
4. `git status --short`.
5. `git diff --stat`.

---

## Doc artifacts produced by this sync

| Artifact | Role |
|----------|------|
| [`docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`](B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md) | B16 Step 1 design record (endpoint, sections, summary fields, attention semantics, safety, tests, `/admin/overview` relationship). |
| Updates to [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP.md`](HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP.md) | B16 status, cross-links, and handoff refresh. |
