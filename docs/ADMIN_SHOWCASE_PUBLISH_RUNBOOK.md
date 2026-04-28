# Admin showcase publish — MVP runbook

**Purpose:** Recommended operational workflow for Telegram **channel showcase** publication (supplier offers). **Docs only** — does not change runtime behavior.

**Related:** Track 3 moderation in [`CHAT_HANDOFF.md`](CHAT_HANDOFF.md); B12/B13 business line [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md); preview readiness fields [`docs/CURSOR_PROMPT_B12_B13_4A_SHOWCASE_PREVIEW_READINESS_FIELDS.md`](CURSOR_PROMPT_B12_B13_4A_SHOWCASE_PREVIEW_READINESS_FIELDS.md).

---

## Preconditions

- Central admin **`ADMIN_API_TOKEN`** (same gate as **`/admin/*`**).
- Offer **`lifecycle_status`** must be **`approved`** before **`POST .../publish`** (moderation **`POST .../moderation/approve`** already done).

---

## Three layers: raw facts, AI-prepared copy, final preview (B13.6A)

Showcase publication should be understood as **three** conceptual layers. They are **not** all separate live “publish sources” today; this section states **intent** and **current behavior**.

| Layer | What it is | Policy |
|--------|------------|--------|
| **1. Supplier / admin raw input** | Facts and text as originally entered (**may** be rough, wrong language, placeholders). | **Admin** should verify **facts** (dates, price, **`sales_mode`**, capacity, program, include/exclude, linked execution) against business truth **before** trusting the channel post. |
| **2. AI-prepared public copy** (future-facing) | AI **may** draft or polish **marketing** wording (e.g. tone, structure, translation) **without inventing** commercial facts; such drafts require **explicit admin review** **before** becoming the **canonical** text for publish—**only** when product wires **approved packaging / AI output** fields into that path (**not** documented here as the default publish source until then). | **AI output is not automatically trusted** at publish time. **AI must not** invent or mutate **price**, **dates**, **program**, **availability**, or **execution** truth—those stay tied to **source-of-truth** fields. **Admin approval** stays required. |
| **3. Final showcase preview** | What **`GET …/showcase-preview`** returns: the **deterministic** Telegram HTML from **`build_showcase_publication`** (**same** builder as **`POST …/publish`**). | This is what admin **sees** immediately before publish. **Today**, preview is the **final** deterministic output, **not** an automatic rewrite of bad raw copy—there is **no** automatic AI rewrite on publish. |

**Principle:** **Admin remains the final publisher.** In **future** workflows, admin should **also** review **layer 2** once it is explicitly approved and wired; **now**, still check **layer 1** (facts) **and** **layer 3** (exact channel output).

**Not implemented as product truth here:** AI as final publisher; automatic AI rewrite at publish time; mandatory AI-copy approval workflow; **`preview_hash`** enforcement; new DB fields for “approved public RO copy” unless a future ticket implements them.

---

## Checklist: preview → verify → publish

1. **Approve** the offer via **`POST /admin/supplier-offers/{offer_id}/moderation/approve`** if not already **`approved`**.
2. **Preview (read-only):**  
   **`GET /admin/supplier-offers/{offer_id}/showcase-preview`**
   - Uses the **same** showcase builder as real publish (`caption_html`).
   - **Does not** call Telegram **or** mutate the database.
3. **Verify:**
   - **`caption_html`:** title, dates, route, price, program, included/excluded — match intent.
   - No bad placeholder/test copy; language matches channel policy (e.g. Romanian showcase copy).
   - CTA line present: **Detalii** and **Rezervă** (or equivalent branded line from the template).
   - **`can_publish_now`:** **`true`** when lifecycle + Telegram config allow **`POST .../publish`** to succeed technically.
   - **`warnings`:** empty, or consciously accepted (see policy below).
4. **Publish:**  
   **`POST /admin/supplier-offers/{offer_id}/publish`**
5. **If wrong after publish:**  
   **`POST /admin/supplier-offers/{offer_id}/retract`** as needed → fix supplier/admin data → **preview again** → **publish again** if appropriate.

---

## Policy notes

| Topic | MVP rule |
|--------|-----------|
| Preview before publish | **Recommended**, **not** enforced by code — **`publish`** does not require prior **`showcase-preview`**. |
| **`can_publish_now === true`** | **Technical / lifecycle readiness** for successful **`POST .../publish`** (e.g. approved + showcase channel config). **Not** “marketing/copy approved”. |
| Copy quality | **Admin responsibility** — the system **does not** auto-translate or rewrite text at publish time. AI-drafted marketing copy (**when** introduced into the pipeline) is **not** trusted until explicitly reviewed and wired as publish source. |
| Raw input | Bad or test input appears in preview **and** in the channel post unless corrected upstream — see **Three layers** above. |
| **`preview_hash`**, **`preview_seen_at`**, **`preview_seen_by`** | **Not** in MVP — **no** migration for preview tracking. Future **only** if product or audit explicitly requires it. |

---

## Explicit non-goals (not documented as shipped)

Mandatory preview enforcement, preview-hash requirement, dedicated admin SPA, **AI as final publisher**, **automatic AI rewrite at publish time**, **mandatory AI-copy approval workflow** (until explicitly scoped), **`sendPhoto`**, channel **`/tours/{code}`** links, media pipeline (**B7.4+**), booking/payment semantics, Mini App UI changes.
