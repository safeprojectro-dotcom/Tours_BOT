# Phase 5 / Step 12 — Payment edge cases & retry UX (Mini App)

## Scope

Presentation only: **no** API, schema, reconciliation, lazy expiry, or webhook changes.

## Booking detail

- Uses existing `facade_state` + `primary_cta` from `GET /mini-app/orders/{id}/booking-status`.
- Below the summary card, a **context note** explains next steps:
  - **Active hold:** pay before deadline; after confirmation → Confirmed section.
  - **Confirmed / in-trip:** paid; review in My bookings.
  - **Expired / released / other:** hold not active; new reservation from catalog if seats exist.
- Booking reference line uses localized `line_reservation_ref` (was hardcoded English).

## Payment screen

- After a **successful** payment-entry load, the intro switches to **`payment_intro_active_hold`** (deadline-focused).
- **HTTP 400** on payment-entry start → localized **`payment_screen_unavailable_hold`** (expired/released hold); Pay / Back-to-bookings buttons hidden.
- Other load errors → **`payment_screen_load_error_generic`**.
- **HTTP 403** on mock-complete → user-facing **`payment_mock_disabled_user_message`** (SnackBar), not a raw technical line.
- Other confirm errors → **`payment_confirm_error_generic`**.

## Files

- `mini_app/presentation_notes.py` — `booking_detail_context_note()`
- `mini_app/app.py` — `BookingDetailScreen`, `PaymentEntryScreen`
- `mini_app/ui_strings.py` — en + ro strings for the above
