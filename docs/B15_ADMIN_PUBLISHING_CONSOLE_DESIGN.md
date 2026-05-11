# B15 — Admin Publishing Console & Channel Publication Model (design)

**Project:** Tours_BOT. **Slice:** **B15A — docs-only design.**  
**Status:** Product/architecture blueprint — **no** application code in B15A.

**Related:** [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) · [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md) · [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) · [`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md) · [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) · [`docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`](B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md) · [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md).

**Current code baseline (context, not scope of B15A):** Showcase publish flows through **`build_showcase_publication`** (`app/services/supplier_offer_showcase_message.py`), **`SupplierOfferModerationService.publish`** / preview, **`TelegramShowcaseChannelAdapter`**, publish attempt audit (**B13D–F**), **review-package** + **`operator_workflow`**, Mini App **`mini_app_supplier_offer_url`** for **Rezervă** CTA (`SupplierOfferModerationService.showcase_preview`). Execution truth for **exact tour** is **separate** (B10 bridge, catalog activation, execution link, B11 routing).

---

## 1. Purpose

Define a **second layer** of product: an **Admin Publishing Console** that manages **what goes to the Telegram channel (and future surfaces)** as **communication**, distinct from **Supplier Offer Admin** (product preparation, moderation, packaging, bridge operations).

The channel must carry **many message types** (new tours, urgency, reminders, transport ads, pure info, future formats) **without** requiring a **code deploy per format**, while keeping **operator UX** shallow: queue, status, preview, publish, skip, schedule — **not** a wall of technical fields.

---

## 2. Problem statement

**Today (MVP):** Channel publication is **tightly coupled** to **supplier offer showcase publish** — one primary path, one HTML builder, **review-package** gates, **B12** template metadata mostly **advisory** until wired into **`build_showcase_publication`**.

**Product reality:** The channel is a **broadcast medium**. Treating every post as “supplier offer publish” will:

- Force awkward data modeling (fake offers for “last seats” or “reminder”).
- Bury admins in **offer lifecycle**, **moderation**, and **conversion panel** fields when they only want to **compose and send** a compliant channel post.
- Block **extensibility** (new templates) behind **Python changes** for every marketing idea.

**Risk if unaddressed:** Either **channel starvation** (too hard to post) or **truth drift** (operators bypass gates and post manual copy that contradicts catalog or booking rules).

---

## 3. Workspace separation

| Workspace | **Role** | **Primary user questions** |
|-----------|----------|----------------------------|
| **Supplier Offer Admin** | Prepare **products**: packaging, supplier truth, moderation, media, bridge, catalog activation, execution link, **review-package** / **conversion_status_panel**. | “Is this offer **correct**, **approved**, and **conversion-ready**?” |
| **Admin Publishing Console** | Prepare **communications**: channel posts, campaigns, reminders; **attach** to resolved **conversion targets** when CTAs exist. | “What is **queued** to the channel **today**? Is this post **safe** and **honest**? **Preview / publish / skip**?” |

**Rules:**

- **Do not merge** into one monolithic “offer screen” that is both CRM and CMS.
- **Publishing Console** may **reference** Supplier Offers, Tours, RFQs, or **manual** content — it does **not** replace **offer approval** or **bridge** operations.
- **Supplier Offer Admin** remains the place for **first-time** offer correctness; **Publishing Console** may **block** “initial public channel publish” until **conversion target** is ready (see §12), but **should not** duplicate the entire review-package UI.

**Navigation concept:** “**Products & conversion**” vs “**Channel & campaigns**” (exact labels product-defined).

---

## 4. Channel Publication conceptual model

High-level types (names illustrative; persistence is **B15B+**):

### 4.1 Channel Publication

A **single intended send** to a **channel** (or export slot). Fields (conceptual):

- **id**, **created_at**, **scheduled_for**, **published_at** (nullable until sent).
- **channel_ref** (e.g. Telegram showcase channel id — aligns with B13).
- **publication_kind:** `initial_supplier_showcase` | `tour_promotion` | `last_seats` | `reminder` | `service_transport_ad` | `informational` | `custom_campaign` | … (extensible enum or string registry).
- **source_entity_type** + **source_entity_id** (nullable for pure manual).
- **template_id** (registry key, maps to B12-style library + future entries).
- **conversion_target** (see §5) — resolved snapshot at **draft** time, revalidated at **publish** time.
- **safety_policy_id** / **policy_eval_snapshot** (see §7).
- **draft_payload_ref** → **Publication Draft** (caption, optional media ref, CTA URLs).
- **status:** `draft` | `ready` | `blocked` | `needs_attention` | `skipped` | `scheduled` | `publishing` | `sent` | `failed` | `cancelled`.
- **blocking_reasons[]** (human-readable + machine codes).
- **attempt_ref** → latest / list of **Publication Attempt** (audit, aligns with **B13** attempt philosophy).

### 4.2 Publication Template

- **Template key** (e.g. reuse **`ShowcaseMarketingTemplateId`** and add **channel-specific** keys: `WEEKLY_DIGEST`, `REMINDER_DEPARTURE_24H`, …).
- **Slot contract:** which **placeholders** exist (title, dates, price line, seats line, CTA block).
- **Default conversion_target_kind** (may be overridden per publication).
- **Allowed automation modes** (§9).
- **Safety profile:** which **gates** apply (§7, §11).

Templates are **data-driven** where possible; **new template = config + registry entry**, not necessarily code.

### 4.3 Conversion Target

See **§5** (registry). Snapshot on draft: URLs, **`tour_code`**, **`supplier_offer_id`**, Mini App paths — **re-resolved** at publish so stale links are caught.

### 4.4 Safety Policy

Named set of **rules** (exact tour gates, seat honesty, deadline, RFQ enabled, “no false booking” for info posts). Evaluates → **pass / block / needs_attention** with reasons.

### 4.5 Publication Draft

Immutable or versioned **content** used for preview:

- **caption_html** (or structured blocks → render to HTML).
- **photo_ref** (optional).
- **cta_spec** (machine-readable: primary/secondary link types).
- **language**, **accessibility flags** (future).

Preview in console = render draft **exactly** as adapter will consume (align **`showcase_preview`** pattern).

### 4.6 Publication Attempt / Audit

Same role as **`supplier_offer_showcase_publish_attempts`** today: **requested → provider_sent → persisted | failed**, fingerprint, error class, **no blind retry** until product says so. Generalize **conceptually** to **ChannelPublicationAttempt**; **B15B** may still **reuse** existing table with `publication_type` discriminator **or** add parallel table — **implementation choice deferred**.

---

## 5. Conversion Target registry

**Target type** | **Meaning** | **Typical CTA behavior**
|----------------|------------|-------------------------|
| **`exact_tour`** | Mini App **exact** tour route (`tour_code`), B11-style. | Open catalog tour / deep link **only** when bridge + catalog + execution link policy satisfied.
| **`supplier_offer_landing`** | **`/mini-app/supplier-offers/{id}`** (today’s **Rezervă**-style landing). | Entry to offer context; may still require **published** offer + policy.
| **`custom_transport_request`** | Layer C **RFQ / custom bus** intake. | **`POST /mini-app/custom-requests`** or dedicated Mini App route per product.
| **`custom_trip_request`** | Synonym or subtype if product splits **transport** vs **trip** copy. | Same family as RFQ; gated on **intake enabled**.
| **`contact_bot`** | Private bot **start** / help / human handoff — **no** instant book. | `t.me/...` deep link.
| **`mini_app_page`** | Generic in-app path (catalog, help, static page). | Requires **known route registry**.
| **`external_url`** | Partner / static HTTPS. | **Safety:** allowlist domain policy (future).
| **`no_cta`** | Informational only — **no** booking claim in body unless policy allows soft “learn more”.

**Source entities** (what a publication **ties back to**):

- **`supplier_offer`**
- **`tour`**
- **`service`** (future packaged add-on entity; or **logical** slice of supplier offer)
- **`campaign`** (console-only grouping; no DB tour row)
- **`manual`** / **`info`** (freeform with **strict** safety tier)

---

## 6. Template model

**Layers:**

1. **Registry** — template id, label, category (`commercial` | `urgency` | `reminder` | `promo` | `info`).
2. **Presentation rules** — which **facts** must be supplied by **resolver** from `tour` / `supplier_offer` / RFQ stats vs **operator override** (e.g. **last seats** requires **verified** `seats_available` — aligns with B12 **`LAST_SEATS_URGENT`** discipline).
3. **Slot map** — named slots → resolver functions (many **declared in config**; rare slots need code).

**B12 alignment:** **`infer_showcase_marketing_template`** remains valid for **offer-centric** assembly; **Publishing Console** adds **channel-centric** templates that may **compose** multiple entities (e.g. digest) **without** inventing facts.

**Adding a format without code (when allowed):**

- New **template id** pointing at **existing slots** + **existing target type** + **existing safety tier**.
- **Copy** variants as JSON / admin-editable **snippets** (future **CMS** depth product-defined).

**Code still required when:** new **resolver** (new fact source), new **target type**, new **channel adapter**, new **payment/booking** path.

---

## 7. Safety policy model

Policies are **composable**:

- **Tier A — hard block (no publish):** breaks law/truth (wrong price, past departure, zero seats on “last seats”, broken execution for **exact_tour** when CTA promises instant book).
- **Tier B — needs_attention:** soft issues (missing optional photo, stale template, **low** seat count not zero).
- **Tier C — informational:** no booking CTA; only **no false claims** checks.

**Exact tour (summary gates — aligns with B10/B14/B14A readiness thinking):**

- Tour **exists**; **`open_for_sale`** (or product-defined “promotable” states for **non-booking** CTA variants).
- **Departure** in future (timezone-safe).
- **Catalog** visibility rules satisfied for **customer** truth.
- **`seats_available`** (and **`sales_mode_policy`**) consistent with **copy** — no “last 3 seats” if DB says **0** or **full** for per-seat policy.
- **Execution link** + **B11** route **known** when CTA is **exact_tour** / bookable path.
- **Text facts** generated from **same read models** as Mini App (avoid stale snapshot).

**Custom transport / RFQ:**

- Intake **enabled**; Mini App route **exists**; **assisted** copy matches **`EffectiveCommercialExecutionPolicyService`** truths (Track 5b.x) when citing **platform** checkout.

**Info / no CTA:**

- **No** sentence that implies **confirmed** booking without path; **no** invented discounts.

---

## 8. Admin UX model

### 8.1 Primary screen: **Today’s queue**

**Columns (conceptual):**

- **Title / summary** (auto from template + entity).
- **Kind** (icon: new tour / urgency / reminder / transport / info).
- **Target** (exact tour · offer landing · RFQ · none).
- **Status:** **Ready** (green) · **Blocked** (red, reasons tooltip) · **Needs attention** (amber).
- **Schedule** (time or “immediate”).
- **Actions:** **Preview** · **Publish** · **Skip** · **Reschedule**.

**Default view:** **hide** packaging JSON, internal IDs, adapter stack traces. Show **human** blockers only: e.g. “Execution link missing — cannot use **Exact tour** CTA.”

### 8.2 Advanced / debug mode (toggle)

For **super-admin** or **support:**

- Raw **conversion_target** resolution JSON.
- **Template** trace (`selection_rules`-style from B12).
- **Policy evaluation** breakdown.
- **Last publish attempt** payload fingerprint (B13-style).

### 8.3 Examples (normal admin)

| Scenario | Queue shows | One-click actions |
|---------|----------------|-------------------------|
| **New supplier tour** | “**Bucharest day trip** — initial showcase” · Ready | Preview · Publish — blocked until §12 checklist green |
| **Last seats** | “**Tour X** — last seats · **3** seats” | Blocked if **3** ≠ DB; Publish when Ready |
| **Private transport ad** | “**Charter spring** — RFQ CTA” | Preview · Publish (RFQ target) |
| **Info post** | “**Holiday hours** — no CTA” | Preview · Publish (policy tier C) |

---

## 9. Automation modes

| Mode | Behavior | Suitable post types |
|------|----------|---------------------|
| **Manual draft** | Operator creates/edits draft; no auto text. | All, especially **info**, sensitive **commercial**. |
| **Auto draft** | System proposes draft from template + entity snapshot; **always** review before send. | **Digest**, **reminder** skeletons, **tour_promotion** from Tour card. |
| **Approval required** | Auto draft **or** scheduled slot requires **second** role or explicit “Approve” (product-defined). | **Initial showcase**, **last seats**, **paid promos**. |
| **Limited auto-publish** | Auto-send **only** for templates with **tier C** or **narrow** tier B + caps (§11). E.g. **reminder** with fixed template, **no** inventory sentence. | **Reminder** variants, **info**, possibly **non-booking** nudges. |
| **Disabled** | Channel queue **read-only** or hidden. | Maintenance, incidents. |

**Principle:** **Auto-publish** never bypasses **hard** safety tier A rules; failures → **failed** + notification, not silent drop.

---

## 10. Scheduler / campaign calendar

**Concept:** **Campaign** = rules + template + audience filter (which tours/offers eligible). **Calendar** = proposed **Publication** rows.

**Example weekly rhythm (illustrative):**

| Day | Theme | Typical templates |
|-----|-------|-------------------|
| **Monday** | **New tours digest** | Aggregate **Tours** first listed **or** offers first **published** in last 7d; **targets** mixed (exact_tour if ready, else offer landing). |
| **Wed / Thu** | **Existing tour promotion** | Rotating catalog subset; **no** duplicate tour in same week (§11). |
| **Friday** | **Last seats / final call / transport** | **Last seats** only if policy passes; **transport** posts use **RFQ** or **service** template. |

**Operator override:** Drag **scheduled** slot, **Skip** week, **Pause** campaign.

**Implementation note:** **B15F** introduces **auto-draft** generation jobs; **full** calendar UI may lag **headless** schedule API.

---

## 11. Anti-spam rules

Configurable limits (defaults product-tuned):

- **Max posts per day** per channel (and per **campaign**).
- **Min hours between** two **commercial** posts for the **same** `tour_id` or `supplier_offer_id`.
- **Last seats:** **no** publish if **`seats_available == 0`** (or **full_bus** equivalent) unless template is **non-booking** “sold out / waitlist” variant (explicit).
- **No publish** after **`sales_deadline`** for bookable **exact_tour** posts claiming bookability.
- **No publish** if **conversion target** resolution returns **unavailable** (missing execution link when CTA requires it — aligns with **B14A** lessons).
- **Digest dedup:** same entity **not** twice in one digest.

Violations → **blocked** with clear reason in queue.

---

## 12. Supplier Offer initial publication sequence (preferred)

**Order operations** in Supplier Offer Admin **unchanged**; **Publishing Console** enforces **“first channel blast”** readiness:

1. Packaging **approved_for_publish** (existing).
2. Moderation **approved** (existing).
3. Media / cover policy satisfied for **chosen** template (C2B8A/C2B5 family).
4. **Tour bridge** created (**Tour** row exists).
5. **Tour catalog** active (**`open_for_sale`** activation).
6. **Execution link** active (B10/B11 truth for **exact** customer path).
7. **Publication draft** built with **`conversion_target = exact_tour`** (preferred) **or** **`supplier_offer_landing`** if product allows staged CTAs — **product choice in B15C**.
8. **Preview** (Publishing Console or existing **`showcase-preview`** parity).
9. **Publish** to channel **last** among **public** steps when the **promised** customer destination is honest.

**Principle:** **Channel publish** must not **race ahead** of **bookable** truth if the post promises **Rezervă**/exact routing — aligns with **ADMIN_OPERATOR_WORKFLOW** / **C2B9B** ordering.

---

## 13. Tour promotion / last seats sequence

1. Pick **Tour** (or **Supplier Offer** linked to tour) in **Publishing Console**.
2. Select template **`tour_promotion`** or **`LAST_SEATS_URGENT`** (B12).
3. **Resolver** pulls **live** `seats_available`, **`sales_deadline`**, **`tour_code`**, execution link status.
4. **Policy** runs §7 + §11.
5. **Preview → Publish** (or **Schedule**).

**Last seats:** **verified** seat count **mandatory** (admin or sync from DB; B12 **`admin_live_seats_remaining`** precedent).

---

## 14. Service / private transport ad sequence

1. Source: **`supplier_offer`** with **`service_composition`** / **`ASSISTED_CLOSURE`** semantics **or** standalone **campaign** entity for **brand** transport (product-defined).
2. **Conversion target:** **`custom_transport_request`** or **`supplier_offer_landing`** depending on whether CTA is **RFQ** or **offer** narrative.
3. **Policy:** RFQ intake enabled; **EffectiveCommercialExecutionPolicy** hints if quoting **platform** vs **external** closure (Track 5b.x) — **no** false “pay now” if not allowed.
4. **Preview → Publish**.

---

## 15. Future extensibility

**Without code (ideal path):**

- New **Publication Template** row using existing **slots** and **resolver** sources.
- New **Campaign** schedule rule (declarative).
- Existing **conversion target** + **safety tier** combination.

**Requires code:**

- New **Mini App route** or **RFQ** branching.
- New **safety** invariant (e.g. cross-offer bundle rules).
- New **channel** (WhatsApp, email) — **B13** new adapter.
- New **monetization** / checkout path.

**Direction:** Treat **Publishing Console** as **orchestration UI** over **read models** and **adapters**, not a second **source of truth** for commercial facts.

---

## 16. Rollout plan (B15B–B15G)

| Slice | Scope | Outcome |
|--------|--------|---------|
| **B15A** | **This document** — design acceptance. | Shared vocabulary; non-goals explicit. |
| **B15B** | **Read-only** Publishing Console API + UI skeleton: queue from **existing** publishes + mock **draft** reads. | No new send paths. |
| **B15C** | **Exact-tour CTA** for **supplier offer** showcase posts when conversion chain green; **align** `build_showcase_publication` / preview with **resolved** `tour_code` link (product parity with §12). | Reduces **landing-only** friction when tour ready. |
| **B15D** | **Tour promotion** drafts — create **Channel Publication** rows from **Tour** without new **SupplierOffer**. | Last-mile promos decoupled from offer lifecycle. |
| **B15E** | **Service / transport** templates + **RFQ** targets in console. | Commercial diversity without fake offers. |
| **B15F** | **Scheduler** — **auto-draft** queue entries (**no** auto-send unless mode allows). | Monday digest / Friday slot automation. |
| **B15G** | **Limited auto-publish** behind **tier C** + caps + kill switch. | Low-risk reminders only; audit mandatory. |

Order may shift if **B15C** is **higher** product priority than **B15D** (exec link / CTA honesty first).

---

## 17. Explicit non-goals (B15A)

- **No** implementation of console UI, APIs, DB tables, or schedulers in B15A.
- **No** change to **`POST …/publish`** behavior, **`build_showcase_publication`**, or **B13** adapter in this slice.
- **No** weakening **review-package**, **fact lock**, or **Layer A** booking rules.
- **No** promise that **every** future format is **config-only** — only a **design target**.
- **No** automatic **AI** as final publisher — **admin / approval** remains product default unless a **future** slice explicitly ships **trust model**.
- **No** merger of **Supplier Offer Admin** and **Publishing Console** into one undifferentiated workflow.

---

**End B15A design.**
