# HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP

## Checkpoint

B14E diagnosed that temporary hold expiry logic exists but expired holds may remain persisted as active if no committing expiry path runs.

Production evidence from smoke:

- Tour **#6** / **`B10-SO12-04fb1f`**
- Order **#52:** 1 seat, expired, still **`active_temporary_hold`**
- Order **#53:** 2 seats, expired, still **`active_temporary_hold`**
- Tour **#6** **`seats_available`** remained **7** after expiry times

B14E code finding:

- **`ReservationExpiryService`** can release seats.
- Worker exists but is **not** automatically started in-app.
- Some lazy expiry **GET** paths called expiry **without** **`commit`**.
- Admin reads **do not** execute expiry.

## B14F purpose

Implement a **narrow** code fix so existing lazy expiry paths **persist** expiry changes safely.

**Status:** **Implemented** in repo (see sections below). Canonical trace: **`docs/B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC.md`** §10.

## Safety (B14F authoring)

No production API calls. No production data mutation. No hardcoded production order IDs in code. No publish/retry/resend. No execution-link mutation. No orders/payments/reservations created by the change. No CTA changes. No weakening of Layer A guards.

## Expected next decision

After **deploy**:

1. **Deploy** B14F build.
2. Run a **safe** post-deploy read/trigger check for historical smoke orders **#52/#53** (e.g. **`GET /mini-app/catalog`**, **`GET …/bookings`**, **`GET …/preparation`**, or worker) — **operator-owned**.
3. If lazy expiry path cleans them, **record** result.
4. If not, decide between:
   - running **`run_reservation_expiry_once`** (scheduled job);
   - adding an admin expire endpoint (future prompt);
   - controlled operator cleanup with documented semantics (**`mark-cancelled-by-operator`** vs **`cancelled_no_payment`**).

---

## What was fixed

- **Root cause:** `lazy_expire_due_reservations` updated the SQLAlchemy session, but many **Mini App read** handlers (and **`payment-entry`** on **400** with **`rollback()`**) closed the session **without** `commit`, so seat release and **`cancelled_no_payment`** state **rolled back**. **`PrivateReservationPreparationService.get_preparable_tour`** (Telegram **`with SessionLocal()`** without commit) had the same pattern.
- **Fix:** **`lazy_expire_due_reservations_commit_if_any`** in **`app/services/reservation_expiry.py`** — delegates to **`ReservationExpiryService.expire_due_reservations`** and calls **`session.commit()`** only when **expired_count > 0**. No duplicated eligibility rules.

## Code paths changed

| Module | Change |
|--------|--------|
| `app/services/reservation_expiry.py` | New **`lazy_expire_due_reservations_commit_if_any`** |
| `app/services/catalog_preparation.py` | **`list_catalog_cards`** uses commit-if-any |
| `app/services/mini_app_tour_detail.py` | **`get_tour_detail`** uses commit-if-any |
| `app/services/mini_app_bookings.py` | **`list_bookings`**, **`get_booking_detail`** use commit-if-any |
| `app/services/mini_app_booking.py` | **`get_reservation_overview_for_user`**, **`start_payment_entry`** use commit-if-any; **`create_temporary_reservation`** keeps **`lazy_expire_due_reservations`** only |
| `app/bot/services.py` | **`get_preparable_tour`** uses commit-if-any |

## Tests

- **`tests/unit/test_services_reservation_expiry.py`** — commit-if-any persists; no commit when zero expired.
- **`tests/unit/test_services_mini_app_catalog.py`** — catalog list persists expiry + lifecycle; future hold unchanged.
- **`tests/unit/test_services_mini_app_booking.py`** — overview + payment-entry persist expiry, seats restored, lifecycle **`expired_unpaid_hold`**.
- **`tests/unit/test_api_mini_app.py`** — **`test_create_reservation_and_payment_entry_routes`** uses **relative** departure dates (was flaky when wall-clock passed **`sales_deadline`**).

**Run:**  
`pytest tests/unit/test_services_reservation_expiry.py tests/unit/test_services_mini_app_catalog.py tests/unit/test_services_mini_app_booking.py tests/unit/test_bot_private_foundation.py tests/unit/test_api_mini_app.py -q` — **all passed** (authoring run).

## What remains open

- **Admin HTTP reads** still do **not** run lazy expiry (by design this slice).
- **`describe_order_admin_lifecycle`** unchanged — still **persisted** fields only.
- **Scheduler:** **`app/workers/reservation_expiry.run_once`** still **not** wired to startup; **recommended** for ops when there is no Mini App/traffic-driven commit path.

## Production follow-up (incl. smoke #52 / #53)

**B14G — PASS:** Handoff **[`docs/HANDOFF_B14G_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_VERIFICATION_TO_NEXT_STEP.md`](HANDOFF_B14G_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_VERIFICATION_TO_NEXT_STEP.md)**; metrics **[`docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`](B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md)**.

After deploy:

1. **Hit a committing path** (e.g. **`GET /mini-app/catalog`**, **`GET …/preparation`**, **`GET /mini-app/bookings`**, or run **`run_reservation_expiry_once`** in production job) so any clock-expired holds persist **`cancelled_no_payment`** and **seats** restore.
2. **Re-read admin** — orders should show **`expired_unpaid_hold`** (not **`active_temporary_hold`**) when DB updated; **Tour #6** **`seats_available`** should reflect releases.
3. **Handoff #86** on historical **#53** — close/update per support workflow (**not** hardcoded in app).

## Next recommended prompt

- **B14G — production cleanup / verification** for Tour **#6** and smoke orders (operator-owned checklist + optional worker schedule doc).  
- Optional later: admin read lazy-expire or **`POST /admin/orders/.../expire-hold`** if product wants parity without customer traffic.
