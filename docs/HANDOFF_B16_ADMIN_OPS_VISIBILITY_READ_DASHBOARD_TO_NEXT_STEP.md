# HANDOFF_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD_TO_NEXT_STEP

## Status: B16 Step 1 implemented (read-only); docs synced

- **Design record:** [`docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`](B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md).
- **Spec / prompt:** [`docs/CURSOR_PROMPT_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`](CURSOR_PROMPT_B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md).
- **Docs sync prompt:** [`docs/CURSOR_PROMPT_B16_DOCS_SYNC_AFTER_OPS_DASHBOARD.md`](CURSOR_PROMPT_B16_DOCS_SYNC_AFTER_OPS_DASHBOARD.md).
- **Endpoint:** **`GET /admin/ops-dashboard`** — same **`ADMIN_API_TOKEN`** gate as other `/admin` routes.
- **Code:** `app/schemas/admin_ops_dashboard.py`; `app/services/admin_ops_dashboard_service.py` (`AdminOpsDashboardService.read_dashboard`); `app/api/routes/admin.py` (`get_admin_ops_dashboard`).
- **Tests:** **`tests/unit/test_admin_ops_dashboard.py`** — **`4` passed** (`python -m pytest tests/unit/test_admin_ops_dashboard.py -q`). **Regression pairing** with **`test_admin_publishing_console.py`**: **`12` passed** total.

**Context:** After B15 publishing-console foundation — [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md).

---

## Response sections (Step 1)

Top-level **`AdminOpsDashboardRead`**:

- **`summary`** — counts (`upcoming_tours_count`, `open_for_sale_tours_count`, `active_holds_count`, `pending_payment_orders_count`, `confirmed_orders_count`, `expired_or_closed_orders_count`, `open_handoffs_count`, `attention_items_count`). There is **no** `recent_publications_count` on the summary; use the **`recent_publications`** list.
- **`attention_items`**
- **`recent_orders`** — **`AdminOrderListItem`**
- **`upcoming_tours`**
- **`recent_publications`**
- **`conversion_links`**
- **`generated_at`**
- **`audit_hint`**

---

## Safety (confirmed for Step 1)

**Read-only:** no order mutation, payment completion, reservation expiry mutation, seat changes, Telegram send/publish/retry, supplier execution attempt creation, Layer A changes, Mini App routing changes, or migrations introduced for this slice.

---

## Next recommended options

1. **B16B** — filters / pagination / time-window query params.
2. **B16C** — dashboard → admin detail navigation polish.
3. **B16D** — explicit OPS actions (**design-only** first).
4. **B16E** — notification / audit visibility (read-only).
