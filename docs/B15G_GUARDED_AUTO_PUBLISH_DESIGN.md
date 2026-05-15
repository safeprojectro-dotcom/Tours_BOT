# B15G — Guarded auto-publish (design only)

**Status:** `design_only` / **not implemented** — **no runtime behavior is enabled by this document.**  
**Scope:** documentation and architectural gates only. There is **no** auto-publish, scheduler, worker, Telegram send/publish/retry, new admin route, migration, or business-logic change implied or required by this gate.

---

## 1. Status and scope

- **Design only:** this file describes *future* guarded auto-publish behavior for the publishing console / supplier-offer funnel. Nothing here turns on auto-publish.
- **No runtime behavior added:** no code, endpoints, jobs, or Telegram I/O are introduced by B15G.
- **No auto-publish enabled:** production behavior remains “manual publish with explicit admin confirmation” for public Telegram showcase surfaces, per existing TECH_SPEC and publishing-console foundations.
- **No Telegram send/publish/retry:** any future execution must be a separate implementation track with its own go/no-go and tests.

**Aligns with:** `docs/TECH_SPEC_TOURS_BOT_v1.1.md` (Layer separation, visibility ≠ bookability, showcase vs execution truth), `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` (supplier marketplace / publishing ops sequencing), `docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`, `docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`, `docs/HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md`, production smoke notes `docs/B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md` and `docs/B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md`.

**Note:** `docs/BUSINESS-план-v2.txt` was not found in the repository at the time of writing; this design does not depend on that file.

---

## 2. Definition — three separate concepts

### 2.1 Internal conversion preparation

- **What it is:** `prepare_conversion_chain` — deterministic, auditable **internal** readiness work (bridge/catalog/execution-link alignment, plan materialization, operator-facing diagnostics).
- **What it is not:** **not** a public publish, **not** Telegram I/O, **not** a substitute for Layer A booking/payment authority, **not** a channel “go live” action.
- **I/O boundary:** may touch DB and internal read models; must **not** broadcast to Telegram or mutate orders, reservations, seats, or payments.

### 2.2 Manual publish

- **What it is:** an **explicit** admin (or authorized operator) action that causes a **public** side effect on the Telegram showcase / discovery surface (e.g. post message, pin policy per product rules), with clear actor, audit, and rollback expectations.
- **Invariant:** **no hidden publish** — human or system intent must be visible in audit and product UX; no silent publish from supplier input alone.

### 2.3 Future guarded auto-publish

- **What it may mean (future):** after **strict gates**, the system may **propose**, **queue**, or **schedule** publication — still with **admin approval** where required by mode, and always **auditable** and **reversible** within product/ops limits (Telegram posts may require manual channel cleanup; see §8).
- **What it does NOT mean:** no fully automatic “supplier submits → live on channel” without an explicit future decision gate; no bypass of approval for MVP-class public showcase; no conflation with `prepare_conversion_chain` success.

---

## 3. Current foundation (closed work)

The following **already exist** and support **internal readiness** and **operator execution**; they **do not** constitute public auto-publish:

| Track | What was delivered | Role |
|--------|-------------------|------|
| **B16D2C** | `POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain` | Guarded HTTP execution of prepare plan; `actor_surface` e.g. `admin_http`. |
| **B16D2D** | Read-model **action affordances** for `prepare_conversion_chain` | UI/navigation hints; **no** extra business logic in UI; derives from service/readiness. |
| **B16D2E** | Production smoke (`docs/B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md`) | Validates prepare endpoint + affordances in Railway context. |
| **B15E2** | `POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain` | Same internal prepare handler with `actor_surface=publishing_console`. |
| **B15E2 smoke** | `docs/B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md` | Publishing-console path smoke; still **internal** prepare, not Telegram publish. |

**Key alignment:** `prepare_conversion_chain` = **internal conversion preparation**. **Public** Telegram showcase publish remains a **separate** explicit action and must stay separate from internal conversion preparation per project invariants (see §“Architectural invariants” below).

---

## 4. Proposed future auto-publish gates

Before **any** future auto-publish **proposal** or **execution** (per chosen mode in §6), **all** applicable gates below must pass. Exact evaluation order and caching are implementation details; **stale recheck immediately before send** is required in §11.

**Lifecycle and packaging**

- Supplier offer lifecycle indicates **approved** or **published-ready** (exact enum names TBD at implementation time; must not be guessed in UI).
- `packaging_status` (or successor field) = **`approved_for_publish`** (or equivalent product-defined state).

**Content and media**

- Content quality review has **no blocking issues** (policy: blocking vs non-blocking defined in admin workflow).
- Media review **approved**, **or** **safe text-only fallback** explicitly selected and recorded (no implicit downgrade).

**Safety and channel**

