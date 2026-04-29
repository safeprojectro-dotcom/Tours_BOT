# Production / staging E2E smoke — supplier offer → Mini App catalog

**Purpose:** Operator checklist to verify the **real** admin + Mini App path for one supplier offer on **staging or production**, without treating unit tests as a substitute for infra smoke. **Docs only** — no runtime behavior change.

**Anchor milestone:** Core conversion chain is **MVP-closed** in code/tests (**[`BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md`](BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md)**); this document is the **human + API** smoke layer (**B13-adjacent**).

**Related:** **[`HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md`](HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md)** · **[`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** · unit proof **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`**.

---

## Scope and non-goals

| In scope | Out of scope |
|----------|----------------|
| Read/admin GET smoke, explicit POST gates in order | New features, migrations, AI wiring |
| Showcase **preview** / **publish** only when env allows | Changing booking/payment/order/reservation **logic** |
| **`conversion_closure`** as pass/fail helper | Mini App UI edits, Telegram HTML template edits |
| Confirm Layer A **unchanged by this checklist** (no booking mutations required) | Media download/storage pipeline (**B7.3**) |

**Hard rule:** **`POST /admin/supplier-offers/{offer_id}/execution-link`** requires **`lifecycle_status === published`** (**[`supplier_offer_execution_link_service`](../app/services/supplier_offer_execution_link_service.py)**). Plan **`publish`** before **`execution-link`**.

---

## Modes

### Mode A — Dry-run / API checklist (no live secrets)

Use **`BASE_URL`** as your deployed API origin (no path prefix — routers mount at **`/admin`**, **`/mini-app`**).

Set **`ADMIN_TOKEN`** from **`ADMIN_API_TOKEN`** (same secret the API expects). Auth: **`Authorization: Bearer <token>`** or **`X-Admin-Token: <token>`** (**[`app/api/admin_auth.py`](../app/api/admin_auth.py)**).

Execute steps below with **`curl`** / HTTP client; record status codes and **JSON** excerpts. Mark **`NOT RUN`** where credentials or data are unavailable **— do not invent outcomes.**

### Mode B — Live staging/production smoke

Same steps; paste **observed** HTTP results into the **Run log** section (or an ops ticket). Redact tokens.

---

## Preconditions (environment)

| Variable / config | Role |
|-------------------|------|
| **`ADMIN_API_TOKEN`** | Required for all **`/admin/*`** calls **;** without it admin returns **503** (“Admin API is disabled”). |
| **`telegram_mini_app_url`** | Used for **`conversion_closure.bot_deeplink_routes_to_tour`** (**B11** URL resolution). Empty base URL yields **`bot_ok` false**. |
| Showcase channel (**`telegram_offer_showcase_channel_id`**, bot token, etc.) | **`POST .../publish`** fails with **503** (**`SupplierOfferPublicationConfigError`**) if publication is not configured — preview/read paths still work. |

---

## Canonical gate order (explicit)

Align with **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`** and **[`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)**:

1. Packaging **`approved_for_publish`** (if not already).
2. **`moderation/approve`** → lifecycle **`approved`** (not yet channel-published).
3. **`POST .../tour-bridge`** → **`tour_id`** (idempotent replay OK).
4. **`POST /admin/tours/{tour_id}/activate-for-catalog`** → **`status: open_for_sale`**.
5. **`GET .../showcase-preview`** (recommended before publish).
6. **`POST .../publish`** → lifecycle **`published`** (**requires** moderation approved **+** Telegram showcase config **when** exercising real publish).
7. **`POST .../execution-link`** with **`{"tour_id": <id>}`** — **only after** published.

Central catalog can list the Tour **before** step 7 (**OPEN_FOR_SALE** **does not** depend on execution link). Landing **exact Tour** and **`supoffer_<id>`** routing **require** active execution link **+** catalog visibility rules (**audit / tests**).

---

## Checklist (operator path)

Use **`OFFER_ID`** = integer supplier offer id **;** **`TOUR_ID`** from bridge response **;** **`TOUR_CODE`** from **`activate-for-catalog`** or **`GET /admin/supplier-offers/{OFFER_ID}`**.

