# Supplier outbound messaging — design gate (Y49)

**Phase:** Y49 — design only (documentation). **No** application code, migrations, new HTTP routes, workers, or live sends in this document.

**Depends on:**  
- [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) (Y38)  
- [`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md) (Y39)  
- [`docs/SUPPLIER_EXECUTION_FLOW.md`](SUPPLIER_EXECUTION_FLOW.md) (Y40)  
- [`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`](SUPPLIER_EXECUTION_DATA_CONTRACT.md) (Y41)  
- [`docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md`](SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md) (Y42)  
- [`docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md`](SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md) (Y47)  
- Y45–Y48: request + attempt **persistence** and **admin** **surfaces** exist; **Y48** creates **`pending`** **attempts** with **`channel`=`none`** — **not** an outbound **send**.

**Purpose:** Define **outbound** **supplier** **messaging** as the **first** **irreversible** **external** **side** **effect** in the **supplier** **execution** **stack**, and **lock** where it may **attach**, what **preconditions** apply, and what is **forbidden** until a **separate** **implementation** **ticket** **explicitly** **ships** **sends**.

---

## 0. Why outbound messaging is the most dangerous step

| Risk | Why it matters here |
|------|----------------------|
| **Irreversibility (practically)** | A **sent** message **reaches** a **real** **supplier** **surface**; recall/repair is **best-effort** or **impossible** — unlike **rolling** **back** a **DB** **row** in **dev** / **low** **user** **count** **scenarios**, production **trust** and **reputation** **burn** on **errors**. |
| **Idempotency** | Wrong **deduplication** **duplicates** **spams** or **contradictory** **nudges**; too **aggressive** **dedup** may **block** a **valid** **follow-up** — must be **proven** **per** **channel** and **use** **case**. |
| **Blast** **radius** | A **bug** in **one** **path** can **message** the **wrong** **supplier** or the **right** **supplier** with **wrong** **content** (PII, **wrong** **tour/RFQ** **context**). |
| **Coupling to Layer C** | If **messaging** is **implicitly** **tied** to **`operator_workflow_intent`**, Y38 is **void**; **if** **tied** to **request** **create** or **Y46** **trigger** **alone**, Y45 **separation** is **void**. |
| **Audit / compliance** | **Who** **authorized** **what** **to** **whom** **when** must be **reconstructable** — **messaging** **without** **audit** is **unacceptable** in **ops**-heavy **RFQ** **workflows**. |

**Therefore:** this **doc** **treats** **messaging** as a **gated** **sub-capability** **inside** the **execution** **attempt** **line**, **not** a **by-product** of **data** **entry** or **Layer** **C** **intent**.

---

## 1. What outbound supplier messaging is (in this architecture)

- **Real** **supplier** **contact** over an **agreed** **channel** (see §5), with **content** and **recipients** **chosen** (or **validated**) by **authorized** **logic** **after** **explicit** **preconditions** (§3).  
- The **first** **genuine** **external** **side** **effect** in the **Y40** **pipeline** that **reaches** **outside** the **platform**’s **DB** + **internal** **admin** **UIs** — **not** the same as **inserting** **`supplier_execution_request`** (Y45/Y46) or **`pending`** / **`none`**-**channel** **`supplier_execution_attempt`** (Y48).  
- **Not** the same as **storing** **Layer** **C** **intent** or **ops** **notes**; **not** a **customer** **notification** (customer paths are **out** **of** **scope** **unless** a **separate** **product** **gate** **says** **so**).

---

## 2. Where messaging belongs (placement rules)

| Location | **Outbound** **messaging** **allowed?** |
|----------|----------------------------------------|
| **`supplier_execution_attempt`**-**scoped** **logic** (the **only** **approved** **anchor** in this design) | **Yes** — **only** as a **future** **implementation** that **performs** **send** **after** **checks** in §3; **update** or **sub-step** on an **existing** **attempt** **row** (or a **dedicated** **“execute** **outbound**” **step** **bound** to **one** **attempt** **id**) — **TBD** in an **implementation** **ticket** **that** **cites** **this** **doc**. |
| **Y45** / **Y46** **`supplier_execution_request` creation** (admin **trigger**) | **No** — **request** = **intention** / **idempotency** / **context**; **no** **contact**. |
| **`POST` … request** / **idempotent** **replay** of **create** | **No**. |
| **`POST` … attempts** with **Y48** **semantics** (**row** **create** **only**, **`none`** / **`pending`**) | **No** **send** by **that** **endpoint** **alone** — **attempt** **creation** **is** **not** **authorization** to **message** (Y47, Y48). **Actual** **send** requires **an** **additional** **explicit** **entry** in a **future** **slice** (see §4). |
| **Layer** **C** **`operator_workflow_intent`**, **`operator-decision`**, **RFQ** **row** **writes** | **No** (Y38) — **intent** is **data**, **not** a **messenger** **trigger**. |

**Rule of thumb:** **if** a **line** of **code** would **emit** a **message** when **the** **only** **input** is “**intent** **changed**” or “**request** **created**” or “**attempt** **row** **inserted** **via** **Y48**” **with** **no** **further** **guards**, that **line** is **not** **allowed** by this design.

---

## 3. What messaging MUST require (preconditions, non-negotiable)

A **conforming** **future** **implementation** **that** **sends** must **satisfy** **all** of:

1. **Explicit** **attempt** **context**  
   A **durable** **`supplier_execution_attempt`** (or a **strictly** **1:1** **sub-record** **policy** **approved** in the **same** **gate** as **code**) **identifies** **this** **try**. **No** “floating” **send** **without** **attempt** **id** in **internal** **audit** **path**.

2. **Explicit** **permission** (Y42)  
   **Central** **admin** / **policy-defined** **operator** / **system** / **integration** **identity** — the **same** **classes** as **Y42** **initiators**, **not** “**anyone** **who** **can** **write** **intent**.” A **separate** **bit** or **role** for “**may** **cause** **supplier** **outbound**” **should** be **assumed** **unless** a **narrower** **exception** is **product-approved**.

3. **Idempotency** for **sends**  
   A **client**-**supplied** or **server**-**derived** **key** or **(attempt_id,** **operation,** **dedupe** **version)** **tuple** that **prevents** **duplicate** **sends** **under** **retries** and **at-least**-**once** **delivery** **semantics** — **designed** **per** **channel** in the **implementation** **ticket** (see §6).

4. **Audit** **trail**  
   **Who** / **what** **job** **invoked** **send**; **when**; **target**; **raw** or **redacted** **content** **reference** (Y41 `provider_reference` / **log** **pointer**); **outcome** **or** **error** on **`attempt`** **(and** **if** **needed,** **request**)**. **No** **silent** **sends**.

These **are** **design** **requirements**; **Y49** does **not** add **endpoints** or **transport** **code**.

---

## 4. What messaging MUST NOT be

| Prohibited pattern | Rationale |
|--------------------|-----------|
| **Automatic** **send** on **timer**, **row** **change**, **ORM** **event**, or **“intent** **=** **need_supplier_offer**” | Y38, Y39, Y47 |
| **Triggered** **directly** by **`operator_workflow_intent`**, **`operator-decision`**, or **any** **handler** that **only** **persists** **intent** | Y38 #5 |
| **Triggered** **by** **Y46** **request** **creation** **or** **replay** | Y45, Y47 |
| **Triggered** **solely** by **Y48** **attempt** **row** **insert** ( **`none`** / **`pending`** ) | Y47, Y48 — **row** = **reservation** / **plumbing**; **not** **=** “**ship** **now**” **unless** a **separate** **“execute** **outbound**” **step** **exists** and **passes** **§3** |
| **Hidden** **DB** **triggers** on **`custom_marketplace_requests`** or **other** **tables** | Y39, Y42 |
| **Customer**-**facing** **“your** **RFQ** **was** **sent** **to** **suppliers**” **as** a **default** | Out of this **doc**; **separate** **product** / **legal** / **comms** **gate** |
| **Broadcast** to **unbounded** **supplier** **sets** **without** **explicit** **policy** and **eligibility** **checks** | **Safety** / **spam** / **compliance** |

---

## 5. Allowed **future** channel families (illustrative; not implemented here)

| Channel (logical) | Role | Notes for **first** **implementation** **slices** |
|-------------------|------|------------------------------------------|
| **Telegram** | **Primary** in-repo **path** for **approved** **suppliers** (Y2+ **onboarding** **truth**) | **Must** **resolve** **binding** **/** **chat** **id**; **respect** **block** / **opt-out** **if** **policy** **exists** |
| **Email** | **Optional** **parallel** for **certain** **B2B** **contacts** | **SPF**/**DKIM**/**templates** = **separate** **ops**; **PII** **minimization** |
| **Partner** / **API** (HTTP **webhook** **out** or **message** **queue** **out**) | **Integration**-grade; **mTLS** / **HMAC** **/** **API** **key** = **TBD** | **Idempotency-Key** **headers** or **message** **dedup** **ids** |

**Enum** **alignment:** Y41 `SupplierExecutionAttemptChannel` already **includes** `telegram`, `email`, `partner_api`, `internal`, `none`. **Y48** **uses** `none` **until** **this** **gate**+**implementation** **choose** a **real** **channel** for a **real** **send**. **`internal`** may **denote** “**only** **platform**-**internal** **side** **effects**” and **is** **not** **by** **itself** **supplier** **messaging** — **naming** in **implementation** **must** **not** **confuse** **ops**.

---

## 6. Safety: retries, failure, and “no duplicate sends” (future implementation rules)

| Topic | **Design** **stance** (implementation **must** **detail**) |
|-------|--------------------------------|
| **Retry** | **Distinguish** **transport** **retry** **(same** **logical** **send,** **safe** **idempotent** **re-post)** from **“** **new** **try**” **(new** **`attempt`/`attempt_number`**) per **product**; **exponential** **backoff** / **DLQ** for **workers** **if** **used** |
| **Failure** **recording** | **Persist** **`error_code`**, **`error_message`** (and **optional** **provider** **payload** **ref**) on **`supplier_execution_attempt`**; **link** to **request**-**level** **terminal** **state** only **per** **Y41** **/** **next** **slice** — **this** **doc** does **not** **mandate** **request** **=** **failed** on **one** **failed** **message** **attempt** **without** **policy** |
| **No** **duplicate** **sends** | **Idempotency** **key** **scope** must **cover** **(who,** **what** **template,** **what** **request** **entity,** **what** **window)**; **replay** of **the** **same** **idempotent** **create** must **not** **double**-**message**; **at-least**-**once** **consumers** must **de-dupe** **inbound** or **outbound** **ACK** per **Y40** **retry** **safety** |
| **Rate** **limits** / **abuse** | **Per-supplier** and **per-run** **limits** = **TBD** in **implementation**; **default** should **favor** **deny** when **over** **limit** |

**Y49** does **not** add **retry** **workers** or **queues**; it **only** **states** that **they** must **obey** **the** **above** **if** **introduced**.

---

## 7. Hard constraints (Y49 acceptance of **this** **file**)

Y49 **as** a **document** does **not** authorize:

- **Any** **code** **change** **or** **send** in **`app/`**  
- **Real** **Telegram** / **email** / **HTTP** **calls** **from** **this** **PR** / **this** **doc** **alone**  
- **Bookings,** **orders,** **payments,** **RFQ** **logic** **beyond** what **already** **exists** **without** **this** **messaging** **layer**  
- **Mini** **App,** **execution** **links,** **identity** **bridge** **mutation**  
- **Default** **customer** **notifications** **driven** from **messaging** **(supplier)** **outcomes**  
- **Workers** or **infrastructure** **in** the **Y49** **deliverable** **itself** — **only** **design** **text**

---

## 8. Relationship to Y40 / Y41 / Y47 / Y48

- **Y40** **stage** **4** **=** the **locus** where **outbound** **would** **execute**; **Y49** **specializes** **that** **for** **messaging** **+** **API**-**like** **channels** **only** **with** **§2–4** **invariants**.  
- **Y41** **attempt** **fields** **(`provider_reference`,** **`error_*`)** are **the** **natural** **home** for **message** / **API** **correlation** **ids** **and** **errors**.  
- **Y48** **remains** **row**-**level** **plumbing** **without** **send**; **Y50+** (or **named** **slice**) may **add** “**commit** **outbound**” **API** that **cites** **Y49** **+** **Y42**.

---

## 9. Next step (product/engineering)

1. **Accept** **Y49** as the **gating** **design** for **any** **first** **supplier** **outbound** **messaging** **implementation** **in** **app/**.  
2. **Next** **implementation** **ticket** (not Y49): **narrow** **slice** for **one** **channel** (e.g. **Telegram** **to** **one** **approved** **supplier** **profile**), **explicit** **entry**, **Y42** **RBAC**, **idempotency**, **append-only** **audit**, **no** **customer** **fan**-**out** **by** **default**; **cites** **Y38**–**Y49**.  
3. **Update** [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when **Y49** is **accepted** in **continuity** **and** when **a** **messaging** **slice** **merges** **or** **fails** **a** **review** **(revise** **gate**).

---

## Summary

| Topic | Y49 stance |
|--------|------------|
| **What** it **is** | **Real** **supplier** **contact**; **first** **external** **irreversible** **effect** in this **stack** |
| **Where** | **Only** **in** **attempt**-**tied** **outbound** **logic**; **never** **trigger** / **request** **create** / **intent** **alone** / **Y48** **row** **alone** |
| **Must** **have** | **Explicit** **attempt** + **permission** + **idempotency** + **audit** |
| **Channels** (future) | **Telegram**, **email**, **partner** **API** — **separate** **hardening** per **channel** |
| **Safety** | **No** **dup** **sends**; **failure** **on** **attempt**; **retry** **rules** TBD in **code** **ticket** |
| **Forbidden** in **Y49** | **Implementation**, **sends**, **workers** **as** part of this **file**; **bypass** of Y38 / Y45 / Y47 / Y48 |
