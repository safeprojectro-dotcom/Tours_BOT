# B16 — Admin OPS visibility (read-only dashboard)

**Status:** Step 1 implemented (read-only API).  
**Builds on:** [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md) (publishing console **B15B–F** remains the supplier-offer **channel** readiness surface).  
**Code:** `app/schemas/admin_ops_dashboard.py` · `app/services/admin_ops_dashboard_service.py` · `app/api/routes/admin.py`.  
**Handoff:** [`docs/HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP.md`](HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP.md).  
**Original prompt:** [`docs/CURSOR_PROMPT_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`](CURSOR_PROMPT_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md).

---

## 1. Objective

**B16** starts **Admin / OPS visibility** after the **B15** publishing-console foundation. Step 1 gives operators a **read-only** aggregation of **tours**, **orders / holds**, **showcase publication attempts**, **supplier-offer execution links**, and **attention** rows so they can orient after publication—without turning this route into a workflow executor.

---

## 2. Endpoint

- **`GET /admin/ops-dashboard`**
- **Auth:** same as other `/admin` routes (`ADMIN_API_TOKEN` via `Authorization: Bearer …` or `X-Admin-Token`, per existing admin router dependencies).
- **Read-only:** no writes, no Telegram, no Layer A side effects.

---

## 3. Response sections (`AdminOpsDashboardRead`)

| Section | Role |
|---------|------|
| `summary` | Bounded numeric counts for ops orientation (see §4). |
| `attention_items` | Short, conservative hints (sample rows — not exhaustive queues). |
| `recent_orders` | Recent orders as **`AdminOrderListItem`** (same family as admin order list reads). |
| `upcoming_tours` | Next departures among **non-terminal** future tours (`AdminOpsUpcomingTourRead`). |
| `recent_publications` | Latest **`SupplierOfferShowcasePublishAttempt`** rows (`AdminOpsRecentPublicationRead`). |
| `conversion_links` | Newest **`SupplierOfferExecutionLink`** rows joined with **`Tour.code`** (`AdminOpsConversionLinkRead`). |
| `generated_at` | UTC timestamp when the payload was built. |
| `audit_hint` | States that the endpoint is read-only (no mutation / Telegram send). |

---

## 4. Summary fields (`AdminOpsDashboardSummary`)

Implemented field names (see `app/schemas/admin_ops_dashboard.py`):

| Field | Meaning (high level) |
|-------|----------------------|
| `upcoming_tours_count` | Tours with **future** departure and status not **cancelled** / **completed**. |
| `open_for_sale_tours_count` | Tours with **`open_for_sale`** status. |
| `active_holds_count` | Orders matching **active temporary hold** lifecycle (aligned with admin lifecycle helpers). |
| `pending_payment_orders_count` | Orders with **`payment_status == awaiting_payment`** (count may overlap holds). |
| `confirmed_orders_count` | **Confirmed paid** + **ready for departure paid** lifecycle classes. |
| `expired_or_closed_orders_count` | **Expired unpaid hold** lifecycle **or** other **non-active** cancellation states (excluding move-to-another-* transitions). |
| `open_handoffs_count` | Handoffs with **`status == open`**. |
| `attention_items_count` | Length of the returned **`attention_items`** list (bounded samples, not global queue depth). |

**Note:** There is **no** `recent_publications_count` (or similar) on **`summary`** in Step 1; use **`len(recent_publications)`** client-side or the **`recent_publications`** list directly.

---

## 5. Attention item semantics (`AdminOpsAttentionItemRead`)

Stable **`kind`** values (string) include:

- **`payment_pending`** — active temporary hold; **`severity`** typically **`info`**.
- **`hold_expired_unpaid`** — expired unpaid hold; **`severity`** **`warning`**.
- **`open_handoffs`** — aggregate row when **open handoffs** exist; points to **`/admin/handoffs`**.
- **`showcase_publish_failed`** — recent **failed** showcase publish attempts.

Fields: **`severity`** (`info` | `warning` | `error`), **`title`**, **`summary`**, **`admin_path`**, optional **`related_order_id`**, **`related_tour_id`**, **`related_supplier_offer_id`** (offer inferred from an **active** execution link for the tour when available).

These are **read-only hints**; they do not replace **`GET /admin/orders/{id}`**, **`GET …/review-package`**, or handoff workflows.

---

## 6. Source-of-truth policy

- The dashboard **aggregates** existing **orders**, **tours**, **publish attempts**, **execution links**, and **handoffs** from the database plus **`AdminReadService.list_orders`** for **`recent_orders`**.
- It **does not** own **business rules**, **payment truth**, or **reconciliation** beyond what existing enums / lifecycle classification already encode.
- It **does not** trigger reservation expiry, payment completion, or any **Layer A** mutation paths.

---

## 7. Safety boundaries (Step 1)

This endpoint must **not**:

- mutate orders or payments;
- expire or “fix” reservations;
- change seats or tour inventory;
- send Telegram messages or run publish/retry;
- create supplier execution attempts;
- change **Layer A** or **Mini App routing**;
- introduce **migrations** for B16 Step 1.

---

## 8. Tests

```powershell
python -m pytest tests/unit/test_admin_ops_dashboard.py -q
```

**Result:** `4 passed`.

Regression pairing with publishing console (same app/session harness style):

```powershell
python -m pytest tests/unit/test_admin_ops_dashboard.py tests/unit/test_admin_publishing_console.py -q
```

**Combined:** `12 passed` (8 + 4).

---

## 9. Relationship to **`GET /admin/overview`**

- **`GET /admin/overview`** — coarse totals (**`AdminOverviewRead`**: e.g. approximate tour/order counts, open handoffs, waitlist).
- **`GET /admin/ops-dashboard`** — **richer, ops-oriented** slice: lifecycle-oriented order counts, bounded lists, publication and execution-link recency, attention samples.

---

## 10. Next steps

1. **B16B** — filters / pagination / time-window query parameters.
2. **B16C** — dashboard → admin detail navigation polish.
3. **B16D** — explicit OPS **actions** (**design-only** first).
4. **B16E** — notification / audit visibility (**read-only**).
