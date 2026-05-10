# B13G — Production publish smoke with audit verification (runbook)

**Project:** Tours_BOT. **Type:** documentation / ops readiness only — **does not** change application code or tests.

**Purpose:** Give operators a **repeatable checklist** to confirm that, after deploy, **showcase publish audit** (B13D–B13F) is **live**: migration applied, **`supplier_offer_showcase_publish_attempts`** in use, and **`review-package`** exposes **`showcase_publish_attempts_review`** so publishes can be traced (who, outcome, provider ids, errors).

**Related:** **[`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** (preview → publish workflow); **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** §11–§12; **[`docs/HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`](HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md)**; **[`docs/HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)** (production smoke result — 2026-05-10); **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** (B13D–B13F bullets).

---

## Safety and scope

- **This document** does not execute commands on your behalf. **Your** team runs steps in **staging** or **production** only under your change policy.
- **Read-only steps** (migration status, **`GET …/review-package`**) are safe to run anytime you already have admin access.
- **Publish** (**`POST …/publish`**) is a **real public side effect** (Telegram channel post). Run publish smoke only on an **approved** offer, in the **intended** environment, and **never** as part of automated CI against production without explicit approval.
- **No retry/resend** and **no idempotency enforcement** in product (B13E) — a failed publish may leave **`failed`** attempt rows; duplicate publishes are **not** automatically deduped. Treat audit rows as **evidence**, not as a substitute for process.

---

## Checkpoint (what must already be shipped)

| Slice | What production must have |
|--------|---------------------------|
| **B13D** | Alembic migration **`20260531_29_supplier_offer_showcase_publish_attempts`** applied — table **`supplier_offer_showcase_publish_attempts`**, FK **`ON DELETE RESTRICT`**. |
| **B13E** | **`SupplierOfferModerationService.publish`** creates/updates attempts: **`requested`** → **`provider_sent`** → **`persisted`** or **`failed`**. |
| **B13F** | **`GET …/review-package`** includes **`showcase_publish_attempts_review`**; Telegram admin offer card shows compact publish audit block. |

---

## 1. Deploy gate: migrations (Railway / production)

**B13D** introduced the attempt table. After deploy, the runtime **must** run Alembic **before** relying on publish audit.

**On the deployment environment** (e.g. Railway service shell or release phase — match your repo’s standard; see internal deploy docs):

```bash
python -m alembic upgrade head
python -m alembic current
```

**Expect:**

- **`upgrade head`** completes without error.
- **`current`** shows head revision **`20260531_29`** (or a later migration that **revises** **`20260531_29`**). Migration file: `alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py` — **`revision = "20260531_29"`**.

**If migration is missing:** publish may error or skip audit persistence; **do not** treat publish as audited until this is fixed.

---

## 2. Read-only check: review-package shape (any offer id)

Use an existing **`offer_id`** you are allowed to inspect (e.g. staging draft or a published offer).

```http
GET /admin/supplier-offers/{offer_id}/review-package
Authorization: Bearer <ADMIN_API_TOKEN>
```

**Verify JSON contains:**

- **`showcase_publish_attempts_review`** with:
  - **`total_returned`** (integer),
  - **`items`** (array, possibly empty),
  - **`preview_notice`** (string).

**Empty history:** **`items: []`** and **`total_returned: 0`** are valid if the offer **never** went through a publish that wrote attempts.

**If the key is missing:** deploy artifact may predate B13F — fix versioning before relying on audit UX.

---

## 3. Audit row semantics (verification cheat sheet)

Each element of **`items`** (newest first in API) should align with DB enums documented in B13C:

| Field | Notes |
|--------|--------|
| **`status`** | **`requested`**, **`provider_sent`**, **`persisted`**, **`failed`** (string values). |
| **`actor_surface`** | **`http_admin`** or **`telegram_bot`**. |
| **`requested_by`** | e.g. **`http_admin`**, **`telegram:{telegram_user_id}`**. |
| **`showcase_chat_id`**, **`showcase_message_id`** | Set when **`persisted`** (match channel message when correlating manually). |
| **`error_code`**, **`error_message`** | Populated when **`failed`** (e.g. send error, missing message id). |

**Edge case (documented in B13C):** Telegram may accept a message while DB commit fails — rare **orphan-post** / inconsistent state; audit improves traceability but does not remove this class of risk.

---

## 4. Optional: end-to-end publish smoke (ops-controlled)

**Only** when product/ops explicitly approve a **real** publish test (staging strongly preferred for first run).

