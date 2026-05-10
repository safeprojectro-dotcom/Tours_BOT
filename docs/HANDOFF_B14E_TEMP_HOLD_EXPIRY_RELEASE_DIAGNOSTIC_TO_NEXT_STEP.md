# HANDOFF_B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC_TO_NEXT_STEP

## Checkpoint

B14D remediation succeeded:

- Tour **#6** got boarding point **#15**.
- Mini App preparation endpoint works.
- Manual Mini App flow created temporary reservations:
  - Order **#52**, 1 seat
  - Order **#53**, 2 seats
- Tour **#6** `seats_available` changed from **10** to **7**.

Problem:

- After `reservation_expires_at`, Orders **#52/#53** still show `active_temporary_hold`.
- Tour **#6** still shows `seats_available = 7`.

## B14E purpose

Read-only diagnostic to determine:

- whether automatic expiry/release exists;
- whether it is configured/running;
- which code path releases seats;
- how to safely clean existing smoke orders;
- whether a new admin endpoint/job is needed.

**Outcome:** B14E is complete — see **[`docs/B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC.md`](B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC.md)** (full detail).

## Safety (B14E execution)

No production API calls. No production data mutation. No cancellation. No payments. No reservations. No publish/retry/resend. No execution-link changes.

## Findings (summary)

- **Expiry logic exists** in **`app/services/reservation_expiry.py`** (`ReservationExpiryService.expire_order_if_due`): restores **`tour.seats_available`** (capped) and sets **`payment_status=unpaid`**, **`cancellation_status=cancelled_no_payment`**, **`reservation_expires_at=null`**; **`booking_status`** stays **`reserved`**.
- **Background worker** **`app/workers/reservation_expiry.run_once`** commits a batch — **not** wired to app startup in-repo; needs **external** scheduling unless ops rely on **lazy** paths only.
- **Lazy expiry** runs on several **Mini App** services, but **many GET routes** call **`lazy_expire_due_reservations`** **without** **`session.commit()`**, so **`get_db`** session close **rolls back** persistence — **admin-only** checks after the deadline can see **stale** holds and **stale** seat counts.
- **Committing** customer paths include e.g. **`GET /mini-app/tours/{code}/preparation`**, **`POST …/reservations`**, **`POST …/payment-entry`**, **`preparation-summary`** (via `get_preparable_tour`).
- **Admin lifecycle** (`describe_order_admin_lifecycle`) is **persisted-state only** — **`active_temporary_hold`** if **`reservation_expires_at is not null`**, **ignoring** whether that timestamp is already in the past.
- **No** dedicated admin **`/expire`** endpoint. **`POST /admin/orders/{id}/mark-cancelled-by-operator`** (and **`mark-duplicate`** on active hold) **restores seats** for the same **active temporary hold** predicate **including** clock-expired-but-not-persisted rows; cancellation semantics differ from **`cancelled_no_payment`**.

## Expected next decision

After B14E:

- **If worker or committing lazy path is acceptable:** run controlled cleanup for **#52/#53** (e.g. schedule/invoke **`run_reservation_expiry_once`**, or trigger a **committing** Mini App path such as **`GET …/preparation`** for the tour) so rows become **`cancelled_no_payment`** and seats restore — **operator-owned**, still **no** ad-hoc production calls from Cursor.
- **If admin-only cleanup is required:** **`mark-cancelled-by-operator`** (or **`mark-duplicate`**) is **code-verified** to release seats for active holds — only if **operator/duplicate** semantics are acceptable; resolve **handoff #86** on **#53**.
- **If product wants first-class expiry semantics on all reads:** implement **B14F** (commit-after-lazy on affected GETs, optional admin expire/read parity) **with tests**, then **B14G** cleanup as needed.

## Recommended next prompt

- **B14F:** Implement fix — e.g. **commit** after lazy expiry on affected Mini App GETs (or centralize), optional **admin read** lazy-expire or **`POST …/expire-hold`**, optional lifecycle label for clock-expired persisted holds.
- **B14G:** Production cleanup — confirm **`run_reservation_expiry_once`** schedule; remediate **#52/#53** via worker, committing lazy path, or accepted admin mutation; resolve **handoff #86** on **#53**.

## Safe cleanup endpoint?

- **Dedicated “expire hold” admin API:** **no.**
- **`mark-cancelled-by-operator`:** **code-verified** seat release for **active temporary hold** shape — use only if **operator-cancel** semantics are acceptable for smoke cleanup.
- **`mark-duplicate`:** same seat restore on active hold; **duplicate** semantics.

## Can production #52/#53 be cleaned now?

- **Yes, only after explicit operator approval** and choice of semantics:
  - **Preferred** if available: run **reservation expiry worker** or a **committing** path so rows become **`cancelled_no_payment`**.
  - **Admin alternative:** **`mark-cancelled-by-operator`** (or duplicate) — **releases seats** per code, but **audit/reason** differs from auto-expiry.
- **Caution:** **#53** has **open handoff #86** — coordinate support closure.

**No production mutation was performed from Cursor for B14E.**
