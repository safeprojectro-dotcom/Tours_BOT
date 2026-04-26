# Supplier messaging — manual retry (Y53)

**Phase:** Y53 — **design only** (documentation). **No** application code, migrations, new HTTP routes, workers, or automatic retries in this document.

**Depends on:**  
- [`docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md`](SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md) (Y49)  
- [`docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md`](SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md) (Y51)  
- [`docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md`](SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md) (Y47)  
- Y50: `POST /admin/supplier-execution-attempts/{attempt_id}/send-telegram` (first send).  
- Y52: read/audit visibility on attempts (idempotency evidence, `outbound_telegram_operation`, etc.).

**Purpose:** Define **manual** **retry** for **supplier** **outbound** **messaging** as an **explicit** **admin**-**only** **decision**, with a **clear** **retry** **model**, **preconditions**, **audit** **minimums**, and **forbidden** **patterns**. This **gate** **must** be **accepted** **before** any **implementation** **ticket** adds a **“retry** **send**” **or** **“new** **attempt** **for** **retry**” **flow**.

---

## 1. Manual retry principle

| Rule | Y53 stance |
|------|------------|
| **Explicit admin action** | A **retry** is **only** **valid** when **invoked** by an **authorized** **admin** (**or** **product**-**approved** **operator**, if a **future** **policy** **extends** **Y42**) through a **declared** **entry** (e.g. **dedicated** **admin** **HTTP** **route** or **equivalent** **explicit** **UI** **action**), **not** as a **side** **effect** of **other** **work**. |
| **No automatic retry** | **No** **workers**, **no** **cron**, **no** **queue** **drain**, **no** **“heal** **failed** **after** **N** **minutes**” **without** **human** **or** **explicit** **ops** **intent** **in** **this** **product** **line**. |
| **No hidden retry on read** | **GET** **/ **list** **/ **detail** **must** **not** **call** **Telegram**, **must** **not** **mutate** **attempts**, **must** **not** **create** **sends** **(Y51** **unchanged**)**. |
| **No retry from request/attempt creation** | **Y46** **request** **create**, **Y48** **`POST` …/attempts** **(row** **create** **only**)** **must** **not** **imply** **or** **schedule** **a** **retry** **or** **a** **send**; **retry** **is** **a** **separate** **step** **after** this **gate** **(Y45** **/** **Y47** **separation**)**. |

**Alignment:** **Layer** **C** **`operator_workflow_intent`** and **`operator-decision`** **must** **not** **trigger** **retry** **(Y38** **/** **Y49**); **intent** may **only** be **context** on the **parent** **request** **snapshot**, **not** a **messenger** **or** **retry** **signal**.

---

## 2. Retry model (data + idempotency)

| Topic | Y53 **preferred** **/ **default** **model** |
|-------|----------------------------------|
| **In-place resend of a failed row** | **Not** **default**. **Do** **not** **re**-**invoke** **`send-telegram`** **on** the **same** **attempt** **row** **by** **clearing** **failure** **and** **re**-**posting** **without** **a** **product**-**approved** **exception**—**preserves** **one** **row** = **one** **try** **history** **(Y47**)**. |
| **New attempt for retry** | **Preferred:** **create** a **new** **`supplier_execution_attempt`** **row** (**next** **`attempt_number`**) **under** the **same** **`supplier_execution_request`**, then **use** the **existing** **Y50** **send** **endpoint** (or a **successor** **channel** **abstraction**) **on** that **new** **attempt** **id** **when** **pending** **and** **policy** **allows**. **Traceability:** **link** **original** **↔** **retry** **in** **audit** **(see** **§4**)**. |
| **Each retry send = new idempotency key** | **Every** **new** **logical** **outbound** **send** **must** **use** a **client**-**supplied** **(or** **server**-**agreed**)** **idempotency** **key** **scope** **for** **that** **attempt**—**as** in **Y50** **(`UNIQUE` **(attempt_id,** **idempotency_key)**). **The** **retry** **is** a **new** **send** **→** **new** **key** **required**. |
| **Same key = replay** | **Unchanged** **from** **Y50:** **re**-**POST** **with** the **same** **(attempt_id,** **idempotency_key)** **must** **not** **duplicate** **Telegram** **delivery**; **returns** **prior** **outcome** **(idempotency** **row** **on** **success**)**. |

