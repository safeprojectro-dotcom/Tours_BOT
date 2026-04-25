# Supplier execution data contract (Y41)

**Phase:** Y41 — design only (documentation). **No** Alembic migrations, **no** SQLAlchemy models, **no** Pydantic/OpenAPI schemas, **no** `app/` or `tests/` changes in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38)  
- [`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md) (Y39)  
- [`docs/SUPPLIER_EXECUTION_FLOW.md`](SUPPLIER_EXECUTION_FLOW.md) (Y40)  
- [`docs/OPERATOR_WORKFLOW_GATE.md`](OPERATOR_WORKFLOW_GATE.md) (Y37.1)  
- [`docs/OPERATOR_DECISION_GATE.md`](OPERATOR_DECISION_GATE.md) (Y37.3)  

**Purpose:** Give **minimal, implementation-agnostic** **logical** records for a **future** supplier execution layer so the first migration does **not** invent one fat table, does **not** use live `operator_workflow_intent` as workflow state, and does **not** couple to Layer A or customer surfaces. Table names, indexes, and exact types are **TBD** when a ticket implements persistence.

---

## 1. Minimal **future execution request** record (logical)

One row = **one** supplier-execution **run** started from a **Y39** entry point (audit anchor per Y40 §2 stage 3).

| Field | Role |
|-------|------|
| **`id`** | Stable identifier of this **execution request** (surrogate key in a future DB). |
| **`source_entry_point`** | **How** the run was started — must be traceable to a **Y39** family (e.g. `admin_explicit`, `scheduled_job`, `external_webhook`, `operator_do_action`). **Illustrative** enum-like string; concrete values fixed in implementation. |
| **`source_entity_type`** | Type of primary business entity the run concerns (e.g. `custom_marketplace_request`). **Not** an order or booking type. |
| **`source_entity_id`** | Primary key of `source_entity_type` (e.g. custom request id). |
| **`operator_workflow_intent_snapshot`** | Nullable **copy** of `operator_workflow_intent` **at run creation** (or at a defined moment in validation). **Context only** — see §6. |
| **`requested_by_user_id`** | **`users.id`** of the actor who **invoked** the entry (or null for pure system/job if policy allows). |
| **`status`** | Lifecycle of **this** request — see §4. **Not** `CustomMarketplaceRequest.status`. |
| **`idempotency_key`** | Caller-supplied or derived key for **idempotent** create/replay (Y39/Y40). Uniqueness scope defined in implementation. |
| **`created_at`** | Creation time (timezone-aware in implementation). |
| **`updated_at`** | Last mutation time. |

**Note:** This record is **not** an RFQ row, **not** a bridge row, **not** an order.

---

## 2. Minimal **future execution attempt** record (logical)

One row = **one** **try** to perform a supplier-impacting action (Y40 stage 4). Retries = multiple rows with increasing **`attempt_number`** for the same **`execution_request_id`**, or one row updated per policy — **implementation choice**; this contract only requires **traceable** attempts.

| Field | Role |
|-------|------|
| **`id`** | Surrogate key for the attempt. |
| **`execution_request_id`** | FK (logical) to **execution request** `id`. |
| **`attempt_number`** | 1-based sequence per request (or monotonic). |
| **`channel_type`** | **Illustrative:** `telegram`, `email`, `partner_api`, `internal`, `none` — fixed in implementation. |
| **`target_supplier_ref`** | Opaque or structured ref to supplier (e.g. supplier id, external id) — **no** PII requirement in this doc. |
| **`status`** | Outcome of **this** attempt (may align with §4 subset or attempt-specific values — see §4 notes). |
| **`provider_reference`** | External correlation id (message id, provider job id), nullable. |
| **`error_code`** | Machine-readable failure code, nullable. |
| **`error_message`** | Sanitized human/debug text, nullable. |
| **`created_at`** | When the attempt was **recorded**. |

---

## 3. Minimal **future result / audit** fields (logical)

These may live **on the execution request** row, on a **final attempt** row, or a small **append-only** audit tail — **implementation choice**. The contract requires the **information** to exist for **terminal** runs.

| Field | Role |
|-------|------|
| **`final_status`** | Terminal summary aligned with §4 (`succeeded`, `failed`, `cancelled`, or `blocked` as terminal). |
| **`completed_at`** | When the run reached a **terminal** state. |
| **`completed_by`** | **`users.id`** or system marker for who/what closed the run, nullable if system. |
| **`raw_response_reference`** | Pointer to **stored** payload (object store, JSON blob id, etc.) — **not** raw dump in hot row if large; nullable. |
| **`audit_notes`** | Optional internal ops notes (not customer-facing). |

---

## 4. **Status** boundaries (execution **request** lifecycle)

Use **one** coherent set for **`execution_request.status`** (and align **attempt** `status` or a subset as needed).

| Status | Meaning |
|--------|---------|
| **`pending`** | Created; not yet validated. |
| **`validated`** | Preconditions passed; allowed to proceed to attempt(s). |
| **`blocked`** | Validation/policy failure; **fail-closed**; no supplier action (or no further action) until resolved or cancelled. |
| **`attempted`** | At least one **attempt** has been **recorded** (may still retry). |
| **`succeeded`** | **Terminal** success. |
| **`failed`** | **Terminal** failure after attempts or unrecoverable error. |
| **`cancelled`** | **Terminal** — user/system cancelled before success. |

**Rules:**  
- **Terminal** states: `succeeded`, `failed`, `blocked` (if treated as terminal), `cancelled` — product may choose whether `blocked` is terminal or recoverable; if recoverable, document in implementation.  
- **Not** a replacement for **`CustomMarketplaceRequest.status`** or **`operator_workflow_intent`**.

---

## 5. Separation rules (forbidden couplings)

Data for these future records **must not** be used to **mutate**:

- **`orders`**, **`payments`**, **bookings**, **tours** (Layer A).  
- **Mini App** DTOs or customer read models (no dependency of execution persistence on Mini App shape).  
- **`supplier_offer_execution_links`**.  
- **Identity bridge** / session / `telegram_user_id` binding logic.  
- **Customer notifications** (no default fan-out to customers from these tables’ triggers).  

**RFQ** domain tables may only be touched if a **future** ticket explicitly scopes it; Y41 does **not** add RFQ schema.

---

## 6. **Intent** usage (non-negotiable)

| Rule | Detail |
|------|--------|
| **Snapshot** | **`operator_workflow_intent_snapshot`** may copy the current enum value from `custom_marketplace_requests` for **audit and reporting**. |
| **Not a live trigger** | Changes to live `operator_workflow_intent` **do not** enqueue, update, or cancel execution requests **by side effect**. |
| **Not primary execution state** | Workflow progression for supplier execution is **`execution_request.status`** + **attempt** records, **not** the Layer C intent column. |

---

## 7. Invariants (align with Y39 / Y40)

- **Idempotency:** **`idempotency_key`** on the **execution request**; replays must not double-charge irreversible external effects.  
- **Auditability:** **`requested_by_user_id`**, **`created_at`**, **`source_entry_point`**, **`source_entity_*`**, attempts, **`final_status`**, **`completed_at`**.  
- **Explicit permissions:** Enforced at the **entry point** (Y39), not inferred from snapshot.  
- **No hidden triggers:** No DB trigger on `operator_workflow_intent` that inserts/updates these records.  

---

## 8. Next step (product/engineering)

1. When persistence is **implemented**, a **migration ticket** maps this contract to **real** tables/columns/types; cites **Y38–Y41**.  
2. **Do not** merge execution request into `custom_marketplace_requests` as the only row — keep **separation** unless a later gate collapses them with explicit tradeoffs.  
3. Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when a Y41-aligned migration is **accepted** or this contract **revises**.

---

## Summary

| Topic | Y41 stance |
|--------|------------|
| **Execution request** | Audit anchor: entry, entity ref, snapshot intent, idempotency, lifecycle **status**. |
| **Execution attempt** | Per-try record with channel, target ref, outcome/error. |
| **Result/audit** | Terminal fields + optional response ref and notes. |
| **Statuses** | `pending` → `validated` / `blocked` → `attempted` → `succeeded` / `failed` / `cancelled`. |
| **Intent** | Snapshot only; **not** trigger; **not** primary execution state. |
