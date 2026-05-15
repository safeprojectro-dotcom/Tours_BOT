# B16D2E — Production / Railway smoke — `prepare_conversion_chain`

**Purpose:** Operator checklist to verify **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`** on a **real** deployed environment (e.g. Railway). **Docs + run log only** unless a blocking bug is filed separately.

**Code reference:** B16D2C route **`app/api/routes/admin.py`** · B16D2B service **`PrepareConversionChainExecutionService`** · B16D2D affordances on **`GET …/review-package`** and related read surfaces.

---

## Pre-smoke reference (from codebase)

### 1. Endpoint and body

| Item | Value |
|------|--------|
| **Method / path** | **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`** |
| **JSON body** | **`idempotency_key`** (string, required, non-blank after trim), **`confirm`** (bool, default `false`), **`dry_run`** (bool, default `false`) |
| **Live rule** | If **`dry_run`** is **`false`**, **`confirm`** must be **`true`** or the API returns **422** before the service runs. |
| **Response** | **`AdminPrepareConversionChainExecutionResultRead`**: e.g. **`overall_status`**, **`dry_run`**, **`attempt_id`** (often `null` for dry_run), **`attempt_status`**, **`steps[]`** (**`step_code`**, **`status`**, …), **`tour_id`**, **`execution_link_id`**, **`message`** (replay hints), **`prepare_conversion_chain_plan_status`**. |

### 2. Admin auth

From **`app/api/admin_auth.py`**:

- **`Authorization: Bearer <ADMIN_API_TOKEN>`**, or  
- **`X-Admin-Token: <ADMIN_API_TOKEN>`**  

If **`ADMIN_API_TOKEN`** is unset on the server, admin routes return **503** (“Admin API is disabled”).

### 3. GET endpoints useful for verification

| Goal | GET path |
|------|-----------|
| Full funnel + **`prepare_conversion_chain_action`** (B16D2D) | **`/admin/supplier-offers/{offer_id}/review-package`** |
| Plan-only chain preview | **`/admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan`** |
| Raw offer row | **`/admin/supplier-offers/{offer_id}`** |
| Publishing console (find row by **`candidate_key`** `supplier_offer:{id}`) | **`/admin/publishing-console`** (optional query `kind=supplier_offer_initial`) |
| OPS summary rows | **`/admin/ops-dashboard`** (**`recent_publications`**, **`conversion_links`**, **`attention_items`**, **`audit_events`**) |

**Audit rows (`admin_guarded_action_attempts` / `steps`):** there is **no dedicated admin GET** for guarded-action tables in **`app/api`**. Treat **`attempt_id`**, **`attempt_status`**, and **`steps[]`** on the **POST response** as the primary API-visible audit. If Railway/DB access is available, operators may **read-only** query those tables for the same **`attempt_id`** — optional, not required by this checklist.

**Note:** **`GET /admin/ops-dashboard` → `audit_events`** aggregates **showcase publish attempts**, **notification outbox failures**, **supplier execution** signals — **not** automatically the same as **`prepare_conversion_chain`** guarded-audit rows.

### 4. Safe candidate `supplier_offer_id`

Prefer an offer that is **disposable for testing** or **staging-only**, not a live revenue-critical tour.

**Good candidates (typical):**

- Lifecycle **`approved`** or **`published`** with packaging **`approved_for_publish`**, and **`prepare_conversion_chain_plan_status`** from plan/review-package in **`partial`** or **`blocked`** only if you **intend** to mutate bridge/catalog/link.
- For **minimal risk**: use an offer that **already** has bridge + catalog + execution link so **`prepare_conversion_chain`** is mostly **idempotent / already_prepared** (smaller blast radius).

**How to pick:** list offers via existing admin listing or known test ID; run **Step 0** reads first.

### 5. Safe vs unsafe states

