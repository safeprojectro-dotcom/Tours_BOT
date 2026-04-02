# Phase 5 Step 9 — hold / payment lifecycle (staging + production-safe)

## Current behavior (unchanged rules)

- **Hold creation:** `TemporaryReservationService.create_temporary_reservation` decrements `tours.seats_available`, creates an `orders` row with `booking_status=reserved`, `payment_status=awaiting_payment`, `cancellation_status=active`, and sets `reservation_expires_at` from `calculate_reservation_expiration` (hold window capped by `sales_deadline` when present).
- **Expiry processing:** `ReservationExpiryService.expire_order_if_due` runs for eligible orders: `reserved` + `awaiting_payment` + `active` + `reservation_expires_at <= now`. It restores `seats_available` on the tour (capped at `seats_total`) and updates the order to `payment_status=unpaid`, `cancellation_status=cancelled_no_payment`, `reservation_expires_at=null`. Booking status stays `reserved` (historical snapshot).
- **Background worker:** `app/workers/reservation_expiry.run_once` can still batch-expire orders; it uses the same service.

## Step 9 change: lazy expiry on read paths

Without relying on a cron on every host, **expired holds are processed eagerly** by calling `lazy_expire_due_reservations(session)` (wrapper around `expire_due_reservations` with a bounded batch size) at the start of:

- `CatalogPreparationService.list_catalog_cards` — refreshes seat counts for **catalog** (Mini App + bot browse).
- `PrivateReservationPreparationService.get_preparable_tour` — **prepare** flows see up-to-date `seats_available`.
- `MiniAppTourDetailService.get_tour_detail` — detail deep-links.
- `MiniAppBookingService` — `create_temporary_reservation`, `start_payment_entry`, `get_reservation_overview_for_user`.
- `MiniAppBookingsService` — `list_bookings`, `get_booking_detail`.

Effects:

- **False sold out** from stale unpaid holds is reduced: seats return when the user (or anyone) hits catalog/prepare after the hold deadline.
- **Idempotent:** safe to call on every request; each run processes up to **500** expired orders (configurable constant in `reservation_expiry.py`).

## Mini App copy

Booking list/detail use **localized shell strings** keyed by `facade_state` (`booking_facade_labels` in `mini_app/ui_strings.py`) instead of the API’s English labels, so UI language matches **Language & settings** for status lines.

## Manual lifecycle test (staging)

1. Create a temporary reservation on a test tour; note `reservation_expires_at` (or use a short hold by adjusting tour departure/sales in a dev DB only if allowed).
2. Wait until after expiry **or** advance clock in a controlled test DB.
3. Open **catalog** or **prepare** again without running the reset script: **seats** on the tour should increase and the order should show as released / expired in **My bookings** (after lazy expiry runs on that request).
4. **Pay Now** should no longer apply to an expired hold (payment entry rejects expired reservation).

## Out of scope

- Payment provider integration beyond current mock / payment-entry flow.
- New migrations, Railway layout, webhook transport, admin/operator tools.
- Strong guarantees if more than **500** expired orders pile up before any read — run the existing worker or increase `LAZY_EXPIRY_DEFAULT_LIMIT` operationally if needed.
