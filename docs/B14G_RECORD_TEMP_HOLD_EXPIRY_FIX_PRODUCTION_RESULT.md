# B14G — Record: B14F temporary hold expiry fix (production verification)

**Type:** operator documentation / run log — **docs-only** (no application code in this step).  
**Primary handoff:** **[`docs/HANDOFF_B14G_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_VERIFICATION_TO_NEXT_STEP.md`](HANDOFF_B14G_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_VERIFICATION_TO_NEXT_STEP.md)**  
**Prior fix:** **[`docs/HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md`](HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md)**

---

## 1. Shipped fix (reference)

| Field | Value |
|--------|--------|
| **Commit** | **`58968a5`** |
| **Message** | `fix: persist lazy reservation expiry` |
| **Mechanism** | **`lazy_expire_due_reservations_commit_if_any`** — commits when **`ReservationExpiryService`** expires at least one due hold |

**Paths with committing lazy expiry (B14F):** catalog, tour detail, bookings list/detail, reservation overview, payment entry (before gate), **`get_preparable_tour`** / Mini App preparation + Telegram private prep.

---

## 2. Production context (smoke IDs)

| Field | Value |
|--------|--------|
| **supplier_offer_id** | **12** |
| **tour_id** | **6** |
| **tour_code** | **`B10-SO12-04fb1f`** |
| **execution_link_id** | **5** |
| **boarding_point_id** | **15** |
| **Order #52** | **`seats_count = 1`**, smoke temporary hold |
| **Order #53** | **`seats_count = 2`**, smoke temporary hold; **open handoff #86** (support — operator-owned) |

---

## 3. State before this verification (post-expiry clock, pre-B14F behavior)

| Check | Value |
|--------|--------|
| **Tour #6 `seats_total`** | **10** |
| **Tour #6 `seats_available`** | **7** (holds still consuming inventory in DB) |
| **Order #52 `lifecycle_kind`** | **`active_temporary_hold`** (persisted; past **`reservation_expires_at`**) |
| **Order #53 `lifecycle_kind`** | **`active_temporary_hold`** (same) |

---

## 4. Verification trigger (operator)

After B14F **deploy**, operator ran **read-only** Mini App preparation (commits on success — aligns with B14F **`get_preparable_tour`** path):

```powershell
$TourCode = "B10-SO12-04fb1f"

Invoke-RestMethod `
  -Uri "$Base/mini-app/tours/$TourCode/preparation" `
  -Method GET | ConvertTo-Json -Depth 5
```

**Rationale:** **`GET /mini-app/tours/{tour_code}/preparation`** calls **`MiniAppReservationPreparationService.get_preparation`** → **`PrivateReservationPreparationService.get_preparable_tour`**, which runs **`lazy_expire_due_reservations_commit_if_any`**; the route **`session.commit()`** on **200** (see **`app/api/routes/mini_app.py`**).

---

## 5. Post-trigger expected outcomes (for PASS)

When expired holds **#52** and **#53** are processed by the service:

- **`Tour.seats_available`** should return to **10** (cap **`seats_total`**).
- Admin order reads should show **`lifecycle_kind = expired_unpaid_hold`** (**`cancelled_no_payment` / `unpaid`**, **`reservation_expires_at`** null, **`booking_status`** still **`reserved`**).
- **`GET …/preparation`** body should show **`seats_available_snapshot`** consistent with restored inventory (**10** if no other holds).

---

## 6. Recorded outcome

**Verification:** Post-deploy, after commit **`58968a5`** on production; operator **`GET /mini-app/tours/B10-SO12-04fb1f/preparation`** then admin re-reads (exact UTC timestamp optional).

| Check | After trigger | Source (e.g. admin JSON, prep key) |
|--------|----------------|-------------------------------------|
| **HTTP `GET …/preparation`** | **200** | Mini App / operator verification |
| **`seats_available_snapshot` (prep)** | **10** | preparation JSON (`tour.seats_available_snapshot` / equivalent) |
| **Admin Tour #6 `seats_available`** | **10** (restored from **7**) | **`GET /admin/tours/6`** |
| **Order #52 lifecycle / `cancellation_status`** | **`expired_unpaid_hold`**; **`cancelled_no_payment`** | admin order read |
| **Order #53 lifecycle / `cancellation_status`** | **`expired_unpaid_hold`**; **`cancelled_no_payment`** | admin order read |
| **Order #52 / #53 `payment_status`** | **`unpaid`** | admin order read |
| **Order #52 / #53 `reservation_expires_at`** | **`null`** | admin order read |
| **Handoff #86** | **Still open** — support ops | manual |

**PASS / FAIL / PARTIAL:** **PASS**

**Conversion chain sanity (Offer #12):** unchanged — showcase published, tour bridge linked, catalog **listed_for_sale**, booking link **active**, **customer_action** **open_exact_mini_app_tour**.

**Notes:** Lazy expiry executed via **`get_preparable_tour`** + route **commit** as designed in B14F. B14D boarding remediation remains prerequisite for prep **200** on this tour.

---

## 7. Follow-ups

- **Scheduler/worker:** **`run_reservation_expiry_once`** still recommended for off-traffic / backlog hygiene (no code change in B14F/B14G).
- **Handoff #86** on **Order #53:** review/close per support ops — not cleared by expiry alone.
- **`ADMIN_API_TOKEN`:** rotate if not already done post-smoke (existing runbook discipline).

## 8. Recommended next prompts (optional)

- Return to supplier-offer / showcase / bridge roadmap — e.g. **`CURSOR_PROMPT_B14H_RETURN_TO_SUPPLIER_OFFER_CTA_OR_NEXT_ROADMAP_STEP.md`** (product-defined).
- If scheduler should be addressed next: **`CURSOR_PROMPT_B14H_RESERVATION_EXPIRY_WORKER_SCHEDULING_DESIGN.md`** (product-defined).

---

**End B14G record.**
