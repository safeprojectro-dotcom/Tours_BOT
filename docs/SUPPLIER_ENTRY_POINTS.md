# Supplier interaction entry points (Y39)

**Phase:** Y39 — design only (documentation). **No** runtime code, migrations, tests, new APIs, workers, or messaging in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38: intent ≠ trigger; separate supplier layer)  
- [`docs/OPERATOR_WORKFLOW_GATE.md`](OPERATOR_WORKFLOW_GATE.md) (Y37.1)  
- [`docs/OPERATOR_DECISION_GATE.md`](OPERATOR_DECISION_GATE.md) (Y37.3)  
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (accepted Layer C state)

**Purpose:** Y38 forbids **starting** supplier-impacting work from `operator_workflow_intent` and from the **operator-decision** path. Y39 **names** the **only acceptable families** of **entry points**—the places a future design may attach **supplier interaction** so that work is **explicit, auditable, and not hidden behind intent writes**.

---

## 1. What **may** start supplier interaction in the future (allowed families)

When a product slice is **separately** gated and implemented, only these **kinds** of starts are **architecturally** acceptable. Concrete routes, job names, and payloads are **TBD** in implementation tickets; this section defines **types** only.

| Family | Description | Notes |
|--------|-------------|--------|
| **Admin / central explicit action** | A **human (or service account) with admin/ops authority** invokes a **dedicated** operation whose **sole purpose** is the supplier-impacting step (e.g. “send nudge to eligible suppliers,” “publish request to supplier queue” — **names illustrative**). | Must be a **different** HTTP/CLI/Telegram callback than **`POST /admin/custom-requests/{id}/operator-decision`**. **Reading** `operator_workflow_intent` to **pre-fill** a screen or **filter a list** is allowed; that read **must not** auto-fire the action. |
| **Scheduled / background job** | A **worker** runs on a **defined schedule** or queue with **explicit** policy (what to process, rate limits, idempotency keys). | Trigger is **the schedule or queue message**, not a row change in `custom_marketplace_requests` from intent. Optional: job **inputs** can include `request_id` and **current** intent as **read-only** context. |
| **External trigger** | Inbound **webhook** or **integration** (e.g. partner system) with **auth**, **verify**, and **explicit** handler entry. | Treated as its own “admin-grade” or “integration” entry; **not** a DB trigger on `operator_workflow_intent`. |
| **Manual operator-triggered action (not intent)** | An operator uses a **UI control or API** whose **name and contract** are about **doing** something to suppliers, **separate** from “set next step / intent.” | Distinct from recording **`need_supplier_offer`**. E.g. a button “Notify suppliers” (future) is an **action**; “Need supplier offer” on the same request remains **Layer C** intent only until combined in UI **without** coupling the **backend** of intent to the **send**. |

**Illustrative rule:** If you cannot **name the entry point** in one line (“User called X”, “Job Y started”, “Webhook Z received”), it is **not** an allowed start under this design.

---

## 2. What **must not** start supplier interaction

| Forbidden starter | Rationale |
|-------------------|-----------|
| **Change to `operator_workflow_intent`** (including `need_supplier_offer` / `need_manual_followup`) | Y38: intent is **stored decision**, not a trigger. |
| **`POST /admin/custom-requests/{id}/operator-decision`** (or any future alias that **only** persists operator intent) | Same path may **read** and **return** DTOs; it **must not** enqueue supplier work, call supplier Telegram, or mutate RFQ/bridge/booking. |
| **Implicit side effects** | No ORM hooks, `after_update` on `CustomMarketplaceRequest` for intent, “listener” on enum change, or **hidden** `if intent == x: send_supplier()` in unrelated code. |
| **Mini App** or **customer** surfaces | Supplier interaction starts from **ops/admin/integration** entry points, not from customer `My requests` (unless a **future** product gate explicitly and narrowly defines otherwise). |

---

## 3. Entry point **types** (where code may **live** in a future implementation)

