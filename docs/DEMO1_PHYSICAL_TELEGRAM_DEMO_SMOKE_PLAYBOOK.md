# DEMO-1 — Physical Telegram demo / smoke playbook

Manual-only checklist for demonstrating an already-deployed Tours_BOT stack. This is **not** a product roadmap item (see `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` and checkpoint docs in-repo for roadmap context).

**Scope:** smoke the chain from **channel showcase** → **customer reservation/order** → **supplier notification outbox** → **manual outbox delivery** → **operational sales push preview** → **admin-gated channel publish**.

Runtime code changes are **out of scope** for this document.

---

## Preconditions (environment)

- API process running with **`ADMIN_API_TOKEN`** set (**admin endpoints return 503** if unset — see `app/api/admin_auth.py`).
- Telegram bot token and showcase channel configured: **`TELEGRAM_BOT_TOKEN`**, **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`** (supplier offer publish and **S1D-2** operational push use the same channel configuration where applicable).
- Database reachable from the API container/process.
- For Mini App flows: customer **`telegram_user_id`** must exist as a **`User`** row (Mini App rejects unknown ids on some endpoints).
- For **supplier outbox delivery (S1C-2)** the target **`supplier_notification_outbox`** row must have a resolved **`telegram_chat_id`** (or supplier Telegram mapping that delivery can resolve); otherwise delivery will skip/fail safely.

---

## Admin HTTP auth pattern

All routes under **`/admin/*`** share the FastAPI dependency **`require_admin_api_token`**:

- Preferred: header **`Authorization: Bearer <ADMIN_API_TOKEN>`**
- Alternate: **`X-Admin-Token: <ADMIN_API_TOKEN>`**

There is currently **no** admin HTTP API to **list** `supplier_notification_outbox` rows; obtain **`outbox_id`** via DB query (PostgreSQL table **`supplier_notification_outbox`**) or your own ops tooling.

---

## Demo flow (recommended order)

### 1) Supplier offer / tour appears in Telegram channel

**Goal:** Telegram showcase channel shows the published supplier offer card (public side effect).

1. Prep the offer through your normal moderation path (approve packaging, unblock channel send per existing B-blocks — depends on staging data).
2. **Publish to channel (admin):**

   - **`POST /admin/supplier-offers/{offer_id}/publish`**

   On success this path sends to the showcase channel **`and`** (internally **S1C-3**) enqueues a **`supplier_offer_published`** row in **`supplier_notification_outbox`** after successful Telegram send (**no** scheduler; **no** automatic supplier DM from outbox).

3. Observe the new channel message with the Telegram client subscribed to **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`**.
4. **Optional note:** the admin route best-effort may also invoke **`SupplierOfferSupplierNotificationService.notify_published`**, which can send an **immediate** short lifecycle DM **if** the supplier has **`primary_telegram_user_id`** configured; that path is distinct from **S1C-2 outbox delivery** (stored payload).

**Refs:** [`docs/HANDOFF_S1C3_WIRE_SUPPLIER_NOTIFICATION_AFTER_CHANNEL_PUBLISH.md`](HANDOFF_S1C3_WIRE_SUPPLIER_NOTIFICATION_AFTER_CHANNEL_PUBLISH.md).

---

### 2) Customer can reserve / create order

**Goal:** Layer A temporary reservation/order exists via Mini App APIs (exact UI path is Mini App/Flet-specific; API layer is documented here).

Representative HTTPS entry points (prefix **`/mini-app`**) include:

- Catalog / tour landing: **`GET /mini-app/catalog`**, **`GET /mini-app/tours/{tour_code}`**, **`GET /mini-app/supplier-offers/{supplier_offer_id}`** (as enabled for staging).
- Seat/point preparation: **`GET /mini-app/tours/{tour_code}/preparation`** (query params include **`telegram_user_id`**).
- Create temporary reservation:

  - **`POST /mini-app/tours/{tour_code}/reservations`**

Optional query: **`language_code`**. Body is **`MiniAppCreateReservationRequest`**: **`telegram_user_id`** (**required** **`> 0`**), **`seats_count`**, optional **`boarding_point_id`** (**omit** for some full-bus charter flows per server rules).

Continue through payment entry / mock-complete as allowed for your sandbox:

- **`POST /mini-app/orders/{order_id}/payment-entry`**
- **`POST /mini-app/orders/{order_id}/mock-payment-complete`** (sandbox only if enabled)

Verify in admin or DB that an **`order`** row linked to your tour/supplier scenario exists.

**Refs:** customer-order outbox enqueue is **S1C-4**: [`docs/HANDOFF_S1C4_WIRE_SUPPLIER_NOTIFICATION_AFTER_CUSTOMER_ORDER.md`](HANDOFF_S1C4_WIRE_SUPPLIER_NOTIFICATION_AFTER_CUSTOMER_ORDER.md).

---

### 3) Supplier notification outbox rows appear

After **step 1** (successful channel publish), expect **`supplier_offer_published`** enqueue (**S1C-3** actor surface **`s1c3_after_showcase_channel_publish`**, idempotent key per offer).

After **step 2** (successful **`TemporaryReservationService.create_temporary_reservation`** path), expect **`supplier_order_created`** enqueue (**S1C-4**, actor **`s1c4_after_layer_a_temporary_reservation`**).

Verify with SQL (adapt schema/columns locally), e.g. recent rows keyed by **`supplier_offer_id`** / **`order_id`**, **`dispatch_status`** pending, and **`idempotency_key`** populated.

Enqueue failures are structured-logged (**`s1c3_…`** / **`s1c4_…`**) without rolling back publish/order success.

---

### 4) Supplier receives Telegram DM via manual outbox delivery (S1C-2)

**Goal:** Explicit admin triggers send for **exactly one** **`supplier_notification_outbox.id`**.

**API:**

**`POST /admin/supplier-notification-outbox/{outbox_id}/deliver`**

- **401** invalid/missing token
- **404** unknown **`outbox_id`**
- **409** duplicate / wrong state (**already delivered/skipped**) — defensive idempotency
- **200** with **`SupplierNotificationOutboxDeliveryResultRead`** describing outcome

Observe the supplier Telegram account for the **`message_text`** stored on the row (delivery must not reconstruct from customer PII at send time).

**Refs:** [`docs/HANDOFF_S1C2_SUPPLIER_NOTIFICATION_TELEGRAM_DELIVERY_FROM_OUTBOX.md`](HANDOFF_S1C2_SUPPLIER_NOTIFICATION_TELEGRAM_DELIVERY_FROM_OUTBOX.md).

---

### 5) Operational sales push — preview only (S1D-1)

**Goal:** Read-only eligibility + plaintext preview (**no Telegram send**).

**API:**

**`GET /admin/tours/{tour_id}/operational-sales-push-preview`**

Eligible shapes include **`predeparture`** (default window **≤2** days before departure, config **`PREDEPARTURE_SALES_PUSH_DAYS_BEFORE`**), **`low_availability`** (remaining seats **≤** **`LOW_AVAILABILITY_SEATS_THRESHOLD`**, inclusive floor **1**), or **`combined`**. **`not_eligible`** returns gated diagnostics via **`eligibility_block_codes`** (tour **`OPEN_FOR_SALE`**, future departure, **`sales_deadline`** not passed, **`seats_available` > 0**, **no S1A inventory-vs-order mismatch**, etc.).

For a **physical** demo, rotate staging clock **or** pick a staging tour whose **`departure_date`**/`seats_available` satisfy gates.

