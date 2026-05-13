# B16D — OPS actions guarded automation (design only)

**Status:** Design record — **no** implementation in this slice.  
**Builds on:** [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md) (read-only console + affordances); [`docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`](B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md) (read-only ops dashboard).  
**Handoff:** [`docs/HANDOFF_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN_TO_NEXT_STEP.md).  
**Prompt archive:** [`docs/CURSOR_PROMPT_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](CURSOR_PROMPT_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md).

**Principle:** Do **not** jump to auto-publish. The system may compute the **next** operator action and expose **one-click guarded** actions; **internal** preparation may be **chained** where safe; **public** channel publish stays **explicit** and **confirmation-gated**; **every** action and sub-step must be **audited**.

---

## 1. Problem

Operator burden is real: for each approved supplier-offer path toward showcase publication, the team today must stitch together many **correct but manual** steps—generate/approve package, moderation, tour bridge, catalog activation, execution link, media clearance, then Telegram publish. Repeating this via **PowerShell**, raw **HTTP**, or tribal knowledge is **not** a sustainable control surface for a growing catalog.

The **read-only** publishing console and **ops dashboard** (B15B–F, B16 Step 1) already improve **visibility** and **blocking reasons**; the next increment is **guided** and eventually **executed** actions **without** collapsing safety boundaries. At the same time, **public** publish and anything touching **payments** or **orders** remains **high risk** and must stay **separate**, **visible**, and **auditable**.

---

## 2. Automation levels

### Level 0 — read-only visibility (**done**)

- Publishing console (`GET /admin/publishing-console`).
- Ops dashboard (`GET /admin/ops-dashboard`).
- Readiness, blockers, read-only **`actions[]`** affordances (metadata only).
- **No** mutation, **no** Telegram side effects from these routes.

### Level 1 — assisted one-click actions (**future**)

- Single **explicit** action per request.
- Delegates to an **existing** service or narrowly scoped new service.
- **Confirmation** scales with **danger** classification (see §7).
- **Audit** required for every invocation.

**Examples:** approve packaging; approve cover; create tour bridge; activate tour for catalog; create execution link; publish showcase **with** strong confirmation (still Level 1 if a single POST).

### Level 2 — guarded internal chain (**future**)

- **`prepare_conversion_chain`** — may run **multiple** internal, **non-public** steps in one operator gesture.
- Must **stop before** Telegram **publish** / **send** (no hidden public side effect).
- **Strict preconditions** (§4); **audited** **sub-steps** (§6).
- Final HTTP response may be **`partial_success`** with a clear **next** action (§5).

### Level 3 — public publish with confirmation (**future**)

- **`publish_showcase_channel`** (or equivalent) — **external / public** side effect.
- **Always** separate from the internal **prepare** chain.
- **Explicit** confirmation; **`public_dangerous`** (§7).
- **No** “publish slipped in” at the end of Level 2.

### Level 4 — scheduler / auto-publish (**future only**)

- **Not** approved in this design.
- Requires a **separate** gate (e.g. **B15G**) with its own threat model and approvals.

---

## 3. Proposed future action: `prepare_conversion_chain`

| Field | Value |
|--------|--------|
| **Code** | `prepare_conversion_chain` |
| **Purpose** | For an **approved** supplier offer, perform **internal** preparation so the offer reaches **`ready_to_publish`** (operator-facing state / readiness signal), **without** any **Telegram** channel publish or send. |

**Intended sub-steps (in order; exact service mapping is implementation detail):**

1. **Create or link tour bridge** if missing (offer → `Tour` per existing B9/B10 rules).
2. **Activate linked tour for catalog** if **eligible** (e.g. `open_for_sale` / B10.2 semantics — only when prechecks pass).
3. **Create active execution link** if missing (B15C-aligned booking link before public publish when policy requires it).

**Explicitly excluded** from this action (and must **never** be bundled silently):

- Telegram **publish** or **send** / retry loops.
- **Payment** state changes or capture.
- **Order** create/cancel/refund or hold manipulation.
- **Supplier** outbound messaging.
- **Auto-retry** of failed sub-steps without a **new** explicit operator or system policy (future scheduler is Level 4).

After **successful** completion of all sub-steps (or idempotent replay when already satisfied), the surfaced **next** product state for operators should be **`ready_to_publish`**, with **`publish_showcase_channel`** as a **distinct** next action (Level 3).

---

## 4. Preconditions

