# Supplier messaging — result visibility, audit, and retry (Y51)

**Phase:** Y51 — **design only** (documentation). **No** application code, migrations, new HTTP routes, workers, or automatic retries in this document.

**Depends on:**  
- [`docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md`](SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md) (Y49)  
- [`docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md`](SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md) (Y47)  
- [`docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md`](SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md) (Y42)  
- Y50: first outbound implementation — `POST /admin/supplier-execution-attempts/{attempt_id}/send-telegram` (Telegram, admin explicit, idempotent), table **`supplier_execution_attempt_telegram_idempotency`** with **`UNIQUE` (`supplier_execution_attempt_id`, `idempotency_key`)**.

**Purpose:** After Y50, define what **ops/admin** (and, where product allows, **authorized operator**) **must** be able to **see** and **reconstruct** for a supplier messaging **attempt**, what **audit** **hardening** is required beyond raw attempt fields, and **how** **retry** may be introduced **without** automatic background sends, **without** Y38 / Y45 / Y47 / Y48 bypass, and **without** new customer/side-effect surfaces beyond this gate’s scope.

---

## 1. What admin/operator must see after a send (and on read of history)

A conforming **admin (or product-approved operator)** view of a **`supplier_execution_attempt`** that was used for Y50 Telegram send (or a future channel) must expose, at minimum:

| Area | What must be visible | Notes (Y50 baseline / gap) |
|------|------------------------|----------------------------|
| **Attempt outcome** | **`status`** (`pending` / `succeeded` / `failed`, etc.) | Already on `supplier_execution_attempt`. |
| **Provider correlation** | **`provider_reference`** (e.g. Telegram `message_id` as string) | Set on success in Y50; must appear in any **detail** DTO / UI that lists attempt outcomes. |
| **Failure** | **`error_code`**, **`error_message`** (sanitized, **ops**-facing) | Set on send failure in Y50. |
| **Target** | **Where** the message was addressed — for Telegram, **`target_supplier_ref`** (e.g. Telegram user id) after send | Y50 sets on success; read APIs must not omit for audit. |
| **Idempotency (send)** | **Proof** that a **deduplication** key was used for that logical send: either **“idempotency key recorded”** for this **(attempt, key)** in **`supplier_execution_attempt_telegram_idempotency`**, or an equivalent **explicit** flag in a **read** DTO. | The key lives in the idempotency table, not the attempt row; **read** surfaces should **not** make ops guess. |
| **Timestamps** | **When** the attempt row was **created** (`created_at`); for **outcome** time, Y50 updates attempt in place — **if** `updated_at` is **missing** on the model, a **future** implementation may add it **or** use **idempotency** row `created_at` as **“send completed at”** for success replays (document the chosen rule in the implementation ticket). | Y51 **recommends** a clear **“result recorded at”** semantically, either by **`updated_at`** on attempt, **or** a dedicated **timestamp** on success/failure, **or** the idempotency row `created_at` as defined by policy. |

**Read path:** listing **parent** `supplier_execution_request` with **nested** `attempts` (existing admin read) must continue to return these fields; **Y51** does **not** require a **new** public customer surface. **Idempotency key** is **per-send**; surfacing the **set** of keys or **at least** “send was idempotency-protected (yes/no)” is acceptable for a **first** read hardening slice, as long as **ops** can reconcile **replays** with **audit** questions.

---

## 2. Audit hardening (who / what / when / where / outcome)

Y42 already requires **initiator**, **entry**, **source entity**, idempotency at **request** level, and **attempt/result** state. Y50 added **outbound** **send** with **`X-Admin-Actor-Telegram-Id`** but **persistence** of **“who** **sent** **the** **Telegram**” may be **incomplete** if only the **header** is validated. **Y51** **locks** the **audit** **minimums** for **messaging** **specifically**:

| Audit element | Requirement |
|---------------|-------------|
| **Who sent** | **Durable** link to an **internal** **identity** (e.g. **`users.id`** of the **admin** **actor** who called the send endpoint). If **not** yet stored, **next** **implementation** **slice** should **add** **`sent_by_user_id`** (or **equivalent** on attempt or **append-only** **audit** **subtable**) **or** a **redacted** **log** **pointer** (Y42 “capturable” standard). **Must** **not** rely on **“who** **owns** **the** **RFQ**” **alone** for “who caused the send.” |
| **When** | **Clock** time of **outcome** and, if distinct, **when** the **send** was **acknowledged** (see §1 timestamps). |
| **Which endpoint** | **Literal** name or stable **operation** **id** — e.g. **`POST` …/send-telegram** — in **ops** **docs** and, where product agrees, in **structured** **audit** (not necessarily in every DTO for customers). |
| **Target** | **Channel**-appropriate **ref** (Telegram: **chat** / **user** **id** as stored in **`target_supplier_ref`**). |
| **Result** | **Succeeded** vs **failed**; **`provider_reference`** on success. |
| **Failure reason** | **`error_code`** + **`error_message`** (or machine-readable + short human) **without** leaking **PII** into **default** **customer** **channels** (Y42). |

**Fail-closed (audit):** if **“who** **sent**” **cannot** be **reconstructed** from **DB**+**logs**, treat as **Y51** **implementation** **debt** until fixed; do **not** add **new** **send** **paths** that **bypass** **actor** **attribution**.