### 1. Supplier offer exists with required fields

**GET** **`/admin/supplier-offers/{OFFER_ID}`**

- **200** — inspect **`packaging_status`**, **`lifecycle_status`**, dates, **`sales_mode`**, pricing, etc.
- Map **`422`** / validation messages from bridge later to missing mandatory fields (**review-package** **`warnings`** / **`recommended_next_actions`** help).

### 2. Admin review package readable

**GET** **`/admin/supplier-offers/{OFFER_ID}/review-package`**

- **200** — confirm aggregates present: **`offer`**, **`showcase_preview`**, **`bridge_readiness`**, **`active_tour_bridge`**, **`linked_tour_catalog`**, **`execution_links_review`**, **`mini_app_conversion_preview`**, **`conversion_closure`**, **`warnings`**, **`recommended_next_actions`**.
- **404** — offer id invalid.

### 3. Packaging **`approved_for_publish`**

If **`offer.packaging_status`** is not approved:

**POST** **`/admin/supplier-offers/{OFFER_ID}/packaging/approve`**  
Body (minimal): **`{"accept_warnings": false}`** (add **`reviewed_by`** if you track reviewer).

- **200** — **`packaging_status`** reflects approval **;** **400** — state error (wrong prior state).

### 4. Moderation approved

If **`lifecycle_status`** is not **`approved`** / **`published`**:

**POST** **`/admin/supplier-offers/{OFFER_ID}/moderation/approve`**

- **200** — expect **`approved`** when starting from **`ready_for_moderation`** (exact enum strings in **`AdminSupplierOfferRead`**).

### 5. Tour bridge creates/links Tour

**POST** **`/admin/supplier-offers/{OFFER_ID}/tour-bridge`**  
Body: **`{}`** or **`{"created_by": "...", "notes": "..."}`** (optional link to existing tour per schema).

- **200** — capture **`tour_id`**, **`bridge_status`** **;** idempotent replay returns same bridge.
- **422** — **`packaging_not_approved`** / **`lifecycle_rejected`** / missing fields (**detail.errors**).

**GET** **`/admin/supplier-offers/{OFFER_ID}/tour-bridge`** — optional confirmation.

### 6. Tour activated for Mini App catalog

**POST** **`/admin/tours/{TOUR_ID}/activate-for-catalog`**  
Body: **`{}`** or **`{"activated_by": "...", "notes": "..."}`**.

- **200** — **`status`** **`open_for_sale`** **;** capture **`code`**.
- **400 / 422** — activation validation (**linked tour fields**, **B8.3** conflict, etc.).

### 7. Showcase preview / publish (**if** channel config available)

**GET** **`/admin/supplier-offers/{OFFER_ID}/showcase-preview`**

