# Supplier execution — controlled trigger design (Y45)

**Phase:** Y45 — design only (documentation). **No** runtime code, migrations, new API handlers, tests, or messaging in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38)  
- [`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md) (Y39)  
- [`docs/SUPPLIER_EXECUTION_FLOW.md`](SUPPLIER_EXECUTION_FLOW.md) (Y40)  
- [`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`](SUPPLIER_EXECUTION_DATA_CONTRACT.md) (Y41)  
- [`docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md`](SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md) (Y42)  
- Y43: persistence for `supplier_execution_requests` / `supplier_execution_attempts` exists.  
- Y44: admin read-only visibility exists.

**Purpose:** Define the **first** allowed way to **create** a supplier **execution request** row — a **trigger** that is **explicit, authenticated, validatable, and auditable** — while **stopping before** any supplier-impacting **runtime** (Y40 stage 4+) such as messaging or partner calls. This doc does **not** implement anything.

---

## 0. Why “trigger” is separated from “execution”

| Concept | Meaning in this project |
|--------|-------------------------|
| **Trigger (this doc)** | A **dedicated, controlled start** that may **only** create/update **execution request** audit state (Y41) after checks — **persistence and validation boundary**, not outbound work. |
| **Execution (runtime, future)** | **Later** code paths that perform **attempts** (Y41 attempt rows, channels, transport), retries, and supplier-facing side effects. That is **Y40 stages 4–6**; it **must not** be implied or started by the same handler contract as a **Y45** trigger unless a **separate** ticket explicitly adds it. |

**Separation is mandatory** so that: (1) Y38 is preserved — `operator_workflow_intent` and `POST .../operator-decision` never **silently** start supplier work; (2) Y39 entry points stay **one explicit family per invocation**; (3) Y40 does not collapse “record a run” with “ship a message”; (4) idempotency and audit attach to **one** durable request row before any irreversible **external** effect.

---

## 1. First (and only) allowed trigger in this design slice: **admin explicit**

| Field | Value |
|-------|--------|
| **Y39 family** | **Admin / central explicit action** — a **dedicated** operation whose **purpose** is to register a supplier execution run (Y39 §1). **Not** `POST /admin/custom-requests/{id}/operator-decision`. |
| **Y39 surface type (illustrative)** | **Explicit admin API** (future implementation must name the route, method, and body). |
| **Entry point value (`source_entry_point`)** | Maps to the implemented enum **`admin_explicit`** (Y41 logical / Y43 naming), so every row is traceable. |
| **Who may invoke** | Only callers that satisfy **§4** (central **ADMIN_API_TOKEN** + policy below). **Operators** and **customers** are **out of scope** for this **first** trigger; a **separate** design ticket is required for `operator_do_action` or `scheduled_job` starts. |

**Not in scope for Y45:** Telegram callbacks, background jobs, webhooks, Mini App, operator “do” buttons — even if they later mirror the same **logical** checks.

---

## 2. What the trigger **does** (allowed effects)

When a future implementation follows this design, a successful invocation may **only**:

1. **Authenticate** the caller per **§4.1** (fail-closed if not).
2. **Validate** the payload: required fields, types, and business preconditions in **§4** (fail-closed with a **block** outcome or HTTP error, per implementation ticket).
3. **Prove** the **source entity** exists and is the correct **type** (e.g. `custom_marketplace_request` + id) — **read-only** check against domain tables. **No** mutation of that entity for “execution convenience.”
4. **Create** (or **idempotently resolve**) exactly **one** `supplier_execution_request` row per Y41 with:
   - `source_entry_point` = `admin_explicit`
   - `source_entity_type`, `source_entity_id`
   - `idempotency_key` (call-site supplied or policy-defined; must meet **§4.3**)
   - `operator_workflow_intent_snapshot` = **copy** of current Layer C intent **at create time** (optional if null; **never** a live join)
   - `requested_by_user_id` = **actor** as resolved from admin policy (or null only if a future policy explicitly allows system-only; **Y45** assumes a **resolvable** human/service account id when required)
   - `status` = **`pending`** or **`validated`** per **§5** (not terminal failure states for “happy” path)
5. **Persist audit-facing fields** as needed: timestamps, and on validation failure with row creation: `validation_error` / **blocked** semantics per Y41 and **§4**.

**Explicitly not done by this trigger:** creating **attempt** rows (except a possible **`internal` / `none` channel** no-op in a **separate** ticket is **out of Y45** — default is **no attempt rows** from Y45), invoking workers, enqueuing messages, or advancing to **attempted** / **succeeded** / **failed** except as defined by **status** + validation rules in a later runtime slice.

---

## 3. What the trigger **must not** do

The following are **forbidden** for the Y45 trigger (and for any “first” implementation claiming Y45 compliance):

| Forbidden | Rationale |
|-----------|-----------|
| **Send** supplier or customer **messages** (Telegram, email, push, etc.) | Outbound comms = execution runtime / notifications — **not** Y45. |
| **Call supplier or partner HTTP/APIs** | External I/O = execution — **not** Y45. |
| **Create or modify RFQ** (`CustomMarketplaceRequest` as **new** row, or automation beyond existing product rules) | Y38 / Layer C boundary. |
| **Create or mutate bookings, orders, payments, tours** | Layer A / commercial execution — out of scope. |
| **Change Mini App** routes, DTOs, or customer visibility | Y38 / Y39. |
| **Create, replace, or close** `supplier_offer_execution_links` | Execution **link** feature — not Y45. |
| **Modify identity bridge** or session / `telegram_user_id` binding | Out of scope. |
| **Notify customers** (or suppliers) of any kind | Triggers are **not** a notification system. |
| **Treat `operator_workflow_intent` as a live trigger** | Snapshot only; Y38, Y41 §6. |
| **Hide** the start in ORM/DB **triggers** on `custom_marketplace_requests` or intent columns | Y39 / Y42 — **declared** entry only. |
| **Assume** that “intent = need_supplier_offer” **implies** this trigger ran | Gating and explicit admin action are separate. |

**Y45 is “DB record + validation + audit trail”** — not “supplier execution runtime.”

---

## 4. Required checks (fail-closed)

| # | Check | On failure |
|---|--------|------------|
| **4.1** | **ADMIN_API_TOKEN** — same **shared secret** / header contract as other **central admin** mutators (e.g. `Authorization: Bearer` or `X-Admin-Token`). No token or wrong token → **no row**; HTTP **401** (or **503** if admin disabled in config, consistent with existing admin routes). | Deny. |
| **4.2** | **Source entity exists** — `source_entity_type` + `source_entity_id` must resolve to an **existing** row. Deleted or unknown → **block**; do not create an ambiguous run (Y42 §4). | `blocked` or reject before insert — **no** “phantom” execution for missing entities. |
| **4.3** | **Idempotency key present and valid** — non-blank, within length/format rules (align Y43 / DB constraints). Missing or invalid → **block**; no silent default that weakens deduplication. | `blocked` or 4xx. |
| **4.4** | **No duplicate active / conflicting idempotency** — same `idempotency_key` must not create **second** **competing** row (DB **unique** constraint on key as in Y43). Replays: **idempotent** — return the **existing** row and **do not** double-book side effects (there are **none** in Y45). | If key exists: **200** with same body as first create, or **409** with clear policy — **must** be documented in the implementation ticket. |
| **4.5** | **“Not already active” (policy-level)** — product rule examples: (a) no **new** run if one already exists for the same **source entity** with `status` in `pending` / `validated` and **same** product-defined **intent to dedupe**; or (b) only **idempotency key** enforces deduplication. **Y45** requires **at minimum** 4.4; stricter “one active per entity” rules are **optional** but if added must be **documented and tested**. | Fail-closed: **block** with explicit **reason** in `validation_error` or equivalent. |
| **4.6** | **Permission (Y42)** — trigger is **not** `operator-decision`. Caller must be **admin-grade**; **not** “any authenticated user.” | Deny. |
| **4.7** | **No auto-refresh of intent** — validate against **read** of current intent for snapshot **only**; do not **write** Layer C as part of this trigger. | N/A. |

**Default:** **When in doubt, deny** (Y42 §4, Y40 §3).

---

## 5. Output of the trigger (observable outcome)

| Outcome | Description |
|---------|----------------|
| **Database** | At most **one** new `supplier_execution_request` per successful **first** `idempotency_key` (subject to uniqueness). |
| **Status** | **`validated`** — all checks in **§4** that this slice implements have **passed** and the request is **ready** for a **future** attempt stage (Y40 §4) **in a different ticket**. **`pending`** — allowed only if the implementation ticket **explicitly** defines a **narrow** “created before full validation” path (e.g. deferred checks); **default recommendation** for the **first** implementation: **use `validated` on success** to avoid indeterminate `pending` without a follow-up job (which Y45 does **not** add). On validation failure with explicit persist: **`blocked`** + `validation_error` / audit text per Y41. |
| **Audit trail** | `created_at` / `updated_at`, `requested_by_user_id`, `source_entry_point`, `source_entity_*`, `idempotency_key`, optional `operator_workflow_intent_snapshot`, and failure text when blocked. **No** `attempt` rows **required** from Y45. |

**HTTP / API response shape** is **TBD** in the implementation ticket; it must **not** claim supplier delivery.

---

## 6. Relationship to Y38–Y42 and Y39 entry point

| Doc | How Y45 uses it |
|-----|-----------------|
| **Y38** | Intent is **not** a trigger; Y45 trigger is a **separate** admin **action**. |
| **Y39** | First trigger = **`admin_explicit`** **family** + **explicit API** **surface**; not operator-decision, not a hidden job. |
| **Y40** | Y45 covers **stages 1–3** only (entry → validation → **execution request** record). **Not** stage 4 (attempt) in Y45. |
| **Y41** | All persisted fields and statuses must stay consistent with the **Y41** contract; snapshot rules apply. |
| **Y42** | Permissions, audit list, and fail-closed table **must** be satisfied; intent ≠ execution permission. |

---

## 7. Hard constraints (Y45 acceptance)

Y45 **does not** authorize:

- **Execution runtime** (workers that send, poll, or complete attempts — **separate** ticket)  
- **Supplier messaging** or **customer notifications**  
- **RFQ** / booking / order / payment **logic** in the trigger path  
- **Mini App** changes  
- **Execution links** or **identity bridge**  
- Nonspecific **“side effects”** beyond **allowed DB writes** in **§2**

**Acceptance of Y45** = this file is the agreed **first** trigger spec; **implementation** = a **future** ticket that cites Y38–Y45 and stays within **§2–§5**.

---

## 8. Next step (product/engineering)

1. **Accept** this document as the **Y45** baseline for the **first** **create-request** **trigger** (admin explicit only).  
2. **Next implementation ticket** (not Y45): add the **concrete** **POST** (or approved method) for admin, OpenAPI, service layer, tests, and **exact** idempotency + “active” rules — still **no** supplier messaging, **no** attempt creation unless a **separate** sub-slice is explicitly approved.  
3. **Later** tickets: `operator_do_action` and/or `scheduled_job` **triggers** require **separate** design addenda (not implied by Y45).  
4. Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when Y45 is **accepted** and when a **Y45-aligned** **implementation** is merged.

---

## Summary

| Topic | Y45 stance |
|--------|------------|
| **First trigger** | **Admin explicit** only (`source_entry_point` = `admin_explicit`). |
| **Does** | Create `supplier_execution_request`, validate, audit; **no** supplier contact. |
| **Does not** | Messages, RFQ/orders/payments, Mini App, execution links, bridge, notifications, execution runtime. |
| **Checks** | ADMIN_API_TOKEN, entity exists, idempotency, deduplication, fail-closed. |
| **Output** | DB row, `pending` or **`validated` (preferred)**; audit; optional **`blocked`**. |
| **Separation** | Trigger ≠ Y40 attempt stage; intent ≠ trigger (Y38). |
