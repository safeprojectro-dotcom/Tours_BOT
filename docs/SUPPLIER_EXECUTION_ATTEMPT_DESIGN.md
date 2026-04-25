# Supplier execution attempt — design (Y47)

**Phase:** Y47 — design only (documentation). **No** runtime code, migrations, new APIs, workers, supplier messaging, or tests in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38)  
- [`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md) (Y39)  
- [`docs/SUPPLIER_EXECUTION_FLOW.md`](SUPPLIER_EXECUTION_FLOW.md) (Y40)  
- [`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`](SUPPLIER_EXECUTION_DATA_CONTRACT.md) (Y41)  
- [`docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md`](SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md) (Y42)  
- [`docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md`](SUPPLIER_EXECUTION_TRIGGER_DESIGN.md) (Y45)  
- Y46: **safe admin trigger** exists (`POST /admin/supplier-execution-requests`); it creates **`supplier_execution_request`** only.

**Purpose:** Define the **execution attempt** as a **separate layer** from the **execution request** and the **Y46 trigger**: what an attempt **means**, how it **lifecycles** (logically), what it **holds**, what it **must not** do without a **future explicit gate**, and how it **relates** to Y40 stage 4. This file does **not** implement outbound messaging or external I/O.

---

## 0. Why attempts must be separated from the trigger (Y46)

| Layer | Role |
|-------|------|
| **Execution request** (`supplier_execution_request`) | **Intention and audit anchor** for a **run**: *what* work is in scope, *who* opened it, *idempotency*, **validated** (or other) state. Created by the **Y46** **admin explicit** **trigger** only in the current product slice — **no** supplier **action** yet. |
| **Execution attempt** (`supplier_execution_attempt`) | **One try** to perform a **supplier-impacting** **step** (Y40 **stage 4**). This is where **outbound** or **side-effecting** work would **attach** in a **future** implementation—**not** in the Y46 **trigger** path. |

**If attempts were conflated with the trigger:** (1) every **idempotent** **request** create could be misread as “we already tried the supplier,” (2) idempotency and **audit** for **I/O** would mix with **idempotency** for **row** creation, (3) Y45/Y46 **safety** (“DB only, no contact”) would be violated, (4) Y38 **(intent ≠ execution)** and Y39 **(explicit entry)** would blur—**triggers** would implicitly **imply** **attempts**. **Separation** keeps **request** = *planned / allowed run*; **attempt** = *concrete try* with its own **permissions**, **entry**, and **outcome** when a **separate** ticket enables it.

---

## 1. What is an execution attempt?

- **One row** = **one** **try** to perform a **supplier interaction** (or a **reservation** of a try that will perform it when a **later** **gate** runs), **always** **scoped** to exactly **one** **`supplier_execution_request`** via **`execution_request_id`** (Y41 §2).  
- **Semantically:** it is the **unit of action** in Y40 **stage 4** (between **request** record and **result**), not a second **trigger** and **not** a replacement for Layer C **intent**.  
- **Retries** (future): typically **new** **attempt** rows with **incrementing** **`attempt_number`** for the same **request**, or a **documented** **update** policy per product—Y41 allows either; this doc only requires **traceable** **tries**.

**Relationship:** Many attempts **may** exist over time for one **request**; **at most one** “active” **outbound** try may be a **policy** **choice** in a **future** implementation (not required by this design).

---

## 2. Attempt lifecycle (logical)

These are **logical** **phases** for product and **audit**; the **persistence** **enum** in the **repo** may use a **subset** or **differing** **names** until a **migration** **aligns** (e.g. add **`in_progress`** to **`supplier_execution_attempt_status`** in a **future** ticket). Y47 **names** the **intended** **meaning**:

| Phase | Meaning |
|--------|--------|
| **Created** | The **attempt** **row** **exists** (inserted) and is **attributed** to a **request**; **outbound** work **has** **not** **necessarily** **started** (initial **persisted** `status` may **map** to **pending** in DB). |
| **Pending** | The **try** is **acknowledged** but **not** **actively** **performing** **external** I/O (e.g. **queued**, **awaiting** **worker**, or **internal** **prep** only). |
| **In progress** | **Outbound** or **long-running** **supplier-impacting** **work** is **in** **flight** (message **submit**, **API** **call** **in** **progress**) — **only** in a **future** slice that **implements** **that** **transport**; **not** in Y47. |
| **Succeeded** | This **try** **completed** **successfully** (terminal for **this** **attempt** **row**). |
| **Failed** | This **try** **ended** in **error** (terminal for **this** **attempt**); **retry** = **new** **attempt** **row** (or **policy**-defined **update**). |

**Current codebase note:** `SupplierExecutionAttemptStatus` may **not** **yet** **include** **`in_progress`**; a **future** **implementation** may **extend** the **enum** or **use** **combinations** of **fields** (`provider_reference` set vs **null**, **time** windows) **until** **in_progress** **exists**—**document** the **choice** in the **implementation** **ticket**. **`skipped`** (if present) remains valid for **no-op** / **deferred** **tries** per Y41.

---

## 3. Attempt responsibilities (what a row is for)

An **execution attempt** **should**:

- **Represent** **one** **execution** **step** (one **try**) **under** a **parent** **`supplier_execution_request`**.  
- **Hold** **channel** and **target** **metadata** — e.g. **`channel_type`**, **`target_supplier_ref`** (Y41).  
- **Store** **provider** **correlation** — **`provider_reference`** (message id, job id, etc.) when **I/O** **exists** (future).  
- **Store** **failure** **data** for **this** **try** — **`error_code`**, **`error_message`** (sanitized, **ops**-facing, not **customer** **notification**).  
- **Record** **`created_at`** (and any **future** **updated_at** if **added** by **policy**).

**Request vs attempt (separation, restated):**

- **Request** = **intention** / **run** **container** (validated **anchor**, **idempotency** at **request** level).  
- **Attempt** = **action** **try** (the **locus** of **outbound** **history** and **per-try** **outcome**).

---

## 4. What the attempt layer MUST NOT do (without a future explicit gate)

| Rule | Detail |
|------|--------|
| **Not** **created** **by** the **Y46** **admin** **trigger** | **`POST /admin/supplier-execution-requests`** **must** **only** **create/resolve** **`supplier_execution_request`**. **No** **attempt** **inserts** in **that** **handler**. |
| **Not** **created** **automatically** from **DB** **triggers** / **ORM** **events** on **intent** / **custom** **request** / **unrelated** **tables** | Y39 / Y42 **no** **hidden** **starters**; **attempts** **start** only from a **declared** **entry** in a **future** ticket (e.g. **admin** “**run** **attempt**,” **worker** **job** **with** **id**). |
| **Not** **run** (no **outbound** **I/O**) **without** a **separate** **product** + **code** **gate** that **cites** Y38–Y47 and **messaging**/**API** **policy** | Y47 is **design** **only**; **no** **implementation** here. |
| **Not** **imply** **operator-decision** or **Layer** **C** **writes** | **Unchanged** Y38. |

---

## 5. Future behavior (document only — not Y47 scope)

**When** **separately** **implemented** and **gated**, an **attempt** may **eventually**:

- **Send** a **supplier** **message** (Telegram, email, **etc.**) — only under **messaging** **design** + **tests**.  
- **Call** an **external** **API** (partner, **webhook** **outbound**) — only under **integration** **design**.  
- **Retry** (new **attempt** **row** or **policy**-based) — **idempotency** for **I/O** **must** **not** **duplicate** **irreversible** **effects** (Y40).  

**Y47** **does** **not** add **any** of the **above** to **`app/`**.

---

## 6. Alignment with Y40 / Y41 / Y42

- **Y40:** **Attempt** = **stage** **4**; **result** **recording** = **stage** **5** (may **update** **request** / **attempt** **rows**).  
- **Y41:** **Field** **list** for **`supplier_execution_attempts`**; **retries** = **traceable** **rows**.  
- **Y42:** **Who** may **create** or **progress** **attempts** = **separate** **from** “**record** **intent**”; **fail-closed**; **audit** **per** **try**.  
- **Y45** **/ Y46:** **Trigger** = **request** **row** **only**; **attempts** = **not** in **trigger**.

---

## 7. Hard constraints (Y47 acceptance)

This design **file** **does** **not** add:

- Supplier **messaging** **implementation**  
- **HTTP** / **API** **clients** to **suppliers**  
- **Workers** / **queues** (beyond **describing** they **may** **exist** **later**)  
- **Bookings** / **orders** / **payments**  
- **Mini** **App** **changes**  
- **`supplier_offer_execution_links`** **mutation**  
- **Identity** **bridge** **changes**  
- **Customer** (or **supplier**) **notification** **pipelines**  

**No** **changes** to **`POST .../operator-decision`**.

---

## 8. Next step (product/engineering)

1. **Accept** Y47 as the **attempt-layer** **design** **baseline**.  
2. **Next** **implementation** **ticket** (not Y47): **optional** **enum** / **field** **tweaks** for **`in_progress`**, **plus** a **single** **explicit** **entry** to **create** the **first** **attempt** **row** (**still** **no** **outbound** **messaging** if **scoped** as “**prep** **only**” or **`channel`=`none`/`internal`** with **no** **send**), or **outbound** **only** when **a** **dedicated** **messaging** **gate** **ships**.  
3. Update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when Y47 is **accepted** and when **attempt**-related **code** **merges**.

---

## Summary

| Topic | Y47 stance |
|--------|------------|
| **Attempt** | **One** **try**, **FK** to **`supplier_execution_request`**; Y40 **stage** **4** **unit** |
| **Lifecycle** | **Created** → **pending** → **in_progress** (future) → **succeeded** / **failed** (logical) |
| **Responsibilities** | **Channel**, **target**, **provider** **ref**, **errors**; **per-try** **audit** |
| **Forbidden (here)** | **Y46** **trigger** must **not** **create** **attempts**; **no** **auto** **creation**; **no** **I/O** **without** **next** **gate** |
| **Future** | **Message** / **API** / **retry** only in **future** **tickets** |
| **Separation** | **Request** = **intention**; **attempt** = **action** **try** |