**Refs:** [`docs/HANDOFF_S1D1_OPERATIONAL_SALES_PUSH_ELIGIBILITY_AND_PREVIEW.md`](HANDOFF_S1D1_OPERATIONAL_SALES_PUSH_ELIGIBILITY_AND_PREVIEW.md).

---

### 6) Operational sales push — publish to showcase channel (S1D-2)

**Goal:** Admin explicitly publishes **only** eligible system-generated text to **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`**; service **re-checks** S1D-1 at POST time (**no scheduler**).

**API:**

**`POST /admin/tours/{tour_id}/operational-sales-push/publish`**  
Body (**JSON**, extra fields forbidden): **`{ "confirm": true }`**  
If **`confirm`** is **`false`** or omitted → **422** with typed validation errors.

Responses to know for smoke scripts:

| Condition | Typical HTTP |
|-----------|----------------|
| Tour missing | **404** |
| Not eligible (recheck fails) | **400** **`operational_sales_push_not_eligible`** + **`eligibility_block_codes`** |
| Missing Telegram config | **503** |
| Telegram send failure | **502** (after transactional safety rules in code) |

On success JSON includes **`telegram_message_id`**, **`message_plain_sent`**, **`eligibility_recheck`**.

Channel message is plain text (**no HTML parse_mode** helper path for this slice).

**Refs:** [`docs/HANDOFF_S1D2_ADMIN_GATED_OPERATIONAL_SALES_PUSH_CHANNEL_PUBLISH.md`](HANDOFF_S1D2_ADMIN_GATED_OPERATIONAL_SALES_PUSH_CHANNEL_PUBLISH.md).

See also **S1D/S1C** dense checkpoint lines in [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and future-gated decisions in [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md).

---

## Quick smoke curls (adapt host / ids)

Replace placeholders: **`BASE_URL`**, **`ADMIN_API_TOKEN`**, **`offer_id`**, **`tour_id`**, **`outbox_id`**, **`tour_code`**.

```bash
# S1D-1 preview
curl -sS \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  "${BASE_URL}/admin/tours/${tour_id}/operational-sales-push-preview"

