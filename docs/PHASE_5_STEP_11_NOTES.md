# Phase 5 / Step 11 — My bookings UX grouping

## What changed

- **Mini App only:** the bookings list is grouped for display using existing `facade_state` from `GET /mini-app/bookings` (no API, DB, or payment changes).
- **Sections (top to bottom):**
  1. **Confirmed bookings** — `facade_state` in `confirmed`, `in_trip_pipeline`
  2. **Active holds** — `active_temporary_reservation`
  3. **History** — `expired_temporary_reservation`, `cancelled_no_payment`, `other`
- Empty sections are **not** shown.
- Card layout and **Open** → booking detail are unchanged.

## Implementation

- `mini_app/booking_grouping.py` — `partition_bookings_for_my_bookings_ui()`
- `mini_app/app.py` — `MyBookingsScreen._render` builds section headers + reuses `_booking_card()` per item
- `mini_app/ui_strings.py` — section titles/hints + updated page subtitle (en, ro)

## Out of scope

- Filtering or hiding rows by age, schema changes, or server-side sorting beyond the existing list order within each bucket.