**Concrete ordering (illustration, not implementation):** **failed** **attempt** **A** **→** **admin** **creates** **attempt** **B** **(pending,** **channel** **none**)** **→** **admin** **calls** **send-telegram** **on** **B** **with** **new** **idempotency** **key** **and** **confirmed** **target** **+** **text** **(§3)**.

---

## 3. Preconditions (before a manual retry may be allowed)

A **conforming** **future** **implementation** **should** **enforce** (fail-closed if unmet; exact checks in the implementation ticket):

1. **Original / prior attempt** — **Status** **is** **retry**-**eligible** **per** **product** **policy** **(typically** **`failed`** **for** **Telegram** **send** **failure;** **not** **`succeeded`** **without** **policy** **exception**). **Skipped** **/** **cancelled** **may** be **excluded** **unless** **product** **defines** **otherwise**.
2. **Parent request** — **`supplier_execution_request`** **still** **valid** **for** **a** **new** **attempt** **(Y48**-**style** **rules**:** **e.g. **not** **terminal** **blocked** **/** **cancelled** **unless** **policy** **allows** **override**). **Source** **entity** **must** **still** **exist** **and** **be** **eligible** **if** **required** **by** **Y42**/**Y46** **checks**.
3. **Admin permission** — **Caller** **passes** **Y42**-**class** **initiation** **rules** **(central** **admin** **or** **policy**-**allowed** **operator**); **not** **“intent** **only**”**.
4. **Target** **re**-**confirmed** — **Retry** **must** **not** **silently** **reuse** **a** **cached** **chat** **id** **without** **an** **explicit** **field** **in** **the** **retry** **/ **send** **payload** **(product** **may** **default**-**suggest** **but** **must** **require** **confirmation** **for** **this** **gate**). **Aligns** **Y49** **blast**-**radius** **concerns**.
5. **Message** **text** **re**-**confirmed** — **No** **auto**-**repost** **of** **a** **prior** **body** **without** **an** **explicit** **user**-**or**-**ops**-**supplied** **(or** **re**-**confirmed**)** **content** **step** **in** **the** **UI** **/** **API**.

**Optional product knobs** (TBD in implementation): **max** **attempts** **per** **request**, **cooldown** **windows**, **who** **may** **retry** **after** **N** **failures**.

---

## 4. Audit (minimums for a manual retry)

When a **manual** **retry** **is** **initiated** **and** **when** a **new** **send** **executes**, the **system** **must** **be** **able** **to** **reconstruct** **(Y42** + **Y51** + **this** **section**):

| Field / concept | Required semantics |
|-----------------|--------------------|
| **`original_attempt_id`** | The **prior** **attempt** **row** **being** **retried** **from** **(or** **“correlation** **anchor**”** if** **policy** **uses** **request**-**level** **link** **only**)**. |
| **`retry_attempt_id`** | The **new** **(or** **current**)** **attempt** **row** **on** **which** **the** **retry** **send** **is** **bound** **(Y50** **send** **path**). |
| **`retry_requested_by`** | **Internal** **identity** **(e.g.** **`users.id`** **from** **`X-Admin-Actor-Telegram-Id`** **or** **equivalent**)** **at** **the** **time** **of** **the** **retry** **decision** **(create** **attempt** **/** **dedicated** **retry** **endpoint**)**. |
| **`retry_reason`** | **Short** **free**-**text** **or** **enum** **(ops**-**facing**)** **why** **retry** **was** **needed** **(e.g.** **“rate** **limit**”,** **“wrong** **target**”**)** **—** **implementation** **may** **store** **on** **request** **audit_notes**, **a** **dedicated** **column**, **or** **append**-**only** **log** **reference** **as** **scoped** **in** **the** **ticket**. |
| **Timestamp** | **Clock** **time** **of** **retry** **request** **/** **attempt** **creation** **(and** **send** **outcome** **time** **via** **existing** **attempt** **/** **idempotency** **rows** **as** **in** **Y50**/**Y52**)**. |
| **Idempotency** **key** | **The** **key** **used** **for** **the** **retry** **send** **(per** **attempt,** **Y50**). |

**Storage shape** is **TBD** in an **implementation** **ticket** **(migrations** **optional**); **Y53** **requires** **the** **semantics** **to** **exist** **or** **be** **intentionally** **deferred** **with** **a** **recorded** **debt** **item** **(fail**-**closed** **default**). **Linking** **original** **→** **retry** **may** use **a** **dedicated** **column** on **`supplier_execution_attempt`**, a **separate** **link** **table**, **or** **structured** **`audit_notes`** **if** **product** **accepts** **weaker** **queryability** **(must** **be** **explicit** **in** **the** **ticket**).

---

## 5. Forbidden (Y53 boundary)

Y53 **as** a **document** does **not** **authorize** (and **code** must **refuse** **unless** a **later** **explicit** **implementation** **gate** **says** **otherwise**):

- **Background** **retry** **worker** (any **unattended** **re**-**send** **driven** **by** **timers** **or** **queue** **drain** **without** **an** **explicit** **per**-**retry** **admin** **action** or **separately** **gated** **ops** **approval**).  
- **Retry** **by** **reading** a **detail** **page** **(GET** **load** **→** **send**).  
- **Retry** **driven** **by** **`operator_workflow_intent`**, **`POST` …/operator-decision**, **Y46** **request** **create**, or **Y48** **attempt** **create** **alone** **(no** **further** **explicit** **retry** **step**).  
- **Retry** **“without** **a** **new** **explicit** **admin** **action**” **(each** **retry** **send** **/ **new** **attempt** **for** **retry** **must** be **deliberate**).  
- **Default** **customer** **notifications** **for** **retry** **outcomes** (out of scope unless a **separate** **product** **gate**).  
- **Booking** **/** **order** **/** **payment** **mutation**, **Mini** **App** **changes**, **execution** **link** **or** **identity** **bridge** **changes** **as** part of **retry** **automation** **(align** **Y49** **/** **Y51**).  

---

## 6. Next safe implementation (not in this file)

1. **After** this **gate** is **accepted:** open an **implementation** **ticket** that **cites** **Y38**–**Y53** (as **applicable**), **Y50** **send** **contract**, and **Y52** **read** **DTOs**; **add** **either** **(a)** a **dedicated** **“create** **retry** **attempt**” **admin** **endpoint** **with** **audit** **fields**, **or** **(b)** **documented** **ops** **flow** using **Y48** + **Y50** **only** with **mandatory** **linkage** **in** **persistence** **/ **logs** for **`original_attempt_id` ↔ `retry_attempt_id`**.  
2. **Still** **no** **automatic** **retry** in **that** **ticket** **unless** **a** **separate** **dangerous**-**automation** **gate** **is** **opened**—**Y53** **default** **is** **manual** **/ **explicit** **only**.  
3. **Update** [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when **Y53** is **accepted** and when a **Y53+** **implementation** **merges** **or** **is** **superseded**.

---

## Summary

| Topic | Y53 stance |
|-------|------------|
| **Principle** | **Manual** **/** **explicit** **admin** **(or** **policy**-**gated** **operator**)** **only**; **no** **auto** / **hidden** / **create**-**path** **retry**. |
| **Model** | **New** **attempt** **preferred**; **new** **idempotency** **per** **send**; **Y50** **replay** **rules** **unchanged**. |
| **Preconditions** | **Eligible** **prior** **state**; **valid** **parent** **request**; **permission**; **re**-**confirm** **target** **&** **message**. |
| **Audit** | **original** **/** **retry** **ids**, **requester**, **reason**, **time**, **idempotency** **key** **(or** **documented** **debt**)**. |
| **Forbidden** | **Workers**; **read**-**time** **send**; **Layer** **C** **/** **Y46** **/** **Y48**-**only** **triggers**; **side**-**effect** **surfaces** **out** **of** **scope** **(booking** / **Mini** **App** **/** **links** **/** **bridge** / **default** **customer** **notify**). |
| **Next** | **Implementation** **ticket** **only** **after** **this** **design** **acceptance**; **no** **auto** **retry** **by** **default**. |
