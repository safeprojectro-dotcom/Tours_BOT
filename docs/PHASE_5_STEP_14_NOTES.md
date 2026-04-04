# Phase 5 / Step 14 — Waitlist MVP entry

## Scope (done)

- **Backend:** `MiniAppWaitlistService` (`app/services/mini_app_waitlist.py`) — join + status; uses existing `waitlist` table and `WaitlistRepository.get_active_entry`.
- **API:**
  - `GET /mini-app/tours/{tour_code}/waitlist-status?telegram_user_id=` → `{ eligible, on_waitlist }`
  - `POST /mini-app/tours/{tour_code}/waitlist` body `{ telegram_user_id, seats_count }` → `{ outcome, waitlist_entry_id }`
  - Outcomes: `created`, `already_exists`, `invalid_tour`, `not_eligible` (HTTP 200; honest outcomes, no fake booking).
- **Eligibility:** tour exists, `OPEN_FOR_SALE`, `seats_available == 0` (sold out). If seats remain, use normal booking — waitlist returns `not_eligible`.
- **Mini App:** Tour detail shows **Prepare reservation** only when `is_available`; sold-out open tours show waitlist copy + **Join waitlist**; **already on waitlist** replaces duplicate CTA.
- **Private chat:** `waitlist_private_hint` in tour detail message when sold out + open for sale (EN/RO in `messages.py`; other langs fall back to EN via `translate`).
- **Out of scope:** auto-promotion from waitlist, operator workflow, notifications, admin, payment/reservation/hold/reconciliation changes.

## Manual smoke

1. Tour with seats → catalog → detail → **Prepare reservation** (unchanged).
2. Tour sold out (`OPEN_FOR_SALE`, 0 seats) → detail → waitlist intro + **Join waitlist** → snackbar “recorded / not a booking”.
3. Submit again → **already on waitlist** / snackbar already exists.
4. Bot tour detail for sold-out open tour includes waitlist hint pointing to Mini App.

## Tests

- `tests/unit/test_api_mini_app.py`: waitlist status, join, duplicate, not eligible, invalid tour.