| Safer | Riskier / avoid without intent |
|--------|--------------------------------|
| Staging; offer with no customer orders on linked tour | Production offer tied to real paid bookings |
| **`dry_run: true`** first | Live **`confirm: true`** when **`plan_status`** is **`ineligible`** (expect **blocked** attempt / failed precheck — still mutates **audit** on live path) |
| New unique **`idempotency_key`** per live experiment | Reusing keys you do not understand (replay semantics) |
| **`partial` / `already_prepared`** when you accept bridge/catalog/link side effects | Offers with **B8 same-offer date conflict** or hard **catalog** blockers unless you are testing **failure** paths only |

**Not in scope for this smoke (do not do):** Telegram **publish** / send / retry; **`POST …/publish`**; Layer A booking/payment/reservation tests; Mini App / B11 changes.

---

## PowerShell snippets (placeholders only)

Set variables **without** committing real secrets:

```powershell
$BASE_URL = "https://your-railway-host.example"   # origin only, no trailing slash
$ADMIN_API_TOKEN = "<paste-from-secrets-manager>"
$OFFER_ID = 0                                     # replace with integer
$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$DRY_KEY = "b16d2e-smoke-dry-run-$ts"
$LIVE_KEY = "b16d2e-smoke-live-$ts"
$headers = @{ Authorization = "Bearer $ADMIN_API_TOKEN" }   # or X-Admin-Token
```

**Step 0 — Health (optional):**

```powershell
Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
```

**Read-only — review package:**

```powershell
Invoke-RestMethod -Uri "$BASE_URL/admin/supplier-offers/$OFFER_ID/review-package" -Headers $headers -Method Get
```

**Read-only — plan:**

```powershell
Invoke-RestMethod -Uri "$BASE_URL/admin/supplier-offers/$OFFER_ID/prepare-conversion-chain/plan" -Headers $headers -Method Get
```

**Dry run:**

```powershell
$bodyDry = @{ idempotency_key = $DRY_KEY; dry_run = $true; confirm = $false } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE_URL/admin/supplier-offers/$OFFER_ID/prepare-conversion-chain" -Headers $headers -Method Post -Body $bodyDry -ContentType "application/json"
```

**Live (only after dry_run + plan review):**

```powershell
$bodyLive = @{ idempotency_key = $LIVE_KEY; dry_run = $false; confirm = $true } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE_URL/admin/supplier-offers/$OFFER_ID/prepare-conversion-chain" -Headers $headers -Method Post -Body $bodyLive -ContentType "application/json"
```

**Idempotent replay (same key as live):**

```powershell
Invoke-RestMethod -Uri "$BASE_URL/admin/supplier-offers/$OFFER_ID/prepare-conversion-chain" -Headers $headers -Method Post -Body $bodyLive -ContentType "application/json"
```

**curl equivalents:** same paths and JSON body; header **`Authorization: Bearer $ADMIN_API_TOKEN`**.

---

## Smoke sequence (operator checklist)

### Step 1 — Read-only precheck

- [ ] **`GET …/review-package`** — record **`prepare_conversion_chain_plan_status`**, **`prepare_conversion_chain_recommended_action`**, **`prepare_conversion_chain_blockers_count`**, **`prepare_conversion_chain_action`** (`enabled`, `path`, `disabled_reason`).
- [ ] **`GET …/prepare-conversion-chain/plan`** — confirm **`steps[]`**, **`prepare_conversion_chain_eligible`**, **`plan_blockers`**, **`will_not_do`**.
- [ ] Decide whether live smoke is acceptable for this offer and environment.

### Step 2 — `dry_run`

- [ ] **POST** with **`dry_run: true`**, **`confirm: false`**, unique **`idempotency_key`**.
- [ ] Expect **`overall_status`** **`dry_run_preview`** or **`blocked`** (precheck-only), **`attempt_id`** **`null`**, **`steps`** consistent with service (no persisted attempt for dry_run in unit contract).

### Step 3 — Live execution

- [ ] **POST** with **`dry_run: false`**, **`confirm: true`**, **new** **`idempotency_key`**.
- [ ] Expect **`overall_status`** **`succeeded`**, **`partial_success`**, **`failed`**, or **`blocked`** per plan; inspect **`steps[]`** for **`ensure_tour_bridge`**, **`activate_tour_for_catalog`**, **`ensure_active_execution_link`**.
- [ ] Record **`attempt_id`** if present.

