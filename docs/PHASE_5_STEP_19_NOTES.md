# Phase 5 / Step 19 — Cleanup / archive policy (presentation)

## Pain point addressed

**My bookings → History** could list many old released/expired holds after long staging use, drowning out current work.

## Policy (archive ≠ delete)

- **No** database deletes, **no** new migrations, **no** cron retention jobs in this step.
- **Presentation only:** the Mini App limits how many **History** rows render and sorts them by **most recently updated order first** (`order.updated_at` descending).
- Hidden rows still exist in the API response from `GET /mini-app/bookings` (unchanged); only the **UI grouping** truncates the History bucket. Users can still open a specific booking by id if they have the reference.

## Implementation

| Piece | Behavior |
|-------|----------|
| `mini_app/booking_grouping.py` | `HISTORY_SECTION_MAX_ITEMS = 15`; `partition_bookings_for_my_bookings_ui(..., history_max_items=...)` returns `(confirmed, active, history_visible, history_omitted_count)`. |
| History sort | Newest `summary.order.updated_at` first. |
| `history_max_items=None` | Disables cap (tests / future use). |

My bookings screen shows a one-line note when `history_omitted_count > 0` (`bookings_history_truncated_note` — **en** and **ro**).

## Ops-facing queues

Unchanged: **open** handoffs and **active** waitlist remain the only actionable lists on internal ops endpoints. Closed rows stay out of those queues by design; no new “recently closed” endpoint in this step.

## Staging reset scripts

Operational tools (e.g. tour reset) remain separate; they do not replace this policy.

## Manual checks

1. Confirmed and active holds still appear in full.
2. With many history items, only 15 show in History + note if more exist.
3. Ops JSON queues unchanged in meaning.
4. No booking/payment API contract changes.

## Out of scope

- API query params for pagination, “show older” button, server-side history truncation, notification cleanup, admin SPA.
