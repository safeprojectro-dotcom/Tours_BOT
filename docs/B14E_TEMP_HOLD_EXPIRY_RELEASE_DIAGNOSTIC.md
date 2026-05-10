# B14E — Temporary hold expiry and inventory release (read-only diagnostic)

**Project:** Tours_BOT. **Type:** code-backed diagnostic only — **no** production calls, **no** mutations, **no** app code changes in this prompt.

**Refs:** B13G/B14D smoke context — Supplier Offer **#12**, Tour **#6**, **`B10-SO12-04fb1f`**, boarding point **#15** (post-B14D).

---

## 1. Context and smoke facts

| Item | Value |
|------|--------|
| **Tour** | **#6** (`tour_code` **`B10-SO12-04fb1f`**) |
| **Seats** | **`seats_total = 10`**; after two holds, **`seats_available = 7`** (10 − 1 − 2) |
| **Order #52** | **`seats_count = 1`**, **`booking_status = reserved`**, **`payment_status = awaiting_payment`**, **`cancellation_status = active`**, **`lifecycle_kind = active_temporary_hold`**, past **`reservation_expires_at`** |
| **Order #53** | **`seats_count = 2`**, same persisted tri-state as #52, past **`reservation_expires_at`**; **open handoff #86** (Mini App booking detail/support) |
| **Observed problem** | After wall-clock **`reservation_expires_at`**, **admin read** still showed **`active_temporary_hold`** and Tour **#6** stayed at **`seats_available = 7`** |

---

## 2. Where expiry is supposed to happen (code)

**Core service:** `app/services/reservation_expiry.py` — `ReservationExpiryService`.

- **`expire_order_if_due`**: eligible when **`reserved` + `awaiting_payment` + `active` + `reservation_expires_at IS NOT NULL` + `reservation_expires_at <= now`** (see `_is_eligible_for_expiry`).
- **Order updates:** **`payment_status → unpaid`**, **`cancellation_status → cancelled_no_payment`**, **`reservation_expires_at → null`**. **`booking_status` stays `reserved`** (expired unpaid hold shape documented in `describe_order_admin_lifecycle` / `docs/MINI_APP_UX.md`).
- **Tour updates:** **`seats_available`** restored with **`min(seats_total, seats_available + order.seats_count)`** (same cap pattern as operator cancel).

**Batch selection:** `app/repositories/order.py` — `list_expired_temporary_reservation_ids` uses the same predicate as eligibility (including **`reservation_expires_at <= now`**).

**Worker:** `app/workers/reservation_expiry.py` — `run_once` opens a session, runs `expire_due_reservations`, **`session.commit()`**. Nothing in-repo wires this to app startup; it is intended for **external** scheduling (cron / platform job).

**Lazy batch:** `lazy_expire_due_reservations(session, ...)` wraps `expire_due_reservations` with default limit **500** (`LAZY_EXPIRY_DEFAULT_LIMIT`).

---

## 3. Automatic vs lazy vs manual — and a persistence gap

| Mechanism | Persists expiry? | Notes |
|-----------|------------------|--------|
| **Reservation expiry worker** | **Yes** (explicit commit) | Requires job/cron to invoke `run_reservation_expiry_once` / `run_once`. Not started from `get_db` / FastAPI lifecycle. |
| **POST** `/mini-app/tours/{tour_code}/reservations` | **Yes** | Calls `lazy_expire` at start of `MiniAppBookingService.create_temporary_reservation`; route **`session.commit()`**. |
| **GET** `/mini-app/tours/{tour_code}/preparation` | **Yes** | `PrivateReservationPreparationService.get_preparable_tour` calls `lazy_expire` first; route **`session.commit()`** on success. |
| **GET** `/mini-app/tours/{tour_code}/preparation-summary` | **Yes** | Route **`session.commit()`**; preparation path uses `PrivateReservationPreparationService` (includes `lazy_expire`). |
| **POST** `/mini-app/orders/{order_id}/payment-entry` | **Yes** | `start_payment_entry` calls `lazy_expire`; route **`session.commit()`**. |
| **POST** `/mini-app/orders/{order_id}/mock-payment-complete` | **Yes** | Uses `lazy_expire`; route commits. |
| **GET** `/mini-app/catalog` | **Risk: no** | `CatalogPreparationService.list_catalog_cards` calls `lazy_expire`; **`get_catalog` does not call `session.commit()`**. `get_db` only closes the session → pending work is rolled back. |
| **GET** `/mini-app/tours/{tour_code}` | **Risk: no** | `MiniAppTourDetailService` uses `lazy_expire`; **`get_tour_detail` has no commit**. |
| **GET** `/mini-app/bookings` | **Risk: no** | `lazy_expire` in list; **`list_my_bookings` has no commit**. |
| **GET** `/mini-app/orders/{order_id}/booking-status` | **Risk: no** | `lazy_expire` in detail; **`get_booking_status` has no commit**. |
| **GET** `/mini-app/orders/{order_id}/reservation-overview` | **Risk: no** | `lazy_expire` in `get_reservation_overview_for_user`; **`get_reservation_overview` has no commit**. |
| **Admin reads** | **No** | Admin order/tour read paths do not invoke `lazy_expire`. |
| **Operator cancel / duplicate (active hold)** | **Yes** | `AdminOrderWriteService` restores seats and clears hold (explicit mutation + commit in route). |