---

## 3. Retry principles (no automatic product retry in Y51)

| Principle | Stance |
|-----------|--------|
| **No automatic retry yet** | **No** **worker**, **no** **cron**, **no** **ORM**-**hooked** **re-delivery** of **Telegram** **(or** **other** **channel**)** for **failed** **attempts** as **part** **of** **Y51** **or** **without** a **later** **ticket**. |
| **Manual retry only after explicit future gate** | A **new** **admin**-**facing** **or** **ops**-**facing** **“retry** **send**” (or **“new** **attempt**”) must be its **own** **product**+**code** **gate** — e.g. **Y52+** — that **cites** **Y49**, **Y50**, and **this** **doc**. |
| **Idempotency on retry** | A **new** **send** (whether **new** **attempt** **row** per Y47 or **allowlisted** **policy** to **re-open** a **flow**) must use a **new** **idempotency** **key** **or** **documented** **replay** **semantics** (same key **only** **returns** **prior** **outcome** — **as** in Y50 **idempotency** **table**; **not** a **second** **Telegram** **message** **unless** **explicitly** **designed**). |
| **Failed attempt must not silently resend** | **Updating** a **failed** **row** **in** **place** to **succeeded** **without** a **new** **explicit** **send** **operation** (or **without** an **idempotent** **replay** of the **same** **logical** **send**) is **forbidden**. **“Fix”** by **new** **attempt** **(preferred** **per** **Y47)** **or** a **dedicated** **admin** **action** with **its** **own** **idempotency** **scope** **(implementation** **ticket**). |

**Y47** **remains:** **retries** are often **new** **`attempt_number`** **rows**; if **only** one **pending** **attempt** per **request** is allowed at a time, that is **product** **policy** — **Y51** only requires **traceability** and **no** **hidden** **retry**.

---

## 4. Forbidden (Y51 scope boundary)

Y51 **as** a **document** does **not** **authorize** (and **future** **code** must **refuse** **unless** a **separate** **gate** **says** **otherwise**):

- **Auto**-**retry** **workers** (queues, **Celery**, **nightly** **jobs**) **driving** **supplier** **Telegram** **sends** **from** **failed** **attempts**.  
- **Hidden** **retry** **on** **read** (e.g. **GET** or **“load** **detail**” **re**-**invoking** **send**).  
- **Retry** (or **first** **send**) **triggered** from **Y46** request **creation** or **replay**, **Y48** **attempt** **row** **insert** **alone**, **`operator_workflow_intent`**, or **`POST` …/operator-decision** — **Y38** / **Y45** / **Y47** / **Y49** **unchanged** **in** **meaning**.  
- **Customer** **notifications** **as** a **default** **side** **effect** of **messaging** **result** (out of this doc).  
- **Booking** / **order** / **payment** **mutation**, **Mini** **App** **changes**, **execution** **link** or **identity** **bridge** **changes** in the **name** of **messaging** **audit** **or** **retry**.  
- **Fan**-**out** **(one** **send** **operation** **→** **many** **suppliers**)** **without** **explicit** **policy** and **eligibility** (align Y49).  

---

## 5. Next safe implementation (Y51+; not in this file)

1. **Read** **visibility** / **admin** **DTOs** (and, if in scope, **Telegram** **admin** **copy**): **ensure** **§1** **fields** **+** **§2** **“who** **sent**” **(if** **missing**)** are **exposed** **consistently**; **idempotency** **“present** **/ **keys**” per **Y50** **table** or **summary** field **as** **agreed** in a **small** **ticket**.  
2. **Optional** **migrations** **only** **when** **needed** (e.g. **`sent_by_user_id`**, **`updated_at`**, or **send**-**outcome** **timestamps** on **`supplier_execution_attempt`**) — **cited** **Y41**+**Y42**+**this** **doc**.  
3. **No** **automatic** **retry** **in** **the** **same** **PR** as **read** **polish** **unless** the **PR** is **explicitly** **scoped** **and** **rejected** **by** default — **Y51** **recommends** **retry** **as** a **separate** **Y52+** **gate** **(manual** **or** **policy**-**driven** **only**)**.  

**Continuity:** update [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) and [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) when Y51 is **accepted** and when a **Y51**+ **read** **/ **audit** **slice** **merges**.

---

## Summary

| Topic | Y51 stance |
|-------|------------|
| **Visibility** | **Status**, **provider_reference**, **errors**, **target**, **timestamps**; **idempotency** for send **not** **hidden**; **reconstructable** from **read** **APIs** or **docs**+**DB**. |
| **Audit** | **Who**, **when**, **endpoint**, **target**, **result**, **failure** **reason** — extends **Y42** for **Y50**-class **sends**; **no** **silent** **actor**. |
| **Retry** | **Not** **automatic**; **future** **gate**; **new** **idempotency** **or** **defined** **replay**; **no** **silent** **resend** of **failed** **attempts**. |
| **Forbidden** | **Workers** / **hidden** **retry** / Layer C **or** request/**attempt**-**only** **triggers**; **customer** **blast**; **booking** / **Mini** **App** / **execution** **links** / **identity** **bridge**; **fan**-**out** **without** **policy**. |
| **Next** | **Harden** **read**+**persistence** **for** **§1**–**§2**; **no** **auto**-**retry** **by** **default**. |
