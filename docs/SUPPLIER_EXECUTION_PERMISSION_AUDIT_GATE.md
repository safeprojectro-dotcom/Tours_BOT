# Supplier execution permission & audit gate (Y42)

**Phase:** Y42 — design only (documentation). **No** migrations, models, `app/`, `tests/`, or API changes in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38)  
- [`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md) (Y39)  
- [`docs/SUPPLIER_EXECUTION_FLOW.md`](SUPPLIER_EXECUTION_FLOW.md) (Y40)  
- [`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`](SUPPLIER_EXECUTION_DATA_CONTRACT.md) (Y41)  
- [`docs/OPERATOR_WORKFLOW_GATE.md`](OPERATOR_WORKFLOW_GATE.md) (Y37.1)  
- [`docs/OPERATOR_DECISION_GATE.md`](OPERATOR_DECISION_GATE.md) (Y37.3)  

**Purpose:** Y41 defines **what** to persist. Y42 defines **who may start** supplier execution, **how** that differs from “record intent,” and **what** must be **audited** and **when** the system must **refuse** (fail-closed). Concrete RBAC keys, role tables, and endpoint paths are **TBD** in an implementation ticket; this file is the **agreed rules**.

---

## 1. Who may **initiate** future supplier execution (illustrative roles)

A **start** (Y39 entry) is allowed **only** from one of these **categories**; each **implementation** must map to **authenticated** identity and **separate** permission checks from Layer C.

| Initiator class | Description |
|-----------------|-------------|
| **Central admin explicit action** | User with **central admin** (or product-defined) authority to invoke a **dedicated** supplier-execution **entry** (e.g. admin API, Telegram admin callback whose **contract** is execution — **not** `operator-decision`). |
| **Authorized operator explicit action** | **Assigned** or **allowlisted** operator who invokes a **separate** “do”/execute entry (Y39), **if** a future policy grants **execution** to operators on that surface. **Not** implied by “can set intent.” |
| **Authorized system job** | **Named** worker/scheduler with **service identity** and **scoped** policy; job **inputs** and **idempotency** are explicit. |
| **Authenticated external integration** | Inbound **webhook** or partner API with **verify** (signing, secret, mTLS, etc.); each request is an **integration**-grade **start**, not a customer path. |

**Denied:** “Anyone who can call `operator-decision`” is **not** sufficient to initiate execution. **Customer** and **unauthenticated** requests do **not** start supplier execution (unless a **future** product gate **explicitly** and narrowly defines an exception—out of Y42 by default).

---

## 2. Permission rules (non-negotiable)

| Rule | Detail |
|------|--------|
| **Assigned operator may record intent** | Per Y37.4/Y37.5: `POST .../operator-decision` when **Owner = you**, **`under_review`**, etc. This is **Layer C** only. |
| **Recording intent is not execution permission** | Permission to **set** `operator_workflow_intent` **must not** grant permission to **create** a supplier execution run or **send** to suppliers. |
| **Supplier execution needs separate permission** | A **distinct** check (and ideally a **distinct** route/operation) for “start / continue supplier-impacting execution” vs “record next-step intent.” |
| **Admin/operator action must be explicit and auditable** | Human-initiated runs must be **attributable** to **`users.id`** (or equivalent) and the **entry point** used; no silent execution. |

**Implementation** must not collapse “intent” and “execute” into one permission bit.

---

## 3. Audit requirements (what must be **capturable** for every execution request)

At minimum, a conforming system must be able to answer **for each** execution request (Y41 records):

| Audit element | Description |
|---------------|-------------|
| **Who initiated** | `requested_by_user_id` and/or system job / integration id (Y41). |
| **What entry point was used** | `source_entry_point` and, if needed, sub-type (align Y39). |
| **Source entity** | `source_entity_type` + `source_entity_id`. |
| **Intent snapshot, if used** | `operator_workflow_intent_snapshot` — **optional**; when present, it is **context**, not a **live** join to intent for **permission**. |
| **Idempotency key** | `idempotency_key` as recorded (Y41). |
| **Validation result** | Pass/fail and **reason** for **blocked** (policy, missing data, not eligible). **Persist** enough to support compliance and support. |
| **Attempt/result state** | Links to **attempts**; **final** `status` and **`completed_at`**. |
| **Error reason if blocked/failed** | Machine code + message (or `audit_notes`) suitable for **ops**; **not** a substitute for **customer** notification. |

**Retention, PII, and log redaction** are **TBD** per product/compliance; Y42 only requires the **semantics** exist.

---

## 4. Fail-closed rules

| Condition | Result |
|-----------|--------|
| **Missing permission** for this entry + entity | **Do not** start or continue supplier-impacting execution; record **blocked** (or reject before persistence) with **reason**. |
| **Missing source entity** (unknown type/id, row deleted) | **Block**; no **ambiguous** run. |
| **Missing idempotency key** when the contract **requires** one | **Block** (or use a **strict** server-generated idempotency with documented scope — **design** in the implementation ticket, not a silent default). |
| **Ambiguous source** (e.g. two candidate requests) | **Block**; require **explicit** disambiguation in the next request. |
| **Stale or invalid intent snapshot** | **Do not** **auto-refresh** live `operator_workflow_intent` into the execution run or **re-open** a terminal run. New intent in Layer C does **not** **mute** a failed run without a **new** **explicit** start (Y39). **Snapshot** stays historical context unless a **new** execution request is **explicitly** created. |

Default posture: **deny** when in doubt.

---

## 5. Strict separation (restate + enforce in implementation)

- **`operator_workflow_intent`** = **context only** (snapshot in Y41); **not** a **live** permission source for execution, **not** **execution** state.  
- **`POST /admin/custom-requests/{id}/operator-decision`** = **intent persistence** only; **not** a supplier **execution** endpoint.  
- **No** **hidden** trigger from **DB** updates, ORM **events**, or **unrelated** code paths to **insert** or **progress** execution requests.

---

## 6. Hard constraints (Y42 + prior gates)

Y42 does **not** add:

- Supplier **messaging**  
- **RFQ** implementation  
- **Booking / order / payment** mutation  
- **Mini App** changes  
- **Execution link** or **identity bridge** mutation  
- **Customer** notifications  

A future PR that implements **checks** and **audit** must cite **Y38–Y42** and the **Y41** field list.

---

## 7. Next step (product/engineering)

1. **Accept** this gate for **Y42** continuity.  
2. First **implementation** ticket: wire **RBAC** and **audit** to these rules, plus **Y41** persistence.  
3. Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when an implementation slice is **accepted** or this gate is **revised**.

---

## Summary

| Topic | Y42 stance |
|--------|------------|
| **Initiators** | Admin, authorized operator (if policy), system job, external integration — **not** “intent” alone. |
| **Permission** | Intent **≠** execution permission. |
| **Audit** | Who, entry, entity, optional snapshot, idempotency, validation, attempts, terminal state, errors. |
| **Fail-closed** | Missing permission, entity, idempotency, ambiguity, snapshot misuse → **block**. |
| **Separation** | Intent = context; `operator-decision` ≠ execute; no hidden **DB** triggers. |
