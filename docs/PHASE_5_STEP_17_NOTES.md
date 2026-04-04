# Phase 5 / Step 17 — Minimal waitlist operator actions

## Status model (no migration)

`waitlist.status` is `String(32)` with a unique constraint on `(user_id, tour_id, status)`. Convention:

| Status | Meaning |
|--------|---------|
| `active` | Interest recorded from Mini App; listed on `GET /internal/ops/waitlist/active`. |
| `in_review` | Ops claimed the row (`PATCH .../claim`). |
| `closed` | Ops finished (`PATCH .../close`). |

Other legacy values (e.g. `cancelled` in tests) are not closed via this slice; **close** is only allowed from `active` or `in_review`.

There is **no** `assigned_operator_id` on `waitlist` — only status changes.

## Internal API (same `OPS_QUEUE_TOKEN` as Step 15–16)

| Method | Path | Body | Effect |
|--------|------|------|--------|
| PATCH | `/internal/ops/waitlist/{id}/claim` | none | `active` → `in_review`. |
| PATCH | `/internal/ops/waitlist/{id}/close` | none | `active` or `in_review` → `closed`. |

**Claim**

- Only when `status == active`. Otherwise **409** `{"code":"waitlist_not_active","current_status":"..."}`.
- Missing row: **404** `waitlist_entry_not_found`.

**Close**

- When `status` is `closed`: **409** `waitlist_already_closed`.
- When `status` is neither `active` nor `in_review` (e.g. legacy `cancelled`): **409** `waitlist_close_not_allowed`.
- No notifications, no seats, no orders, no auto-promotion.

**Response** (`OpsWaitlistActionRead`): `id`, `status`, `user_id`, `tour_id`, `seats_count`, `created_at`.

## Queue behavior

`GET /internal/ops/waitlist/active` remains **only** `status == active`. After claim or close, the row no longer appears there.

## Mini App note (unchanged code)

`MiniAppWaitlistService.get_active_entry` still selects **`active` only**. After ops **claim** (`in_review`), the user is treated as **not** on the waitlist in that API until product defines broader semantics (out of scope for Step 17).

## Manual checklist

1. Create a waitlist row with `status=active`.
2. `GET /internal/ops/waitlist/active` — visible.
3. `PATCH .../claim` — `in_review`; gone from active queue.
4. Repeat claim — **409**.
5. `PATCH .../close` — `closed`.
6. Repeat close — **409** `waitlist_already_closed`.

## Out of scope

- Auto-booking, seat release, payment.
- Handoff changes.
- Operator notifications.
- Admin SPA.
- Extending Mini App to show `in_review` as “still interested” without code changes in this step.