# S1D-2 publish (requires confirm:true)
curl -sS \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}' \
  "${BASE_URL}/admin/tours/${tour_id}/operational-sales-push/publish"

# Supplier offer showcase publish (prerequisites in admin workflow)
curl -sS \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -X POST \
  "${BASE_URL}/admin/supplier-offers/${offer_id}/publish"

# Manual supplier outbox delivery (S1C-2)
curl -sS \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  -X POST \
  "${BASE_URL}/admin/supplier-notification-outbox/${outbox_id}/deliver"
```

---

## Explicit non-goals (demo slice)

Aligned with shipped S1C/S1D handoffs:

- No **scheduler/worker loop** replacing manual deliver or manual publish (**S1D-2** is admin-only POST).
- No **supplier notification automatic send from publish/order** (**S1C-2** delivers only what is already queued).
- No **supplier notification** wired from operational sales push (**S1D** is channel-only slice).
- No **passenger manifest** or **customer PII** surfaced in Telegram copy for supplier outbox payloads.
- No **automatic** repeating operational posts without eligibility + admin **`confirm`** (see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** checkpoint **S1D-2**).

---

## Troubleshooting cheatsheet

| Symptom | First checks |
|---------|----------------|
| **`401`** on **`/admin/*`** | `Authorization` bearer or `X-Admin-Token`; whitespace; typo vs `.env`. |
| **`503`** Admin disabled | **`ADMIN_API_TOKEN`** unset server-side; or **S1D-2 config** (**`TELEGRAM_BOT_TOKEN`**, **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`**) absent. |
| **`400`** **`operational_sales_push_not_eligible`** | Re-read **`GET …/operational-sales-push-preview`**; adjust tour dates/seats/state or **`eligibility_block_codes`**. |
| **`409`** on **`/supplier-notification-outbox/.../deliver`** | Row already **`delivered`/`skipped`**; pick another **`outbox_id`**. |
| Mini App rejects user | **`Unknown telegram_user_id`** — bootstrap user via bot open / catalog onboarding first. |

---

## Related slices (read-only pointers)

| Slice | Topic | Handoff |
|-------|-------|---------|
| S1C-2 | Outbox Telegram delivery | `docs/HANDOFF_S1C2_SUPPLIER_NOTIFICATION_TELEGRAM_DELIVERY_FROM_OUTBOX.md` |
| S1C-3 | Outbox enqueue after showcase publish | `docs/HANDOFF_S1C3_WIRE_SUPPLIER_NOTIFICATION_AFTER_CHANNEL_PUBLISH.md` |
| S1C-4 | Outbox enqueue after customer order/reservation | `docs/HANDOFF_S1C4_WIRE_SUPPLIER_NOTIFICATION_AFTER_CUSTOMER_ORDER.md` |
| S1D-1 | Operational preview (read-only) | `docs/HANDOFF_S1D1_OPERATIONAL_SALES_PUSH_ELIGIBILITY_AND_PREVIEW.md` |
| S1D-2 | Operational channel publish | `docs/HANDOFF_S1D2_ADMIN_GATED_OPERATIONAL_SALES_PUSH_CHANNEL_PUBLISH.md` |