- `publish_safe` (or successor) **acceptable** for **target channel** (rate limits, policy, incident posture).
- **Showcase preview** generated and **valid** (schema, length, link targets, disclosure text if required).

**Internal readiness (non-substitute)**

- `prepare_conversion_chain` **plan status** is **`already_prepared`** **or** a **documented safe partial state** (must be explicitly defined in implementation spec — **not** “dry_run only” or “affordable only”).
- **Active tour bridge** present where the funnel requires catalog linkage.
- **Catalog tour** `open_for_sale` **where required** by CTA semantics (visibility ≠ bookability still applies: visible showcase copy must not imply bookability Layer A does not support).

**Execution path**

- **Active execution link** present **where** the channel CTA expects in-Mini-App booking (otherwise CTA must be disabled or point to non-booking landing — product rule).
- **No** future-departure blocker (calendar/ops rule set).
- **No** catalog visibility blocker that would make showcase misleading.

**Conflict and operations**

- **No** **B8** same-offer/date **conflict** (or successor duplicate-detection policy).
- **No** open **critical incident / disruption** flag affecting this offer or route class.
- **No** unresolved **supplier clarification** request tied to this publish artifact.
- **No** **admin-level publish hold** flag (global or per-offer).

**Engineering**

- **Idempotency key strategy** defined for publish attempts (see §7).
- **Rollback / unpublish strategy** defined before first auto-scheduled publish (see §8).
- **Audit actor** defined (human vs system; surface; correlation id).

---

## 5. Explicit non-gates / not enough alone

The following are **insufficient by themselves** to allow auto-publish (even if true):

- Supplier submits an offer (raw input is never publish authority).
- AI-generated content exists (generation ≠ approval ≠ safety).
- Packaging generated but **not** approved.
- Tour bridge exists **without** full gate set (e.g. missing execution link when CTA implies booking).
- Tour is `open_for_sale` but **no** execution link when booking CTA is shown.
- Offer was published **historically** (stale or superseded artifacts are dangerous).
- Publishing console **row exists** (UI presence ≠ readiness).
- **Action affordance** enabled for prepare (affordance = hint, not publish proof).
- **`dry_run` success only** for prepare (no substitution for publish gates).
- **Smoke passed once** on a different offer/environment (gates must be evaluated per attempt).

---

## 6. Proposed future modes

| Mode | Behavior | MVP stance |
|------|----------|------------|
| **1. Disabled** | No auto behavior; manual only. | **Default / recommended now.** |
| **2. Suggest only** | System surfaces “ready to publish” recommendation; **admin still clicks publish.** | **Recommended** early future step. |
| **3. Queue for approval** | System enqueues item; **admin approves batch** before any send. | Future; needs queue UX + audit. |
| **4. Scheduled after explicit approval** | Admin approves **now**, publish **later**; worker executes **only** pre-approved item. | Future; needs scheduler + hold states. |
| **5. Fully automatic publish** | System publishes without per-item human confirm. | **Not approved for MVP;** separate business/security gate. |

**Current recommendation (B15G):**

- **Disabled** and/or **Suggest only** only.
- **No** fully automatic publish in current scope.
- Any scheduling mode (4) requires explicit policy + audit + rollback runbook before implementation.

---

## 7. Audit and idempotency requirements

For **every** publish attempt (manual or future semi-auto):

- **Publish attempt audit** persisted (append-only log or equivalent).
- **action_code** / verb required (e.g. `telegram_showcase_publish_attempt`).
- **actor_surface** required (`publishing_console`, `admin_http`, `worker`, …).
- **requested_by** required for **human-triggered** actions (user id or service principal for system).
- **idempotency_key** required at publish boundary to prevent duplicate posts under retries.
- **payload_fingerprint** (hash of canonical publish payload + channel id + locale) to detect drift.
- **Before/after state snapshots** recommended (offer id, revision ids, preview hash, gate snapshot id).
- **Provider response** (Telegram API result) stored safely (redact secrets); linkage to audit row.
- **Retry policy:** **manual-first** for public publish failures; **no silent retries** without a future explicit gate (policy doc + monitoring).
- **No hidden** `prepare_conversion_chain` execution unless **explicitly** configured and audited as a distinct action (prepare ≠ publish).

---

## 8. Failure and rollback

**Failure scenarios**