**Conclusion:** Clock expiry **is not magic**. Persisted release happens when **`ReservationExpiryService`** runs **and** the database transaction **commits**. If operators only use **admin GET** after the deadline, or customers only hit **non-committing Mini App GETs**, orders can remain **`awaiting_payment` / `active`** with **`reservation_expires_at` still set**, and **`seats_available`** stays reduced — matching the B14E smoke observation.

This is **both** a possible **production scheduling gap** (worker not running) **and** a **request-layer gap** (lazy expiry on several GETs without commit).

---

## 4. Answers to the inspection checklist (1–10)

1. **Where is expiry supposed to happen?** In **`ReservationExpiryService.expire_order_if_due`** (worker or `lazy_expire_due_reservations`).
2. **Is there a scanner?** Yes — `list_expired_temporary_reservation_ids` + **`expire_due_reservations`** loop.
3. **Is it automatic on startup?** **No** in-repo. Worker must be scheduled externally. Lazy paths depend on traffic **and** committing routes.
4. **Admin read lifecycle?** **`describe_order_admin_lifecycle`** (`app/services/admin_order_lifecycle.py`) maps **persisted** fields only. **`active_temporary_hold`** is **`reserved` + `awaiting_payment` + `active` + `reservation_expires_at is not None`** — it does **not** compare `reservation_expires_at` to “now”. Clock-expired but not yet updated rows still read as active hold.
5. **Payment-entry / reservation-overview lazily expire?** **`start_payment_entry`** calls `lazy_expire` and the route **commits**. **`get_reservation_overview_for_user`** calls `lazy_expire` but the **GET route does not commit** — so it **does not reliably persist** expiry.
6. **Which function releases seats?** **`ReservationExpiryService.expire_order_if_due`** (and equivalently **`AdminOrderWriteService.mark_cancelled_by_operator` / `mark_duplicate`** for active-hold predicate — same seat math).
7. **Field changes after persisted expiry** (designed): **`payment_status → unpaid`**, **`cancellation_status → cancelled_no_payment`**, **`reservation_expires_at → null`**, **`lifecycle_kind` → `expired_unpaid_hold`**; **`booking_status`** remains **`reserved`**. Operator cancel uses **`cancelled_by_operator`** / **`duplicate`** instead of **`cancelled_no_payment`**.
8. **Safe existing admin endpoint to expire?** There is **no** dedicated “expire hold” admin endpoint. **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`** is allowed for **`_is_active_temporary_hold`** (includes **`reservation_expires_at is not None`** **without** requiring future expiry) and **restores seats** with the same cap rule. **`mark-duplicate`** on an active hold does the same seat restore. Both set **`payment_status = unpaid`** and clear **`reservation_expires_at`**; **`booking_status` unchanged**. Product/ops must accept **operator** or **duplicate** semantics vs **no-payment** expiry semantics.
9. **Safest remediation for smoke #52/#53** (conceptual; **not** executed from this doc):  
   - **Preferred product semantics:** run **`ReservationExpiryService`** to **`cancelled_no_payment`** (worker, or any **committing** lazy path, or a future controlled admin “expire hold”).  
   - **If only admin HTTP is available:** **`mark-cancelled-by-operator`** is **verified in code** to restore seats for the active-hold shape — including holds whose clock deadline passed but DB was never updated — **but** cancellation reason differs from expiry.  
   - **Handoff #86 on #53:** resolve or close per support workflow before/after cleanup to avoid confusing operators.
10. **Gap type?** **Configuration / operations** (worker not scheduled) **plus** **code path** (lazy expiry on several GETs without commit) **plus** **admin read model** (no clock check, no lazy expiry). Not “missing entire expiry implementation” — **missing reliable persistence and/or scheduling**.

---

## 5. Mini App vs admin UX (docs alignment)

- **`docs/MINI_APP_UX.md`**: timer and post-expiry copy assume backend-owned expiry; **`mini_app_booking_facade`** (`app/services/mini_app_booking_facade.py`) distinguishes **“expired before worker”** (`reserved` + `awaiting_payment` + `active` + past `reservation_expires_at`) vs **persisted** expired state.
- **`docs/TESTING_STRATEGY.md`**: calls out **reservation expiration** and **workers** as test/integration priorities — consistent with needing a scheduled job and/or commit-safe lazy paths.

---

## 6. Safe options for existing smoke orders (conceptual)

| Option | What it does | Caveats |
|--------|----------------|---------|
| **A — Wait for / run worker** | `app/workers/reservation_expiry.run_once` | Requires production job; **verify Railway/cron** actually runs it. |
| **B — Committing Mini App traffic** | e.g. open **preparation** (GET + commit) or **create** another reservation | Side effects; not ideal as “cleanup API”. |
| **C — Admin operator cancel** | `POST …/mark-cancelled-by-operator` | **Releases seats** for active-hold shape; **semantic** is operator cancel, not `cancelled_no_payment`. |
| **D — Ops script** | Call service/worker with DB session commit in controlled environment | Same as A, explicit. |
| **E — Future admin expire endpoint** (B14F) | Persists **`cancelled_no_payment`** + seat restore | Product/API design follow-up. |

---

## 7. Risk analysis

| Risk | Notes |
|------|--------|
| **Overselling** | If **`seats_available`** is wrong-low due to stale holds, **new** reservations can see fewer seats than truly free **until** expiry persists or operator intervenes. |
| **Stale holds** | Holds staying **`awaiting_payment` / `active`** after deadline until a commit path runs confuses **admin lifecycle** and reporting. |
| **Manual cancellation** | **`mark-cancelled-by-operator`** / **`mark-duplicate`** change **`cancellation_status`** and clear **`reservation_expires_at`**; audit/support must treat as **operator** or **duplicate**, not auto **no-payment**. |
| **Handoff #86 (Order #53)** | Open support handoff may reference an order still shown as “active” hold; coordinate closure. |

---

## 8. Recommendations (next tracks; not executed here)

- **B14F (implementation / fix):** ~~(1) Add **`session.commit()`** (or equivalent) to Mini App GET routes that call **`lazy_expire`**, **or** move lazy expiry to middleware / dependency that commits safely~~ **Done** — see **§10** and **`docs/HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md`**. Remaining optional: **`lazy_expire` on admin order/tour read** or dedicated **`POST /admin/…/expire-hold`**; extend **`describe_order_admin_lifecycle`** for clock-expired read clarity.  
- **B14G (production cleanup):** Confirm whether **`run_reservation_expiry_once`** is scheduled; remediate smoke **#52/#53** via **worker**, **committing lazy path**, or **admin mark-cancel** after product accepts semantics; handle **handoff #86**.

---

## 9. Key file index

| Area | Path |
|------|------|
| Expiry service | `app/services/reservation_expiry.py` |
| Worker | `app/workers/reservation_expiry.py` |
| Expired id query | `app/repositories/order.py` — `list_expired_temporary_reservation_ids` |
| Admin lifecycle labels | `app/services/admin_order_lifecycle.py` |
| Operator cancel / duplicate | `app/services/admin_order_write.py` |
| Hold creation (seat decrement) | `app/services/reservation_creation.py` — `TemporaryReservationService` |
| Payment entry gate (no lazy — eligibility only) | `app/services/payment_entry.py` — `_is_order_valid_for_payment_entry` rejects `reservation_expires_at <= now` |
| Mini App facade (clock vs persisted) | `app/services/mini_app_booking_facade.py` |
| Lazy + commit vs not | `app/api/routes/mini_app.py` (compare routes with/without `session.commit()`) |

---

## 10. B14F implementation follow-up (2026)

**Shipped in code:** `lazy_expire_due_reservations_commit_if_any` in **`app/services/reservation_expiry.py`** — runs **`ReservationExpiryService.expire_due_reservations`** and **`session.commit()`** only when the expired count is **> 0**. Used on read-heavy / rollback-prone paths: **`CatalogPreparationService`**, **`MiniAppTourDetailService`**, **`MiniAppBookingsService`** (list + detail), **`MiniAppBookingService`** (**`get_reservation_overview_for_user`**, **`start_payment_entry`**), **`PrivateReservationPreparationService.get_preparable_tour`**. **`create_temporary_reservation`** still uses non-committing **`lazy_expire_due_reservations`** so expiry + new hold stay one transaction until the route **`commit()`**. **Admin reads** remain non-executors of expiry. **Scheduler/worker** still recommended for backlog/off-HTTP cleanup — see **[`docs/HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md`](HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md)**.

---

**End diagnostic — B14E.**