These are **categories of surfaces**, not concrete endpoints. Each real slice must name **one** primary type and document security.

| Type | Role |
|------|--------|
| **Explicit API endpoints** | New or extended **`/admin/...`** (or dedicated integration) routes with **auth**, **body**, **idempotency** key in contract where needed. **Not** piggyback on operator-decision. |
| **Background workers** | Celery/RQ/scheduled process (whatever the project uses) with **named** job and **input** contract. |
| **Admin panel / Telegram admin actions** | Button → **distinct** callback or **new** `POST` behind the same **actor** model as other admin mutators (e.g. `X-Admin-Actor-Telegram-Id` when applicable), **separate** from intent callbacks. |

---

## 4. Separation (non-negotiable)

| Concept | Stance |
|---------|--------|
| **Operator workflow** | **Layer C** — assignment, `under_review`, **`operator_workflow_intent`**. **Decision and coordination** only. |
| **Supplier execution** | **Future layer** — starts only from **§1** families via **§3** surfaces. |
| **Intent** | **Data** for planning and **read** context; **not** a **trigger** and **not** a **workflow executor** (Y38 + this doc). |
| **Trigger** | A **separate, explicit** invocation: API call, job tick, webhook, or **named** admin action—**not** a side effect of saving intent. |

---

## 5. Required invariants (every future slice must satisfy)

| Invariant | Meaning |
|-----------|---------|
| **Idempotency** | Repeating the same explicit invocation (same idempotency key or safe default) does **not** duplicate irreversible side effects (e.g. double-send) without detection. |
| **Auditability** | Who/what started the action, when, which `request_id` (or resource), and outcome—**attributable** to the entry point, not to “intent changed mysteriously.” |
| **Explicit invocation** | A developer can find **one** function or **one** route as the start of the supplier-impacting path. |
| **No hidden triggers** | No `operator-decision` handler, no intent column migration, and no “magic” on `CustomMarketplaceRequest` updates that **starts** supplier work without going through a **declared** entry in §1 / §3. |

---

## 6. Hard constraints for **this** document and for **any** first implementation (restated)

This design doc **does not** add:

- Supplier **messaging**  
- **RFQ** behavior beyond what already exists without new triggers  
- **Bookings, orders, payments**  
- **Mini App** changes  
- **Execution links** or **identity bridge** work  
- **Customer** or **supplier** **notifications** as part of this doc  

A future PR must cite **Y38** and **this file** and stay within an **accepted** product slice; it must **not** introduce **hidden** starters from **§2**.

---

## 7. How this preserves Y38

- Y38: intent **read-only** for supplier logic **w.r.t. triggering**; separate layer; **no** coupling to `operator-decision` **as executor**.  
- Y39: **concretizes** that by saying supplier work **only** starts at **explicit** entry points (§1, §3) and **never** at intent writes or the operator-decision endpoint as a **side effect** (§2).  
- Together: **intent** can still **guide** humans or **filter** UIs; **execution** of supplier interaction requires a **second, explicit** step and contract.

---

## 8. Next step (product/engineering)

1. When the **first** supplier-interaction feature is prioritized, open an **implementation** ticket that **names** the chosen **entry family** (§1) and **surface type** (§3), with **Y38** + **this doc** in the description.  
2. Add **API/job spec** (paths, idempotency, audit fields) in that ticket or a child design note—**still** not “wire intent to send.”  
3. Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when a Y39+ slice is **accepted** or the entry-point list is **revised** (e.g. new integration type).

---

## Summary

| Topic | Y39 stance |
|--------|------------|
| **Allowed starts** | Admin explicit action, jobs, external triggers, **separate** operator “do something” — **not** intent save. |
| **Forbidden starts** | Intent change, `operator-decision` as **executor**, implicit hooks. |
| **Surfaces** | Dedicated API, workers, admin actions — **not** intent endpoint. |
| **Invariants** | Idempotency, audit, explicit invocation, no hidden triggers. |