- Inspect **`caption_html`**, **`can_publish_now`**, **`warnings`** (**[`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)**).

**POST** **`/admin/supplier-offers/{OFFER_ID}/publish`**

- **200** — **`telegram_message_id`** set **;** offer lifecycle moves toward **`published`** per moderation service.
- **503** — publication config missing (**mark NOT RUN** for real channel smoke **;** continue only if another path sets **`published`** for your environment **—** normally fix config **or** defer publish smoke).

### 8. Execution link created

**POST** **`/admin/supplier-offers/{OFFER_ID}/execution-link`**  
Body: **`{"tour_id": TOUR_ID}`** (optional **`link_note`**).

- **200** — active link created **;** **`GET /admin/supplier-offers/{OFFER_ID}/execution-links`** lists it.
- **400** — “Only published offers…” if step 7 did not reach **`published`**.

### 9. Mini App catalog contains Tour

**GET** **`/mini-app/catalog`** (optional filters: **`language_code`**, dates, **`limit`**, **`offset`**)

- Confirm an item whose **`code`** equals **`TOUR_CODE`** (customer visibility window must include “now” — same rule as **`central_catalog_contains_tour`**).

### 10. Supplier-offer landing resolves linked Tour

**GET** **`/mini-app/supplier-offers/{OFFER_ID}`**

- **200** — **`has_execution_link`** **true**, **`linked_tour_id`** / **`linked_tour_code`** match **`TOUR_ID`** / **`TOUR_CODE`** (**published**-offer landing **;** **404** if not found / not exposed).

### 11. Bot deep link **`supoffer_<id>`** routes to exact Tour

**API verification (no Telegram UI):** **`GET /admin/supplier-offers/{OFFER_ID}/review-package`** → **`conversion_closure.bot_deeplink_routes_to_tour`** **`true`** when **`telegram_mini_app_url`** is set and gates satisfied.

**Manual Telegram check:** `/start supoffer_<OFFER_ID>` should open Mini App **`/tours/{TOUR_CODE}`** per **[`supplier_offer_bot_start_routing`](../app/services/supplier_offer_bot_start_routing.py)** (**execution link + `OPEN_FOR_SALE` + visibility**).

### 12. Booking/payment remains Layer A (**unchanged**)

This smoke **does not** modify reservation/order/payment code paths.

**Verification:** Option A — **do not** place a test booking during infra smoke **;** confirm no Layer A code changes in deploy. Option B — **only** on **staging** with disposable data: follow existing **[`TESTING_STRATEGY.md`](TESTING_STRATEGY.md)** manual Mini App booking checks **;** stop if anything touches production money flows without approval.

---

## Closure aggregate (**`conversion_closure`**)

After steps complete, **`GET /admin/supplier-offers/{OFFER_ID}/review-package`** → **`conversion_closure`** should satisfy:

| Field | Meaning |
|-------|--------|
| **`has_tour_bridge`** | Active bridge exists |
| **`has_catalog_visible_tour`** | Linked **`Tour.status`** **`OPEN_FOR_SALE`** |
| **`has_active_execution_link`** | Active **`supplier_offer_execution_links`** row |
| **`supplier_offer_landing_routes_to_tour`** | Mini App landing sees linked tour (**published** context) |
| **`bot_deeplink_routes_to_tour`** | B11 URL resolvable (**needs** **`telegram_mini_app_url`**) |
| **`central_catalog_contains_tour`** | Catalog visibility window **now** |
| **`next_missing_step`** | **`null`** when all above **true** |

If **`next_missing_step`** is non-null, use it as the single suggested gate (**does not** auto-run actions).

---

## Example **`curl`** snippets (**Mode A** placeholders)

Replace **`BASE`**, **`TOKEN`**, **`OFFER_ID`**.

```bash
# Auth header (pick one style)
HDR="-H Authorization: Bearer TOKEN"

curl -sS "${HDR}" "BASE/admin/supplier-offers/OFFER_ID/review-package" | jq .

curl -sS -X POST "${HDR}" "BASE/admin/supplier-offers/OFFER_ID/tour-bridge" \
  -H "Content-Type: application/json" -d "{}"

curl -sS -X POST "${HDR}" "BASE/admin/tours/TOUR_ID/activate-for-catalog" \
  -H "Content-Type: application/json" -d "{}"

curl -sS "BASE/mini-app/catalog?limit=50" | jq .

curl -sS "BASE/mini-app/supplier-offers/OFFER_ID" | jq .
```

---

## Run log template (**Mode B**)

| Step | Result | Notes |
|------|--------|-------|
| Env (**BASE_URL**, admin enabled, mini_app URL) | OK / NOT RUN | |
| 1–4 Offer + gates | | |
| 5–6 Bridge + activate | | TOUR_ID / TOUR_CODE |
| 7 Showcase | OK / NOT RUN (503?) | |
| 8 Execution link | | |
| 9 Catalog contains code | | |
| 10 Landing | | |
| 11 Bot / **`conversion_closure.bot_*`** | OK / NOT RUN | |
| 12 Layer A | N/A / spot-check | |

---

## Document control

| Field | Value |
|-------|--------|
| **Created** | 2026-04-29 |
| **Kind** | Production/staging E2E smoke checklist (**operator**) |
