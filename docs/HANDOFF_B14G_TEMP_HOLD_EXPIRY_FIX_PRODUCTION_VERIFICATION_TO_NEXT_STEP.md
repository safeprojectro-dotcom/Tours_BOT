# HANDOFF_B14G_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_VERIFICATION_TO_NEXT_STEP

**Companion record (metrics / §6):** **[`docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`](B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md)**  
**Prior fix:** **[`docs/HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md`](HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md)**

---

## Checkpoint

B14F was **deployed** and **production-verified** (commit **`58968a5`**, message: `fix: persist lazy reservation expiry`).

**Trigger used:**

- `GET /mini-app/tours/B10-SO12-04fb1f/preparation`

**Result:**

- Order **#52** changed from **`active_temporary_hold`** to **`expired_unpaid_hold`**
- Order **#53** changed from **`active_temporary_hold`** to **`expired_unpaid_hold`**
- **`payment_status`** → **`unpaid`**
- **`cancellation_status`** → **`cancelled_no_payment`**
- **`reservation_expires_at`** → **`null`**
- Tour **#6** seats restored **7 → 10**
- Offer **#12** conversion chain remains valid:
  - showcase published
  - tour bridge linked
  - catalog **listed_for_sale**
  - booking link **active**
  - **customer_action** **open_exact_mini_app_tour**

---

## Closed

- B14D boarding remediation verified (prep path usable for this tour).
- B14F lazy expiry **persistence** verified in production.
- Smoke holds **#52/#53** no longer block seats on Tour **#6**.

---

## Still open

- Scheduler / worker for **off-traffic** expiry remains **recommended** (`app/workers/reservation_expiry.run_once`).
- **Handoff #86** on Order **#53** remains **open** — review with support ops.
- **`ADMIN_API_TOKEN` rotation** reminder if not already completed post-smoke.

---

## Recommended next step

Return to the supplier-offer / showcase / bridge roadmap after recording this result.

**Possible next prompts:**

- `CURSOR_PROMPT_B14H_RETURN_TO_SUPPLIER_OFFER_CTA_OR_NEXT_ROADMAP_STEP.md`

Or, if the **reservation expiry worker** should be addressed now:

- `CURSOR_PROMPT_B14H_RESERVATION_EXPIRY_WORKER_SCHEDULING_DESIGN.md`
