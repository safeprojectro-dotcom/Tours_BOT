# Supplier offer → tour — BUSINESS plan (B1–B13)

**Phase:** Business / product planning **(documentation only)**. **No** code, **no** migrations, **no** runtime behavior in this file.

**Purpose:** Fix the **BUSINESS**-layer plan as the **authoritative sequence** for evolving supplier offers into **Mini App**-visible, **Layer A**-aligned **Tours**—without conflating this line with V2 **track numbers** (which record historical delivery) or with **Y** execution/messaging tickets.

**Aligns with (do not replace):**
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` — V2 Tracks **0–3** and marketplace expansion history.
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`, `docs/TECH_SPEC_TOURS_BOT.md` — product/technical baselines.
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` — Layer A must-not-break.
- Execution-link and conversion bridge work already documented (e.g. Y27, Y30, operator link workflow gates).

### Status (2026) — B10 → Mini App path

**Prerequisites on record (completed, narrow scopes):** **B0–B4.3** — intake, structured data, AI/deterministic packaging, human-readable formatting, template/marketing rules, pricing/discount/availability truth; **B5** — admin packaging review (`approved_for_publish` = package approved, **not** Telegram publish and **not** Mini App activation); **B6** — branded Telegram preview JSON; **B7.1** — media review metadata; **B7.2** — `card_render_preview` plan (**no** real download/storage yet).

**B9** (bridge **design**), **B10** (bridge **implementation**), **B10.1–B10.5** (draft, activate-for-catalog, **full_bus** Mini App semantics, **Layer A** package total, boarding fallback) are **implemented** and **smoke-accepted**. **Production path:** **Supplier offer #8 → Tour #4 → `open_for_sale` → Reserve bus → preparation → reservation → payment entry / mock complete → My bookings**. **Mini App** remains **execution truth**. **B8** (recurring draft `Tour` generation from template offer + audit; **B8.2** activation policy; **B8.3** duplicate-active guard at B10.2) is **implemented** / **stabilized** in-repo — see [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md`](HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md). **Second** **vehicle** same **date** under **one** **offer** = **ops** / **future** **policy** (not automatic product behavior). **B10.6** (bot as router, not duplicate catalog) is **postponed**. **B7.3A** **media** **policy** **accepted** **(docs** **;** see [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) **,** [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) **,** [`docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md`](SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md) **B7.3A** **).** **B7.3** **implementation** **(download,** **object** **storage,** **pixels,** **Telegram** **media** **send** **)** **remains** **unimplemented** **until** **an** **explicit** **slice** **(e.g. ** **B7.3B** **stub** **/** **storage** **).** **No** **automatic** **publish** **from** **media** **approval.** **B11** **unimplemented** **—** **see** [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) **(B11** **).** **Canonical** **B10** **checkpoint:** [`B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md).

**ADMIN Offer Review & Approval Gate — Slice 1:** Read-only **`GET /admin/supplier-offers/{offer_id}/review-package`** aggregates offer snapshot, packaging axis, moderation/showcase axis, showcase preview, bridge readiness, active bridge / linked Tour, catalog activation readiness, execution-link readiness, Mini App conversion preview, warnings, and recommended actions; it does **not** publish, create/link `Tour`, activate catalog, create execution links, or touch booking/payment. **`conversion_closure`** exposes **`has_tour_bridge`**, **`has_catalog_visible_tour`**, **`has_active_execution_link`**, **`supplier_offer_landing_routes_to_tour`**, **`bot_deeplink_routes_to_tour`**, **`central_catalog_contains_tour`**, **`next_missing_step`** **(read-only).** **`SupplierOfferSupplierNotificationService`** import fixed on HTTP admin routes restores supplier notifications after approve/publish/retract (orthogonal read/write split).

**Canonical operator playbook (docs-only):** **[`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md)** — human-readable sequence aligned with admin gates; **always start with** **`GET …/review-package`**; **no** auto-publish **/** auto-bridge **/** auto-catalog activation **/** auto-execution-link **;** **next implementation slice:** read-only **`operator_workflow`** on **`GET …/review-package`.**

**Supplier Offer → Central Mini App Catalog Conversion Closure — test evidence (2026-04-29):** explicit admin sequence **(bridge → activate-for-catalog → catalog lists Tour without execution link → publish → execution link → closure complete)** covered by **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`** **;** moderation-only approval without **`approved_for_publish`** does not create bridge/Tour **;** catalog visibility remains **`Tour`**-driven **;** landing + bot exact **`/tours/{code}`** routing require active execution link **;** Layer A booking/payment semantics unchanged **.**

**BUSINESS-plan-v2 completion audit (docs checkpoint):** **[`docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md`](BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md)** — **not** **`BUSINESS_PLAN_V3`** **;** **not** replacing this file **;** summarizes done/partial/open **; use before next large block **; recommended next:** production/staging E2E smoke **/** real supplier-offer walkthrough **.**

**Production/staging smoke checklist:** **[`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md)** — full operator path **(** dry-run **/** live **)** **;** **not** new functionality **.** Safe **`OFFER_ID`** **/** staging **or** test channel **before** mutating calls **.** Mode **B** **not** executed yet **;** next BUSINESS slice follows **real** smoke outcome **.**

**AI fact lock — Slice 1A (implementation checkpoint):** **[`docs/AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md`](AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md)** — source facts snapshot + **`fact_claims`** validator **`;`** **`review-package`** **`ai_public_copy_review`** **`;`** public channel/Mini App/booking/bridge behavior **unchanged** **`;`** next **:** **`ai_public_copy_v1`** persistence on packaging generate **vs** admin AI workflow **.**

**Admin Content Quality Gate — Slice 1:** **[`docs/ADMIN_CONTENT_QUALITY_GATE.md`](ADMIN_CONTENT_QUALITY_GATE.md)** — read-only **`content_quality_review`** **`;`** weak-copy/discount warnings **`;`** **`review_supplier_offer_content_quality`** **`;`** no booking/showcase/bridge semantics change **`;`** next **:** operator UX **or** AI copy + fact lock **.**

---

## 1. Core business rule (non-negotiable)

**A published supplier offer must become or attach to a `Tour` in the Mini App catalog only through an explicit, auditable bridge**—**not** by silent ORM side effects, **not** by AI, **not** by supplier-only action.

- **“Become”** = create or bind a **Layer A** tour (or tour-shaped catalog row) per product policy.
- **“Attach”** = **execution / conversion link** (or successor contract) from **`supplier_offer` → `tour`**, with clear admin rules (see **B9** / **B10** and existing design gates).

This rule governs **B1–B13** and prevents accidental coupling of **moderation**, **AI packaging**, and **catalog truth**.

---

## 2. BUSINESS track overview (B1–B13)

| ID | Name | Intent |
|----|------|--------|
| **B1** | Supplier offer intake + AI packaging + moderation (design) | Raw supplier facts → draft AI packaging → admin approval before publication. **Design:** [`SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md). |
| **B2** | Supplier offer content / data upgrade | Schema + validation for intake fields, media references, program blocks, promos, recurrence hooks—**as needed** to implement B1. |
| **B3** | Supplier dialog upgrade | Telegram FSM/UX: step-by-step intake, one question at a time, validation—aligned with B1 dialog structure. |
| **B4** | AI packaging layer | Pluggable service contract: **draft-only** text/card outputs, **no** publish, **no** inventing commercial facts. |
| **B5** | Admin moderation & review | Surfaces to compare **raw** vs **AI draft**, edit/regenerate, approve/reject, clarification loops. |
| **B6** | Branded Telegram post template | Deterministic or templated public-channel presentation (brand, sections, CTA) once content is approved. |
| **B7** | Photo moderation & card generation | Safe media pipeline, optional card/preview image generation, moderation gates. |
| **B8** | Recurring supplier offers | **In-repo:** admin **`POST` …/recurrence/draft-tours** creates **draft** `B8R-*` `Tour`s + **audit**; **activation** **explicit** **via** **B10.2** **only;** **B8.3** **blocks** **duplicate** **`open_for_sale`** for **same** **template** **offer+departure** (sibling **B8** or **B10** **bridge**). **Duplicate** **drafts** **OK**; **re-run** **idempotency** **open.** **Second** **vehicle** **/ same** **date** = **ops** **/** **future** **policy** (capacity **bump** **or** **separate** **offer**/**tour**). |
| **B9** | Supplier offer → tour publication **bridge** (design) | Contract for **how** offer becomes/attaches to **Tour** and appears in Mini App; cites core rule §1. |
| **B10** | Supplier offer → tour bridge **implementation** | Runtime + migrations + admin flows to realize B9 without breaking Layer A. |
| **B11** | Telegram deep link routing | Stable `t.me/.../start` / callback routing for offer → Mini App / booking entry (aligned with product links). |
| **B12** | Admin/OPS visibility | Observability: offers, links, errors, operator surfaces (extends existing admin read patterns). |
| **B13** | Final smoke / production validation | End-to-end checklist: intake → moderation → publish → bridge → catalog → bookability smoke. |

---

## 3. Suggested sequence (not all gates are strict waterfalls)

- **B1** (design) → **B2** (data) → **B3** (dialog) can overlap in *planning*, but **implementation** should prefer: **B2** fields **before** heavy **B3**/**B4** wiring if persistence is incomplete.
- **B4** depends on B1 **output contract** and B2 **structured fields** (at least in principle).
- **B5** is the **control room** for human approval; it consumes B1 + B4 outputs.
- **B6**–**B7** can follow once **B5** can freeze “what gets published to Telegram and what assets exist.”
- **B8** is **logically** after a stable single-offer path (B1–B7), unless product explicitly sequences recurrence earlier.
- **B9** must be **accepted as design** before **B10** code; **B10** may reuse existing **execution link** / **conversion bridge** work—cite those docs in the ticket, do not fork concepts.
- **B11**–**B12** can proceed in parallel with B10 where safe.
- **B13** closes the slice for production.

---

## 4. Guardrails (whole BUSINESS line)

- **Layer A** booking, payment, reservation, reconciliation semantics remain **unchanged** unless a **separate** compatibility gate says otherwise (`TRACK_0` / Phase **7.1** alignment).
- **AI** (when introduced in B4/B1) is **draft-only**; it **must not** invent dates/prices/seats, **must not** publish, **must not** create **Tour**, **order**, or **payment** rows.
- **Supplier** cannot bypass **platform** moderation for public/market-facing publication (as in current Track **3** spirit).
- **RFQ** / **Layer C** and **supplier execution** (**Y** line) stay **separate product surfaces** unless a future gate explicitly integrates them.

---

## 5. Next safe step (BUSINESS)

**Forward order of work (2026) —** **B8** **MVP** **slice** **(draft** **generation** **+** **B8.2** **/** **B8.3** **guards** **)** **is** **implemented;** **choose** **next** **step** **explicitly** ( **not** **auto-approved** **here** **).**

1. **B7.3** — **Policy** **(** **B7.3A** **)** **accepted** **;** **implementation** **(download,** **storage,** **pixels,** **send** **)** **postponed** **until** **explicit** **slice** **(** **B7.3B** **stub** **or** **storage** **).** **See** [`docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md`](SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md) **(B7.3A** **).** **—** **no** **auto-publish;** **B7.1/7.2** **unchanged.**
2. **B11** — **Telegram** **deep** **link** **routing** **(first** **slice** **implemented** **):** **private** **`/start` `supoffer_<id>`** **uses** **active** **`supplier_offer_execution_links`** **to** **offer** **Mini** **App** **`/tours/{code}`** **when** **the** **linked** **tour** **is** **`open_for_sale`** **and** **customer-visible** **;** **generic** **chat** **catalog** **overview** **is** **not** **sent** **after** **that** **exact-Tour** **path** **(see** **`CHAT_HANDOFF`**, **`OPEN_QUESTIONS`** **§24** **).** **Further** **B11** **product** **steps** **may** **expand** **routing** **;** **not** **auto-approved** **here.**
3. **B10.6** — **bot** as **router** **/** **consultant** **:** **slice** **1** **`/start` `tour_<code>`** **/** **tour-detail** **keyboard** **→** **Mini** **App** **`/tours/{code}`** **;** **B10.6B** **generic** **`/start`** **/** **`/tours`** **—** **router** **home** **no** **auto** **catalog** **cards** **;** **B10.6C** **—** **router** **copy** **/** **full_bus** **assisted** **wording** **polish** **(see** **`CHAT_HANDOFF`** **).**
4. **B12/B13** **—** **Telegram** **showcase** **(first** **slice** **+** **B13.1** **branded** **RO** **text** **template** **implemented** **):** **deterministic** **text-only** **template** **`supoffer`** **bot** **CTA** **+** **soft** **Mini** **App** **supplier-offer** **landing** **;** **no** **hard** **„Rezervă”** **;** **no** **channel** **`/tours/{code}`** **;** **no** **photo**/**media** **publish** **;** **emoji**/**section** **layout** **(marketing** **showcase** **,** **not** **dry** **listing** **)** **;** **booking**/**payment** **unchanged** **;** **Mini** **App** **execution** **truth** **unchanged** **;** **admin** **final** **publisher** **unchanged** **;** **B13.3** **`disable_web_page_preview`** **on** **showcase** **`sendMessage`** **;** **B13.4** **read-only** **`GET /admin/supplier-offers/{id}/showcase-preview`** **before** **publish** **;** **B7.4**/**B7.5**/**B7.6** **storage**/**render**/**sendPhoto** **deferred** **(** **`CHAT_HANDOFF`** **).** **B13.6** **(ops** **docs** **):** **recommended** **procedure** **preview** **→** **verify** **→** **`POST .../publish`** **—** **not** **mandatory** **in** **code** **;** **no** **preview** **hash** **/** **DB** **tracking** **in** **MVP** **—** **[`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** **.** **B13.6A** **(docs)** **:** **three** **layers** **—** **supplier** **raw** **facts** **;** **future** **AI** **marketing** **draft** **(reviewed** **/** **approved** **,** **no** **fact** **invention** **);** **deterministic** **showcase** **preview** **as** **final** **channel** **HTML** **—** **admin** **final** **publisher** **.**

- **Completed** **for** **B-line** **continuity (accepted):** **B2;** **B6–B7.2;** **B9** **design;** **B10** + **B10.1–B10.5;** **B8** **slice** **1** + **B8.2** + **B8.3** **(see** **§2** **B8** **row,** **§5.1,** **CHAT_HANDOFF,** **OPEN_QUESTIONS** **).**
- **Alternate** **path** **(still** **valid** **):** **B7.3** **first** **if** **marketing** **requires** **assets** **before** **other** **B-line** **work.**
- **B10.x** **doc** **sync** **checkpoint:** **[`docs/B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md)** **(historical** **B10** **scope** **).**

### 5.1 B8 dependencies and invariants (recurring supplier offers)

- **Recurrence** must **use** the same **Supplier offer → Tour** **bridge** and **Layer A** rules: materialize or link **Tour** instances via **explicit** admin/service steps and **governed** policy — **not** silent **ORM/cron/AI** tour creation.
- **Generated** **Tour** **instances** **start** as **`draft`**. **Catalog** **visibility** **(status** `open_for_sale` **)** **is** **only** **via** **B10.2** **activate-for-catalog** **(B8.2;** **no** **B8-only** **activation** **route** **).**
- **B8.3 (implemented):** **duplicate** **`open_for_sale`** **B8-audited** **Tours** **for** **the** **same** **source** **offer** **+** **same** **`departure_datetime`** **are** **blocked** **at** **activation** **(sibling** **B8** **or** **B10** **active** **bridge** **tour** **).** **Second** **vehicle** **/** **legitimate** **parallel** **capacity** = **not** **solved** **in** **code** **—** **ops** **/** **separate** **offer** **/** **tour** **/** **future** **override** per [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) **(B8** **legitimate** **second** **vehicle** **).**
- **Bridge** **≠** **catalog** **activation** **≠** **Telegram** **channel** **publish** **≠** **booking** **/** **payment** — **preserve** for **each** **generated** **instance.**
- **No** **booking,** **order,** or **payment** **mutation** **inside** **recurrence** **generation** **handlers** **themselves.**
- **No** **automatic** **Telegram** **showcase** **publish** without **explicit** **ops** **/** **status** **policy.**
- **Cite** **B9** / **B10** **/** **[`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md)** **;** do **not** **fork** **execution** **link** **semantics** **(Y27).**

---

## 6. Document control

| Document | Role |
|----------|------|
| This file | **BUSINESS** roadmap **B1–B13** + core bridge rule. |
| [`B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md) | **B10.x** completion, smoke, gates, tech debt, **B8** / **B7.3** / **B11** order. **B10.x** handoff prompt: `docs/CURSOR_PROMPT_B10X_SYNC_HANDOFF_AFTER_SUPPLIER_OFFER_TO_TOUR_BRIDGE.md` (continuity). |
| [`SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md) | **B1** detailed design. |
| `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` | Historical **V2** track delivery; use for **context**, not as a replacement numbering for **B** lines. |
