# Supplier execution flow (Y40)

**Phase:** Y40 — design only (documentation). **No** runtime code, migrations, tests, new APIs, workers, messaging, or schema in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38)  
- [`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md) (Y39)  
- [`docs/OPERATOR_WORKFLOW_GATE.md`](OPERATOR_WORKFLOW_GATE.md) (Y37.1)  
- [`docs/OPERATOR_DECISION_GATE.md`](OPERATOR_DECISION_GATE.md) (Y37.3)  

**Purpose:** Y38 defines **boundaries** (intent ≠ trigger). Y39 defines **entry points** (where a run may *start*). Y40 defines the **logical execution pipeline** after that start: **stages**, **safety invariants**, and what may **eventually** happen vs what is **forbidden** until explicitly implemented. It does **not** prescribe concrete table names, APIs, or message formats.

---

## 1. Clear distinction (concepts)

| Concept | Role |
|---------|--------|
| **Operator intent** (`operator_workflow_intent`) | **Decision data** for Layer C: what ops *thinks* should happen next. **Persisted** by operator workflow; **not** a start signal and **not** a pipeline (Y38). |
| **Entry point** | **Start signal** from an allowed Y39 family (admin action, job, external trigger, separate operator “do” action). Exactly **one** declared surface begins a run. |
| **Execution flow** | **Controlled action pipeline** from that start: validate → record intent to execute → attempt supplier-impacting step → record outcome → optional review. **Not** the same as saving operator intent. |

**Rule:** A single HTTP request that **only** sets `operator_workflow_intent` is **not** an execution flow instance; the flow begins only when a **Y39** entry point fires, with **separate** code paths and audit (Y39 §2, Y38 #5).

---

## 2. Future supplier execution flow — logical stages (order)

When an implementation exists, a **run** (instance) is expected to follow this **shape**. Names, persistence, and APIs are **TBD** per ticket.

| Stage | Purpose |
|-------|---------|
| **1 — Explicit entry point** | Handler receives the **Y39**-approved invocation (API, worker, webhook, or admin “do” action). **Not** an intent write. |
| **2 — Validation** | AuthZ/authN, preconditions (e.g. request exists, supplier eligible, rate limits, idempotency key), **fail-closed** on ambiguity. **Intent** may be **read** as context only. |
| **3 — Execution request / audit record** | Create or update a **durable** record: *what* is being attempted, *who* started it, *when*, idempotency key, link to `request_id` / resources. **This is the audit anchor** for the run. |
| **4 — Supplier action attempt** | The **only** place where *outbound* or *supplier-impacting* work would run in a future slice (e.g. enqueue message, call partner API — **not** in this doc’s deliverable). |
| **5 — Result recording** | Terminal or intermediate **outcome** of the attempt (success, failure, retryable error, no-op) stored against the run / audit record. |
| **6 — Operator / admin review (if needed)** | Optional **ops state** (e.g. “needs follow-up,” “escalate”) for failed or partial runs—**separate** from `operator_workflow_intent` unless a product spec explicitly links them later. |

**Note:** Stages 4–5 may be **asynchronous** in a real system (queue, webhook callback); the **logical** order and **single** audit thread still apply.

---

## 3. Required safety invariants (non-negotiable for any implementation)

| Invariant | Meaning |
|-----------|---------|
| **Idempotency** | Same idempotency key + same action **must not** cause duplicate **irreversible** effects without explicit detection and handling (align with Y39 §5). |
| **Auditability** | Every run is **attributable**: actor or job id, time, `request_id` (or resource), entry family, and outcome. No “mystery sends.” |
| **Retry safety** | Retries are **safe** w.r.t. idempotency and do **not** bypass validation; exponential backoff / dead-letter as appropriate for the chosen transport. |
| **No hidden triggers** | Flow **only** from declared entry (Y39); no ORM listeners on intent, no `operator-decision` side effects. |
| **Fail-closed** | If validation fails or policy is unclear, **do not** perform supplier-impacting work; record failure, surface to authorized roles only. |
| **Explicit permissions** | Each entry path checks **role** and **actor** the same way as other admin/ops mutators; integration paths use **verified** identity and scoped credentials. |

---

## 4. What the execution flow may **eventually** do (only when implemented in a **separate** ticket)

Illustrative only; **not** enabled by this document.

- **Prepare** a supplier contact action (build payload, select recipients) — *after* validation and audit record exist.  
- **Send** a supplier request or message — **only** in a future implementation that **explicitly** includes messaging and **cites** Y38 + Y39 + this doc.  
- **Record** supplier response — **only** in a future implementation with **inbound** contract and the same **audit** thread as the originating run, where applicable.  

**Layer C** remains unchanged: `operator_workflow_intent` can **inform** UIs and filters; it does **not** **replace** the execution run record.

---

## 5. What this design and the repo must **not** do **now**

This document and current production state:

- **No** supplier **messaging** or outbound sends introduced under Y40.  
- **No** new **RFQ** implementation beyond existing product behavior.  
- **No** **booking, order, payment, tour** mutations.  
- **No** **Mini App** or customer-surface changes.  
- **No** **`supplier_offer_execution_links`** or customer **execution** path changes.  
- **No** **identity bridge** or session changes.  
- **No** **customer** (or unscoped supplier) **notifications** from this line of design.  

Y40 **adds** documentation only. **No** `app/`, `tests/`, or migration changes for Y40 acceptance.

---

## 6. How Y40 preserves Y38 and Y39

- **Y38:** Intent is **data**; execution flow **starts** at Y39 entry points, **not** at intent write.  
- **Y39:** Entry points are **the only** starters; Y40 is what happens **after** the start **signal**, with audit and invariants.  
- **Y40:** Pipelines are **visible**; **no** conflation of “record intent” with “execute supplier work.”

---

## 7. Next step (product/engineering)

1. **Accept** this design as the **Y40** reference for **any** first supplier-execution **implementation** ticket.  
2. A future ticket must: cite **Y38**, **Y39**, and **this doc**; name **one** Y39 entry family + surface; map **stages 1–6** to concrete **types** and **persistence**; still **not** use `operator-decision` as executor.  
3. Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when a Y40-aligned slice is **implemented** or this flow is **revised**.

---

## Summary

| Topic | Y40 stance |
|--------|------------|
| **Intent** | Decision **data** (Layer C). |
| **Entry point** | **Start** signal (Y39). |
| **Execution flow** | **Pipeline** after start: entry → validate → audit → attempt → result → optional review. |
| **Invariants** | Idempotency, audit, retry safety, no hidden triggers, fail-closed, explicit permissions. |
| **Now** | Docs only; **no** messaging/RFQ/booking/Mini App/execution links/identity/notifications. |
