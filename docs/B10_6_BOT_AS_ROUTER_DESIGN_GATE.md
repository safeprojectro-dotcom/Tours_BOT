# B10.6 — Bot-as-router design gate (docs only)

**Project:** Tours_BOT. **Status:** design gate — **no** code, **no** B11 route changes, **no** Mini App or booking changes in this step.

**Related:** [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) (B10.6) · [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md) · [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md) (recommended prerequisite).

---

## Purpose

Record **customer-facing** messaging and **product** choices for a future **B10.6** slice: Telegram **private** bot as **router/consultant** (short context + **deep link** into the **Mini App**), **not** a second catalog that duplicates **Mini App** execution truth (**`full_bus`**, pricing, availability).

This doc **gates** implementation until:

- **Admin/OPS** have a **stable, human-readable** conversion status vocabulary (see **C2B11A** proposal), **unless** product explicitly prioritizes **customer routing** first; and  
- **stakeholder** answers the **design questions** below.

---

## Current B11 behavior (summary)

- **Deep link:** Private **`/start supoffer_<supplier_offer_id>`** (and related entry paths documented in **`CHAT_HANDOFF`** / C2B9B) resolves through **`supplier_offer_execution_links`** and **catalog** visibility rules.
- **Happy path:** With an **active execution link** and an **`open_for_sale`** (catalog-visible) **Tour**, the bot can route the customer to the **exact** Mini App **Tour** (`/tours/{code}`), **skipping** generic catalog overview where that slice applies (see **OPEN_QUESTIONS** §24 / **Track 3**).
- **Hard separation:** **Showcase channel** = marketing; **Mini App** = **execution** truth (Layer A booking pipeline). The bot **must not** invent **readiness**; server **`GET …/review-package`** (for **ops**) and **B11** resolution code (for **customer**) remain authoritative for what is technically possible.

---

## Source-of-truth rules

| Layer | Role |
|--------|------|
| **Mini App** | **Execution** truth: **catalog** listing, **seats**, **full_bus**, **Layer A** booking/payment. |
| **Showcase / Telegram channel** | **Marketing** visibility — **published** post does **not** imply **bookable**. |
| **`Tour` + `open_for_sale`** | **Catalog-visible** — customer may see the tour in app catalog; still **not** “exact tour from offer” until **B11** path is satisfied where applicable. |
| **Execution link** | Binds **published offer** to **exact Tour** for **`supoffer_*`** style entry; **required** for that **deep** path. |
| **Bot (B10.6 target)** | **Router:** short explanation + **Open in app** CTA; **never** replace Mini App calculations or show raw internal state. |

Preserved invariants: **published ≠ bookable**; **linked ≠ catalog-visible**; **catalog-visible ≠ execution-linked**; **execution-linked ≠ paid booking**.

---

## Customer-facing states (for copy design only)

These are **UX buckets** for future bot text — **not** new enums in this doc step.

### 1. Published (showcase) but not linked

**Meaning:** Offer may be **published** on showcase / public messaging, but there is **no** **`Tour` bridge** yet (no materialized instance for this offer in the conversion chain).

| Lang | Draft copy |
|------|------------|
| **EN** | **This trip is announced, but bookings aren’t wired to a live departure yet.** Open the app to browse similar trips, or check back soon. |
| **RO** | **Excursia este anunțată, dar rezervările nu sunt încă legate de o plecare activă.** Deschide aplicația pentru oferte similare sau revino în curând. |

### 2. Linked (bridge) but not catalog-visible

**Meaning:** A **`Tour`** exists from the bridge, but it is **not** **listed for sale** (**not** `open_for_sale` / catalog listing path).

| Lang | Draft copy |
|------|------------|
| **EN** | **This departure isn’t on sale in the app catalog yet.** We’re finishing the listing — try again later or browse open tours in the app. |
| **RO** | **Această plecare nu este încă în vânzare în catalogul din aplicație.** Pregătim listarea — încearcă mai târziu sau vezi tururile disponibile în app. |

### 3. Catalog-visible but no execution link

**Meaning:** **`Tour`** is **catalog-visible** (`open_for_sale` / listed), but **`supoffer_*`** (or offer-scoped) **deep** routing is **not** active — customer should use **catalog** or wait for **ops** to add the link.

| Lang | Draft copy |
|------|------------|
| **EN** | **You can see this trip in the app catalog, but the direct link from this announcement isn’t active yet.** Open the app and find the same date/route in the catalog. |
| **RO** | **Vezi excursia în catalogul aplicației, dar linkul direct din acest anunț nu e activ încă.** Deschide app-ul și caută aceeași dată/traseu în catalog. |

### 4. Execution-linked and bookable (Layer A can run)

**Meaning:** **B11** path satisfied and **Mini App** can execute the **Tour** for booking (subject to **seats**, **full_bus**, payment rules — **Mini App** remains source of truth).

| Lang | Draft copy |
|------|------------|
| **EN** | **Ready to book.** Open the trip in the app to choose options and complete your reservation. |
| **RO** | **Poți rezerva.** Deschide turul în aplicație pentru opțiuni și finalizarea rezervării. |

### 5. Unavailable / assisted fallback

**Meaning:** **Sold out**, **past departure**, **blocked**, or **unknown** failure — bot should **not** pretend availability; steer to **human** or **browse**.

| Lang | Draft copy |
|------|------------|
| **EN** | **This trip isn’t available to book online right now.** Browse other dates in the app, or message us and we’ll help. |
| **RO** | **Această excursie nu este disponibilă online acum.** Vezi alte date în aplicație sau scrie-ne și te ajutăm. |

---

## What must **not** be exposed to the customer

- **Raw enum names** (`lifecycle_status`, `OPEN_FOR_SALE`, snake_case action codes).
- **Media review / cover blockers** (`cover_media_quality_review`, **`approved_for_card`**, **`publish_safe`** internals).
- **Internal bridge/execution wording** (“bridge”, “execution link”, “tour-bridge endpoint”, API paths, **POST** names).
- **Operator-only** **`disabled_reason`** strings from **`operator_workflow`**.

Use **plain language** aligned with **C2B11A** labels (**Showcase**, **Catalog**, **Booking link**, **Customer action**) behind the scenes for **ops**; customer copy stays **outcome-oriented**.

---

## Design questions (need product answers before build)

1. **Explain before Mini App?**  
   Should the bot show a **one-screen explanation** (state from table above) **before** opening the Mini App deep link, or **jump straight** with a minimal line + primary CTA?

2. **Secondary actions?**  
   Should the bot offer **Open tour** (primary), **Ask operator** (human channel), and **Browse alternatives** (catalog / router home) as **repeatable** buttons — and in which **priority order**?

3. **Assisted fallback before implementation?**  
   Should **“message operator”** / **RFQ-style** assisted path be **in scope** for the **first** B10.6 implementation slice, or **deferred** until **router** + **Open tour** are stable?

---

## Non-goals (this design step)

- **No** application code.
- **No** Mini App UI or API behavior changes.
- **No** booking, payment, or order logic changes.
- **No** B11 route or deep-link algorithm change — documentation only.

---

## Recommendation

- **Defer** B10.6 implementation until **Admin/OPS** have the **read-only conversion status panel** (**[`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md)** — slice **C2B11A**) **unless** product **explicitly** prioritizes **customer-facing routing** first.
- **Rationale:** Operators and **support** need **one vocabulary** so bot copy, **runbooks**, and **smoke** checks stay aligned; shipping **customer** explanations **before** **ops** clarity increases **mismatch** incidents (wrong expectations on **publish** vs **bookable**).

See ordering: [`docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`](NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md).
