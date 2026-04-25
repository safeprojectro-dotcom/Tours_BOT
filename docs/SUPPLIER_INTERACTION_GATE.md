# Supplier Interaction Gate (Y38)

**Phase:** Y38 — design / architectural boundary (documentation only)  
**Depends on:**  
- [`docs/OPERATOR_WORKFLOW_GATE.md`](OPERATOR_WORKFLOW_GATE.md) (Y37.1)  
- [`docs/OPERATOR_DECISION_GATE.md`](OPERATOR_DECISION_GATE.md) (Y37.3)  
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (accepted Y36 / Y37.2 / Y37.4 / Y37.5)  

**This document does not** add or change runtime code, migrations, API contracts, tests, or Telegram/Mini App behavior. It is the **agreed boundary** that must hold **before** any new **supplier interaction** or **automation** is implemented in a **separate** track or layer.

---

## Purpose

`operator_workflow_intent` (e.g. **`need_supplier_offer`**, **`need_manual_followup`**) exists so **assigned operators** can record **internal coordination intent** on custom marketplace requests (Layer C / RFQ). Y38 **locks** that design so it is **not** misread as a **trigger** for supplier systems, customer flows, or Layer A commercial execution.

---

## Boundary decisions (authoritative for Y38)

1. **Operator workflow remains decision-only.**  
   The implemented operator workflow (assignment, **`open` → `under_review`**, persisting **`operator_workflow_intent`**) is **coordination and reporting** for **admin/ops** only. It does not **execute** or **orchestrate** supplier, customer, or booking subsystems by itself.

2. **`operator_workflow_intent` does not execute supplier logic.**  
   Writing or idempotently re-writing **`operator_workflow_intent`** (including **`need_supplier_offer`**) **must not** call supplier code paths, message suppliers, enqueue RFQ fan-out, mutate bridges, or perform any other **supplier-impacting** side effect. Persistence of intent and audit fields is **not** “supplier execution.”

3. **Supplier interaction must be a separate future layer.**  
   Any future work that **targets suppliers** (Telegram, RFQ broadcast, new visibility rules, nudges, offer workflows) must be **designed and implemented** as its **own** slice, with its own **permissions**, **idempotency**, and **tests**—not as an implicit follow-on to **`POST /admin/custom-requests/.../operator-decision`**.

4. **No side-effect classes from this layer (non-exhaustive, all forbidden as automatic consequences of intent save):**  
   - Supplier **messages** (Telegram or other)  
   - **RFQ** automation (broadcast, re-open, re-rank) beyond **existing** product rules that were already in place **without** this intent as trigger  
   - **`custom_request_booking_bridges`** creation/updates  
   - **Bookings, orders, payments, tours**  
   - **Mini App** list/detail, customer-visible state, or **customer notifications** for intent  
   - **`supplier_offer_execution_links`** mutation or customer “direct book” side effects from intent  
   - **Identity bridge** or session semantics  

5. **Future supplier logic must consume intent as input only; never be triggered directly by intent setting.**  
   If a later implementation **uses** `operator_workflow_intent`, it must treat the stored value as **read-only input** to **separately invoked** actions (e.g. a dedicated operator or admin “notify” with confirmation, a scheduled job with explicit policy, or a **new** API whose contract is **not** the intent-write endpoint). **Prohibited:** coupling such that `operator-decision` or any **intent-only** handler **unconditionally** starts supplier/RFQ/bridge workflows.

6. **Current Y36 / Y37.2 / Y37.4 / Y37.5 behavior remains unchanged by this gate.**  
   This document **reaffirms** the accepted baselines: assignment semantics; mark-under-review; first/second intents; idempotency and actor rules. Y38 does **not** add new preconditions, new enum values, or new user-visible surfaces. Any **future** change to those areas requires a **separate** gate or ticket, not a silent reinterpretation of Y38.

---

## Out of scope (until explicitly gated and implemented)

- **Automatic** supplier contact or **notification** when intent becomes **`need_supplier_offer`** (or any value).  
- New **RFQ** marketplace rules, **bridge** rules, or **Layer A** booking/payment behavior **driven from** intent write paths.  
- **Customer** or **supplier** visibility of raw **`operator_workflow_intent`** values outside **admin/ops** policies defined elsewhere.  
- This gate **does not** specify **concrete** future supplier features; it only defines **separation of layers** and **forbidden** trigger semantics.

---

## Post–Y38: explicit next step (no supplier implementation in this line)

**This section is the canonical “what next” for production continuity. Do not infer a different order from other docs.**

| Order | What | What **not** |
|------|------|--------------|
| **1 — Now** | **Layer C (Y36 / Y37.2 / Y37.4 / Y37.5)** is the **current** completed operator workflow: assignment, `open` → `under_review`, persisted **`operator_workflow_intent`**. | Do **not** add supplier sends, RFQ jobs, customer notifications, or any execution in **`operator-decision`**. |
| **2 — Y38 (this doc)** | **Document** the boundary: intent is **stored decision**, not trigger, not executor. | Do **not** treat Y38 as an implementation task for a supplier or RFQ feature. |
| **3 — Before any `app/` supplier automation** | Open a **new** design gate and ticket for the **first** supplier-interaction (or RFQ) slice, with: explicit **entry point** (not `POST .../operator-decision`); how **`operator_workflow_intent`** may be **read**; permissions; idempotency; tests. | Do **not** couple that slice to **writes** in the intent handler; do **not** auto-run on intent set. |
| **4 — Interim (operations)** | Commercial and ops work that **does not** change code continues to use **existing** tools (e.g. manual supplier contact, existing RFQ flows as already shipped) **outside** this operator-intent automation. | Do **not** use “we need a supplier offer” in admin as justification to bypass this gate. |

**Summary:** The **next product-engineering** step in-repo is **not** “implement supplier layer.” It is: **(a)** keep Layer C as-is, **(b)** when a supplier-layer feature is **ready to be specified**, add a **separate** design doc + `CURSOR` prompt + minimal PR scope **before** writing supplier-facing or intent-triggering code. Until then, **no** new supplier interaction logic in Tours_BOT is authorized by this architecture.

Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when the Y38 gate is accepted or the post–Y38 next-step is revised.

---

## Gate maintenance (product/engineering)

1. **Accept** this gate as the documentation baseline for Y38 when the team align on the post–Y38 table above.  
2. **Revisit** this file if a **future** ticket proposes reading **`operator_workflow_intent`** on a new surface — the **read** must remain **uncoupled** from intent **writes** (separate code paths, separate tests).  
3. **Do not** treat **`need_supplier_offer`** as an automatic nudge, DM, or RFQ event from existing endpoints.

---

## Summary

| Topic | Y38 stance |
|--------|------------|
| **Layer C operator workflow** | Decision/coordination only. |
| **`operator_workflow_intent`** | Data for ops; not an execution or supplier trigger. |
| **Future supplier/RFQ work** | Separate layer; may **read** intent; must not **auto-run** on intent set. |
| **Y36 / Y37.2 / Y37.4 / Y37.5** | Unchanged by this document. |