All of the following are **design requirements** before **B16D2** may execute **`prepare_conversion_chain`**. Enforcement may reuse existing review-package / publishing-console gates; gaps become implementation tasks.

1. **Supplier offer lifecycle** approved for the conversion path (moderation + business rules as today).
2. **Packaging** **`approved_for_publish`** (or equivalent gate) satisfied.
3. **Cover / media:** **`approved_for_card`** **or** an **explicit** operator/text-only path documented as cleared for publish **without** showcase photo (no silent downgrade—must match product rules).
4. **No blocking quality warnings** that **policy** treats as publish blockers (align with console / review-package warnings).
5. **Source fields** sufficient to **materialize** tour data (departure, pricing, capacity model, boarding where required by Layer A / B14 family rules).
6. **No active conflicting bridge/link** (e.g. duplicate bridges, wrong tour linkage, or policy-defined conflicts).
7. **Linked tour** has **valid** departure, price, capacity, and **boarding** data per activation prechecks.
8. **Catalog activation precheck** passes (B10.1/B10.2 style rules).
9. **Execution link precheck** passes (policy for “active link before publish” path).
10. **Operator/admin identity** known and attributable on the request (existing admin auth patterns).
11. **`Idempotency-Key`** (or server-issued equivalent) **available** for the invocation (§10).
12. **Confirmation** accepted when the action is classified **`conversion_enabling`** (§7) — UI + server-side acknowledgment, not checkbox theater.

If any precondition fails, the action must **not** start—or must **fail fast** on the first sub-step with a **clear** **`disabled_reason`** / **`error_code`** for the dashboard.

---

## 5. Failure and partial success policy

The chain **may partially succeed**. Example: **bridge** created → **catalog activation** failed → **execution link** never attempted.

**Rules:**

1. **Every sub-step** is **audited** independently (start, end, status, error) — §6.
2. The **overall** result may be **`partial_success`** with a **machine-readable** list of **completed** vs **failed** vs **skipped** steps and the **remaining** **`next_action_code`** for the UI.
3. The **dashboard** must show the **true** next step—not assume “all green” after a partial run.
4. **Retries** are **explicit** (new invocation with a **new** or policy-defined idempotency policy)—**no** silent background retry.
5. **Idempotent replay** with the **same** key must **not** duplicate bridges, tours, or execution links — detect existing artifacts and **skip** or **return** stable references (§10).
6. **No automatic rollback** in this design; compensating transactions are **out of scope** unless a **later** slice explicitly designs them (operators remediate forward using existing admin tools).
7. **No hidden publish** after partial success—or ever—from this chain.

---

## 6. Audit model

**Requirement:** For **each** top-level action **and** each **sub-step**:

| Field | Description (**design**) |
|--------|---------------------------|
| `action_code` | e.g. `prepare_conversion_chain`, `create_tour_bridge`, … |
| `actor_surface` | e.g. `admin_http`, `publishing_console`, `ops_dashboard` |
| `requested_by` | Stable operator/admin subject id or token identity reference |
| `idempotency_key` | Client-supplied or correlated key |
| `source_entity_type` | e.g. `supplier_offer` |
| `source_entity_id` | Offer id |
| `target_entity_type` | e.g. `tour`, `execution_link` |
| `target_entity_id` | Created or linked id, nullable if failed before assign |
| `started_at` / `finished_at` | Timestamps |
| `status` | e.g. `started`, `succeeded`, `failed`, `skipped_idempotent` |
| `error_code` / `error_message` | Safe-for-ops diagnostics |
| `sub_steps[]` | Nested records for chains (or separate rows keyed by parent) |
| `before_summary` / `after_summary` | **Non-secret** hashes or field snapshots where safe |

**Current state:** Existing audit tables / logs may be **insufficient** for the above richness. **B16D2** (or a dedicated audit slice) should treat **storage** and **retention** as **implementation requirements**, **not** implied by this design-only document.

---

## 7. Danger classification

Reuse the established **style**:

| Class | Meaning (short) |
|-------|------------------|
| `safe_read` | No mutation |
| `safe_mutation` | Writes with low external blast radius |
| `conversion_enabling` | Makes booking / catalog path **reachable**; not yet public marketing blast |
| `public_dangerous` | Public channel or broad customer-visible effect |

**Classifications for this design:**