### Step 4 — Idempotent replay

- [ ] Repeat live **POST** with **same** **`idempotency_key`** as Step 3.
- [ ] Expect same **`attempt_id`**, **`message`** mentioning **replay**, no extra **`Tour` / link** side effects (counts unchanged if checked).

### Step 5 — Post-read verification

- [ ] **`GET …/plan`** and **`…/review-package`** — **`already_prepared`** or aligned **partial**; affordance **`enabled`** / **`disabled_reason`** updated if applicable.
- [ ] **`active_tour_bridge`**, **`linked_tour_catalog`**, **`execution_links_review`** on review-package — match expectations.
- [ ] Optional: publishing console / ops-dashboard row for same **`offer_id`**.
- [ ] Confirm **no** showcase publish was triggered by this flow (no new publish attempts required for **`prepare_conversion_chain`**).
- [ ] Confirm **no** new orders/payments/reservations were needed for this test (Layer A unchanged by this API).

---

## Run log

| Field | Value |
|--------|--------|
| **Environment** | Railway production |
| **Date/time (UTC)** | 2026-05-15 08:16–08:25 UTC |
| **Commit tested** | `fd4e25d79ee7338b15053b51886aa9157c43e6c6` |
| **offer_id** | `12` |
| **offer title** | `Excursie Timisoara Oradea` |
| **dry_run idempotency_key** | `b16d2e-smoke-dry-run-20260515112224` |
| **live idempotency_key** | `b16d2e-smoke-live-20260515112326` |
| **Step 1 notes** | Review package and plan were checked. `plan_status=already_prepared`, `blockers_count=0`, `prepare_conversion_chain_action.enabled=true`. Active bridge existed: `bridge_id=3`; linked tour existed: `tour_id=6`, `tour_code=B10-SO12-04fb1f`, `tour_status=open_for_sale`, `catalog_listed_for_mini_app=true`; active execution link existed: `execution_link_id=5`. |
| **Step 2 result** | Dry run passed. `overall_status=dry_run_preview`, `attempt_id=null`, message: `Dry run: no audit rows or business mutations.` All steps were `skipped` with reason `already_satisfied`. |
| **Step 3 result** | Live execution passed. `overall_status=succeeded`, `attempt_status=succeeded`, `attempt_id=1`, `tour_id=6`, `execution_link_id=5`. Message: `All preparation steps already satisfied; no business mutations performed.` All steps were `skipped` with reason `already_satisfied`. |
| **Step 4 replay result** | Replay passed with the same live idempotency key. Response returned the same `attempt_id=1`; message: `Idempotent replay of a succeeded prepare_conversion_chain attempt.` |
| **Step 5 notes** | Post-read review package confirmed: active bridge `true`, `bridge_id=3`, `tour_id=6`, `tour_code=B10-SO12-04fb1f`, `tour_status=open_for_sale`, `catalog_listed_for_mini_app=true`, active execution link `true`, `execution_link_id=5`, `plan_status=already_prepared`, `blockers_count=0`, `prepare_conversion_chain_action.enabled=true`. |
| **Telegram I/O** | None. No Telegram publish, send, retry, or showcase channel post was executed by this smoke. |
| **Layer A mutations** | None. No order, payment, reservation, or seat mutation was executed by this smoke. |
| **Issues / warnings** | Offer `11` was checked first as a blocked-case precheck and was not used for live execution because the plan was blocked by `Only future-departure tours can be linked.` A transient PowerShell keep-alive connection error occurred during first replay attempt; retry with `-DisableKeepAlive` succeeded and confirmed idempotent replay. |

**Final status:** passed with note.

---

## If something fails

Stop; open an issue with: exact command, HTTP status + body (redacted), expected vs actual, suspected module (**`PrepareConversionChainExecutionService`** vs route), whether data was mutated, whether DB cleanup is needed. **Do not change code** in-repo without explicit approval.