| Scenario | Handling principle |
|----------|-------------------|
| Telegram API failure | Mark attempt **failed**; surface error; **no** silent retry (until policy exists). |
| Duplicate publish attempt | **Idempotency** returns prior result or rejects as duplicate; **never** double-post without explicit recovery. |
| Partially persisted publish attempt | Reconcile via **audit + idempotency**; ops playbook for stuck rows. |
| Channel post sent but DB update failed | **Critical:** treat as **inconsistent state**; alert ops; may require manual reconcile (post id known vs DB). |
| DB update succeeded but Telegram post failed | Roll back **DB publish flags** only if product allows; otherwise mark **failed** and block CTA. |
| Stale content after approval | **Mandatory recheck** immediately before send (§11); if fail, **abort** and notify. |
| Tour becomes not bookable after approval | **Abort** or switch CTA to non-booking fallback per policy; never imply Layer A bookability. |
| Execution link removed after approval | **Abort** send if CTA requires booking; or swap to safe landing. |
| Incident/disruption after scheduled approval | **Incident gate** blocks worker; reschedule or cancel with audit reason. |

**Rollback options (non-exhaustive)**

- Mark publish **failed** / **cancelled** with reason code.
- Disable CTA / **fallback landing** in showcase payload.
- **Manual** delete/edit channel post if Telegram/API allows; document limitation if not.
- **Unpublish / close** showcase state in DB when product supports it.
- **Document manual cleanup** when automation cannot fully reverse channel truth.

---

## 9. Data model implications (future only — no migration in B15G)

Possible future artifacts (illustrative names only):

- `auto_publish_policy` — per-tenant or per-channel policy record.
- `publish_hold_reason` — structured hold/exemption.
- `approved_for_scheduled_publish_at` — when human approved scheduling window.
- `scheduled_publish_at` — intended execution time (UTC).
- `scheduled_publish_by` — approver identity.
- `auto_publish_mode` — enum matching §6.
- `auto_publish_gate_snapshot_json` — immutable snapshot of gate evaluations at approval time.
- `auto_publish_decision_log` — append-only decisions (approve/cancel/fail).
- `publish_batch_id` — batch approval correlation.

**All future only.** No schema change in B15G.

---

## 10. API implications (future only — no endpoint in B15G)

Illustrative future endpoints (names subject to API design):

- `GET` **publish readiness** — read-only gate evaluation + reasons.
- `POST` **propose auto-publish** — creates suggestion or queue item (no send).
- `POST` **approve scheduled publish** — records approval + schedule.
- `POST` **cancel scheduled publish** — cancels pending schedule.
- `POST` **execute scheduled publish (worker-safe)** — idempotent execution only for pre-approved rows.

**All future only.**

---

## 11. Testing strategy (future implementation)

When implementation is approved:

- **Gate evaluation unit tests** — each gate fail prevents publish proposal/execution.
- **Integration:** no publish when **any** gate fails.
- **Stale gate recheck** immediately before send (time-boxed freshness).
- **Idempotent publish execution** — same idempotency key does not double-post.
- **Duplicate prevention** under concurrent workers.
- **Telegram failure handling** — persisted state + operator visibility.
- **Rollback / manual cleanup path** — exercised in staging.
- **No Layer A mutation** from publish path (orders/reservations/seats/payments untouched).
- **No hidden prepare_conversion_chain** unless explicitly configured and tested.
- **Smoke test** on known-safe offer in staging/production dry_run policy.
- **Production dry_run** before first live auto-*scheduled* send (when that mode exists).

---

## 12. Decision / recommendation

- **B15G status:** **design accepted; no implementation** in this gate. No runtime code, routes, workers, or migrations are introduced here.
- **Next safe implementation** (when prioritized): start with **read-only publish readiness evaluation** (`GET`-class behavior in §10) and **Suggest only** UX — **not** actual auto-send.
- **Public Telegram publish** must remain **explicit human-confirmed** (manual publish path) until a **separate go/no-go** decision approves queued or scheduled modes — and **never** conflate with `prepare_conversion_chain` success.

---

## Architectural invariants (must be preserved)

The following are **non-negotiable** for any future auto-publish work:

- **PostgreSQL-first** persistence; migrations safe-by-default.
- **Service layer** owns business rules; **repositories** remain persistence-only.
- **UI / routes / publishing console** must not duplicate business logic (derive from services/read models).
- **Telegram channel** = softer **showcase / discovery**; **Mini App / execution catalog** = **strict execution truth**.
- **visibility ≠ bookability.**
- **Public publish** and **Telegram send** remain **separate** from **internal conversion preparation** (`prepare_conversion_chain`).
- **No hidden publish**; **no hidden** order/payment/reservation/seat mutation; **no hidden** supplier execution retry.
- **Layer A** booking/payment remains the **only authority** for orders, reservations, payments, and seats.
- **Payment entry / reconciliation** remains the **only payment authority.**

---

## Out of scope (explicit, now)

- Any code, endpoint, worker, scheduler, Telegram Bot API integration, publish execution, retry execution, migration, or automated test code for this gate.
- Changing existing `prepare_conversion_chain` semantics beyond future **read-only** readiness surfaces when separately specified.
- Supplier input alone driving channel truth without human gate (modes 3–5 require future approval).

This document completes **B15G — guarded auto-publish design only.**