| Action | Classification |
|--------|----------------|
| **`prepare_conversion_chain`** | **`conversion_enabling`** — requires preconditions + confirmation + full audit |
| **`publish_showcase_channel`** | **`public_dangerous`** — always separate; strongest confirmation |
| **Payment completion** | **Financial / public-dangerous** or a **payment-controller-gated** action family — **out of scope** here |
| **Order cancel / refund** | **Future explicit OPS actions** — **not** part of **`prepare_conversion_chain`** |

---

## 8. Dashboard / UI behavior (**future**)

Surfaces (ops dashboard, publishing console, review flows) should converge on a **single** action descriptor model for the **next** suggested operator step, for example:

- `next_action_code`, `next_action_label`
- `enabled`, `disabled_reason`
- `requires_confirmation`, `danger_level`
- `action_explainer` (short)
- `what_will_happen[]`, `what_will_not_happen[]`
- `expected_result_after_success` (e.g. **`ready_to_publish`**)

### `prepare_conversion_chain` — copy hints

**Button labels (examples):**

- EN: **Prepare for publish**
- RO: **Pregătește pentru publicare**

**Confirmation copy must state** (paraphrase allowed; substance required):

- Creates or links the **tour bridge** if missing.
- **Activates** the tour **for catalog** when **eligible**.
- Creates an **active execution link** if missing.
- Does **not** publish to **Telegram**.
- Does **not** charge customers or alter **payments**.
- Does **not** change **existing orders**.

---

## 9. API design options (**not implemented**)

| Option | Sketch |
|--------|--------|
| **A** | `POST /admin/ops/actions/prepare-conversion-chain` (body: `supplier_offer_id`, …) |
| **B** | `POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain` |
| **C** | Generic executor: `POST /admin/actions` with `{ action_code, payload, idempotency_key }` |

### Recommendation: **Option B**

**Rationale:**

- **Clarity:** URL names the **primary resource** (the offer); fits existing `/admin/supplier-offers/...` family.
- **Auditability:** Logs and audits naturally partition by **offer id** in the path.
- **Admin conventions:** Aligns with other supplier-offer-scoped admin routes (review-package, future mutations).
- **Idempotency:** Header or body `Idempotency-Key` applies cleanly per **offer** + **action**.
- **Future reuse:** Other offer-scoped actions (`approve_package`, `publish_showcase_channel`) can mirror the same pattern; a **generic** **C** can still be introduced **later** as an internal dispatcher **behind** stable resource-centric HTTP routes if needed.

**Option C** remains valuable if many actions share identical plumbing; **start** with **B**-style **resource routes** for the highest-risk conversion paths, then refactor **internally** if duplication hurts.

---

## 10. Idempotency

- **Client supplies** `Idempotency-Key` (HTTP header is conventional; body acceptable if documented).
- **Same** `action_code` + **same** `source_entity_id` + **same** key ⇒ **same logical outcome**: repeated calls return **success** with **existing** artifact ids or a **safe** **`already_applied`** summary—**no** second bridge, **no** second execution link.
- **Telegram publish** is **not** in this chain; the same principle **still** applies to **`publish_showcase_channel`** when implemented: **no** duplicate channel posts for the same key + publish intent.

Server may persist idempotency records keyed by `(tenant scope if any, actor, action_code, source_id, key)`.

---

## 11. Non-goals (**this design document**)

- **Implementation** of endpoints, services, or migrations.
- **Auto-publish**, **scheduler**, or background workers.
- **Payment** completion, **order** cancellation, **refund** flows.
- **Supplier** outbound send automation.
- **Telegram** publish/send/retry inside **`prepare_conversion_chain`**.
- **Mini App** or **Layer A** behavioral changes **by** this doc alone.

---

## 12. Recommended next implementation sequence

After this design:

1. **B16B** — filters / limits / time-window controls for **`GET /admin/ops-dashboard`** (if not yet done).
2. **B16C** — dashboard → detail navigation polish.
3. **B16D1** — **read-only** **action plan preview** endpoint (or read-model extension): returns **planned** sub-steps and **disabled_reasons** — **no execution**.
4. **B16D2** — implement **`prepare_conversion_chain`** with **strict** preconditions, **per-step** audit persistence, and **idempotency**.
5. **B15E2** — explicit **action execution** integration in the **publishing console** (and siblings), reusing the same danger and confirmation rules.
6. **B15G** — guarded **auto-publish** — **design-only**, **much later**, separate approval gate.

---

## Related documents

- [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md) — read-only affordances today.
- [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md) — execution link before publish policy context.
- [`docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`](B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md) — ops aggregation (read-only).
