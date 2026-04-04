# Phase 5 / Step 15 — Minimal operator/admin queue visibility

## Goal

Read-only visibility for operations: **open handoff requests** and **active waitlist interest rows** are visible via authenticated JSON endpoints, without building a full admin product or changing booking/payment/waitlist promotion logic.

## Ordering (operational choice)

| Queue | Default sort | Rationale |
|-------|----------------|-----------|
| Open handoffs | `created_at` **ascending** (oldest first) | FIFO-style triage so the longest-waiting open requests surface first. |
| Active waitlist | `created_at` **ascending** | Longest-waiting interest first; same queue semantics. |

Both responses include `ordering: "created_at_asc"` for clarity.

## API

Requires `OPS_QUEUE_TOKEN` in the API environment. If unset, routes return **503** (disabled).

Authentication (either):

- `Authorization: Bearer <OPS_QUEUE_TOKEN>`, or
- `X-Ops-Token: <OPS_QUEUE_TOKEN>`

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/internal/ops/handoffs/open` | Rows with `handoffs.status == "open"`. Optional `limit` query (1–2000, default 500). |
| GET | `/internal/ops/waitlist/active` | Rows with `waitlist.status == "active"`. Same `limit`. |

Handoff items include: ids, timestamps, status, priority, reason, `user_id`, `order_id`, `assigned_operator_id` (null if unassigned), and optional order tour labels (`order_tour_id`, `order_tour_code`, `order_tour_title_default`) when `order_id` resolves to an order with a tour.

Waitlist items include: ids, `created_at`, status, `user_id`, `tour_id`, `seats_count`, plus `tour_code` and `tour_title_default` when the tour row is loaded.

**Queues are separate:** handoffs and waitlist are different endpoints; waitlist entries are **not** bookings or confirmed orders.

## Implementation notes

- **Read-only:** no POST/PATCH; no new business states.
- **No migrations:** uses existing `handoffs` and `waitlist` tables and string statuses (`open` / `active` as used today).
- **Repositories:** `HandoffRepository.list_open_for_ops_queue`, `WaitlistRepository.list_active_for_ops_queue` with `selectinload` to avoid N+1 for tour context.
- **Service:** `OpsQueueReadService` maps ORM rows to `app.schemas.ops_queue` DTOs.

## Manual verification

1. Seed or create `handoffs` with `status=open` → appear on `GET /internal/ops/handoffs/open` with token.
2. Seed `waitlist` with `status=active` → appear on `GET /internal/ops/waitlist/active`.
3. Confirm orders / paid bookings do not appear on the waitlist endpoint (only `waitlist` table rows).
4. Non-open handoffs (e.g. `closed`) and non-active waitlist rows do not appear in these lists.
5. Public Mini App and private bot flows unchanged.

## Out of scope

- Full operator assignment workflow, handoff lifecycle notifications, waitlist auto-promotion.
- Admin UI SPA, OAuth, role-based access (only shared secret).
- Mutating actions (close handoff, deactivate waitlist) — deferred until product defines safe transitions.