**Preconditions (align with [`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)):**

- Offer **`lifecycle_status`** **`approved`**; packaging and **`operator_workflow`** allow publish for your surface (HTTP vs Telegram).
- **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`** (or equivalent) and bot token valid for the target channel.

**Steps:**

1. Record baseline: **`GET …/review-package`** — note **`showcase_publish_attempts_review.total_returned`** (and optionally last attempt id if any).
2. **Preview (read-only):** **`GET …/showcase-preview`** — confirm caption/CTAs as intended.
3. **Publish:** **`POST /admin/supplier-offers/{offer_id}/publish`** (or Telegram C2B8B confirm path — same moderation service).
4. **Re-fetch:** **`GET …/review-package`**.
5. **Assert:**
   - **`total_returned`** increased by at least **1** (or exactly one new row if you know no concurrent publish).
   - Latest **`items[0].status`** is **`persisted`** for success.
   - **`showcase_message_id`** / **`showcase_chat_id`** present and match the message in the Telegram channel (manual spot-check).
6. **Telegram admin:** Open the same offer card — compact **publish attempts** block should list the recent attempt (up to 5 rows in UI).

**On intentional failure smoke (advanced):** e.g. wrong channel id in a **disposable** environment — expect **`failed`**, **`error_*`** set, offer remains **`approved`**; **do not** run destructive tests in production without a written plan.

---

## 5. Telegram admin (no HTTP)

Operators can rely on the **compact audit block** on the offer detail message (same thread as operator workflow). Full fields remain in **`GET …/review-package`** JSON.

---

## 6. Explicit non-goals (B13G runbook)

- **No** automatic retry/resend procedures (future **B13H+** / product decision).
- **No** **`idempotency_key`** enforcement checklist — key remains **unused** for dedupe in MVP.
- **No** dedicated **`GET …/showcase-publish-attempts`** in MVP — use **`review-package`**.
- **No** DB purge/archive of attempts here — **RESTRICT** FK means offer deletes fail while attempts exist; archival is a future ops topic.

---

## Run log — 2026-05-10 (Railway production)

**Recorded ops result** — see also **[`docs/HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md`](HANDOFF_B13G_PRODUCTION_SMOKE_RESULT_TO_NEXT_STEP.md)**.

| Aspect | Result |
|--------|--------|
| **Environment** | Railway **production** |
| **Migration** | Applied via **Railway SSH**; **`python -m alembic current`** → **`20260531_29 (head)`** |
| **Offer** | **`supplier_offer_id` 11** — title *Excursie Timisoara Cluj* |
| **Pre-check (`GET …/review-package`)** | **`showcase_publish_attempts_review.total_returned`** = **0**; **`cover_media_quality_review.has_warnings`** = **false** (after approve-for-card); **`operator_workflow`**: **`publish_showcase_channel.enabled`** = **true**; **`showcase_preview.can_publish_now`** = **true**; **`publication_mode`** = **`photo_with_caption`** |
| **Publish** | **Admin API** — **`POST /admin/supplier-offers/11/publish`** |
| **Channel** | Telegram showcase post **created**; **no** duplicate post observed during smoke |
| **Post-check** | **`showcase_publish_attempts_review.total_returned`** = **1** |
| **Latest attempt (`items[0]`)** | **`id`** **1**; **`status`** **`persisted`**; **`provider`** **`telegram_showcase_channel`**; **`actor_surface`** **`http_admin`**; **`requested_by`** **`http_admin`**; **`showcase_chat_id`** **`-1003955096010`**; **`showcase_message_id`** **23**; **`error_code`** / **`error_message`** **null** |
| **`conversion_status_panel` (snapshot)** | **`showcase`**: published · **`tour_bridge`**: linked · **`catalog`**: listed_for_sale · **`booking_link`**: **missing** · **`customer_action`**: not_bookable_yet, detail **view_only** |

**Observation:** B13D / B13E / B13F / B13G **audit chain works** end-to-end. **Booking link** is still **missing** — **next functional step** is **creating / verifying an execution link** for Offer **11**, **not** retry or resend publish.

**Security:** **`ADMIN_API_TOKEN`** may have appeared in **manual smoke** screenshots or chat — **rotate** the token in **Railway** environment/config after smoke **(do not paste secrets into docs)**.

---

## 7. Forward references

- **Design / retry:** **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**.
- **Manual retry/resend product design:** track as separate doc/ticket (often labeled B13H or similar) — **docs-first**, **no** behavior until idempotency/safety approved.
