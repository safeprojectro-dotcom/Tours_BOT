# Phase 5 / Step 18 — Waitlist user visibility polish

## Problem

Ops `claim` moved rows from `active` to `in_review`, but Mini App treated “on waitlist” as **only** `status=active`, so the UI looked like the request disappeared.

## API contract (`GET /mini-app/tours/{tour_code}/waitlist-status`)

| Field | Meaning |
|-------|---------|
| `eligible` | Unchanged: sold-out tour still `OPEN_FOR_SALE`. |
| `on_waitlist` | `true` when status is **`active`** or **`in_review`** (interest still in ops pipeline). `false` when only **`closed`** or no row. |
| `waitlist_status` | `null`, or `active`, `in_review`, `closed` — which row is surfaced for UX. |
| `waitlist_entry_id` | Id of that row when applicable. |

## Service rules (`MiniAppWaitlistService`)

- Loads rows for `(user, tour)` with status in `active` / `in_review` / `closed`.
- Picks display row: **active** first, then **in_review**, else most recent **closed**.
- **`join`**: `already_exists` when a **`active` or `in_review`** row exists (`get_pending_entry`), so users cannot duplicate while ops holds the request.

## Mini App UX

- **`active`**: title + body (`waitlist_active_*`).
- **`in_review`**: title + body (`waitlist_in_review_*`); no Join button.
- **`closed`**: neutral copy (`waitlist_closed_body`) + Join again (still not a booking).
- **No row**: intro + Join as before.

Shell strings: **en** and **ro** have full keys; other UI languages fall back to English via `shell()`.

## Manual checks

1. Sold out, no row → Join waitlist.
2. After join → active copy.
3. Ops claim → refresh → in_review copy; request still visible.
4. Ops close → closed copy + Join again; not shown as active/in_review.
5. Booking/payment flows unchanged.

## Out of scope

- Notifications, auto-promotion, ops endpoints, schema migrations.
