# Open Questions and Tech Debt

## Purpose
Track temporary decisions, accepted shortcuts, open architectural questions, and future review points for Tours_BOT.

This file is for items that are acceptable **now**, but should not be forgotten later.

---

## Checkpoint Sync — Admin Offer Review Package — Slice 1 (2026-04-27)

**Docs-only.**

- **Endpoint:** **`GET /admin/supplier-offers/{offer_id}/review-package`** — read-only; aggregates offer snapshot, packaging axis, moderation/showcase axis, showcase preview, bridge readiness, active bridge / linked Tour, catalog activation readiness, execution-link readiness, Mini App conversion preview, warnings, `recommended_next_actions`.
- **Out of scope for this read:** Telegram publish; `Tour` create/link; catalog activation; execution-link creation; booking/payment mutations.
- **Incident:** **`SupplierOfferSupplierNotificationService`** was missing from admin route imports — **`NameError`** swallowed after approve/publish/retract; **import restored** so supplier notifications fire from HTTP admin paths again (separate from review-package behavior).

**Next functional block:** **SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE:** **`conversion_closure`** **field + below.**

---

## Checkpoint Sync — Catalog conversion closure (2026-04-29)

**Docs-only summary.**

- **Explicit admin chain** is **test-proven** in **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`** **:** bridge **`POST .../tour-bridge`**, **`POST .../activate-for-catalog`**, **`MiniAppCatalogService.list_catalog`** sees **`OPEN_FOR_SALE`** Tour **before** execution link exists **;** showcase **`POST .../publish`** **;** **`POST .../execution-link`** **;** landing **`MiniAppSupplierOfferLandingService`**, B11 **`resolve_sup_offer_start_mini_app_routing`**, review-package **`conversion_closure`** all **`true`**, **`next_missing_step`** **`null`** **.**
- **Moderation approve alone** **(packaging not `approved_for_publish`)** **does not** create **`SupplierOfferTourBridge`** **/** **`Tour`** **;** **`next_missing_step`** **`approve_packaging`** **.**
- **No** auto-publish **/** auto-activation **/** hidden ORM triggers **;** **booking/payment** services **unchanged** **(tests do not invoke orders/reservations/payments).**

---

## Checkpoint Sync — B10.x supplier offer → Tour → Mini App (2026)

**Docs-only.** **Canonical** **full** **record:** **[`docs/B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md)** **and** **short** **summary** **in** **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** **(Continuity** **Sync** **—** **B10.x).**

### Completed (accepted)
- **B9** **bridge** **design,** **B10** **bridge** **implementation,** **B10.1** **/** **B10.2** **(draft/activate** **for** **catalog),** **B10.3** **(full_bus** **fixed** **Mini** **App** **semantics),** **B10.4** **(package** **total** **on** **Layer** **A** **hold;** **not** **per-seat** **multiply),** **B10.5** **(boarding** **fallback** **for** **fixed** **full_bus).**
- **Production** **smoke** **(accepted):** **Supplier** **offer** **#8** **→** **Tour** **#4** **→** **`open_for_sale`** **→** **Reserve** **bus** **→** **preparation** **→** **reservation** **→** **payment** **entry** **/** **mock** **complete** **→** **My** **bookings.** **Mini** **App** **=** **execution** **truth.**

### Safety gates (unchanged)
- **`approved_for_publish`** **/** **B5** **packaging** **gates** **before** **bridge.**
- **Bridge** **creates** **`draft`** **(or** **links** **per** **B9);** **not** **auto** **catalog-open.**
- **Explicit** **activate-for-catalog** **/** **`open_for_sale`** **before** **customer** **listing.**
- **Telegram** **public** **channel** **post** **/** **“publish** **to** **Telegram”** **separate** **from** **Mini** **App** **catalog** **bookability** **(B10.2** **activation).**

### Postponed (tech debt)
- **If** **`ADMIN_API_TOKEN`** **or** **other** **secrets** **were** **exposed** **in** **logs** **/** **chat** **during** **smoke,** **rotate** **after** **smoke.** 

#### B10.6 — Telegram private bot: router / consultant (postponed, non-blocking)

- **Intent:** **Short** **summary,** **open** **exact** **Tour** **in** **Mini** **App** **(deep** **link),** **help** **/** **questions,** **custom** **trip** **/** **RFQ** **entry** **—** **not** **a** **second** **Mini** **App** **catalog** **view** **with** **duplicated** **tour** **body.**
- **Risk** **if** **unchanged** **long-term:** **bot** **duplicates** **Mini** **App** **truth** **or** **shows** **stale** **/** **full_bus**-**inconsistent** **copy** **(e.g.** **“sold** **out”,** **debug** **fallbacks).**
- **Accepted** **for** **now** **because** **Mini** **App** **execution** **path** **is** **strict** **and** **B10.x** **smoke** **passed.**
- **Revisit** **before:** **B11** **(Telegram** **deep** **link** **routing** **as** **product** **prioritizes** **it),** **or** **before** **major** **group** **/** **private** **bot** **promotion** **that** **leans** **on** **tour** **copy** **in** **the** **bot.**
- **Explicit** **decision** **(2026):** **no** **B10.6** **bot** **refactor** **in** **the** **B10.x** **doc-only** **/** **stabilization** **window;** **track** **here** **until** **a** **scoped** **ticket.**

#### B7.3 — Publish-safe media policy and pipeline (B7.3A accepted; implementation not done)

- **B7.1** **/** **B7.2** **shipped** **(metadata** **+** **`card_render_preview`** **plan**);** **no** **real** **download,** **storage** **bytes,** **or** **channel** **pixel** **publish** **in** **those** **slices.**
- **B7.3A** **(docs,** **2026** **):** **Publish-safe** **media** **policy** **accepted** **—** see **[`docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md`](SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md) **(B7.3A** **decision** **log** **),** **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) **(B7.3A** **section** **).** **Current** **decision:** **keep** **Telegram** **refs** **and** **media** **review** **metadata** **only** **for** **MVP;** **raw** **media** **is** **not** **publish-safe;** **`approved_for_card`** **(B7.1) ≠** **`publish_safe`** **(durable** **asset** **when** **exists** **);** **`publish_safe` ≠ `published`** **(marketing** **/** **showcase** **=** **separate** **explicit** **admin** **action** **).** **No** **Railway** **local** **filesystem** **as** **canonical** **durable** **store;** **future** **durable** **assets** **—** **object** **storage** **/** **S3-compatible** **when** **scoped.**
- **Risks:** **Telegram** **`file_id`** **not** a **public** **web** **URL;** **access** **can** **expire** **/** **be** **unsuitable** **for** **non-Telegram** **surfaces;** **future** **pipeline** **needs** **storage** **credentials,** **retention** **/** **deletion** **policy,** **and** **ACL** **discipline** **(wrong** **ACL** **=** **leak** **unpublished** **media** **).** **Generated** **cards** **must** **stay** **grounded** **in** **source** **facts.** **Real** **image** **moderation,** **size**/**type** **limits,** **copyright**/**quality** **—** **future** **scope.**
- **Revisit** **before:** **`getFile`** **/** **download;** **real** **card** **rendering;** **Telegram** **photo** **publication;** **Mini** **App** **showing** **real** **approved** **media** **assets;** **object** **storage** **/** **S3** **credentials.**
- **B7.3B** **(optional** **next** **,** **not** **automatic** **):** **metadata-only** **`publish_safe`** **stub** **in** **`packaging_draft_json`**, **no** **download.**
- **Status:** **open** **/** **accepted** **policy;** **implementation** **postponed** **until** **metadata** **/** **storage** **slice** **explicitly** **chosen.**

#### B8 — Recurring supplier offers (upcoming risks / invariants)

- **B8** **must** **create** **/** **link** **planned** **Tour** **instances** **through** **explicit** **service** **/** **admin** **/** **policy** **logic** **—** **not** **silent** **cron** **/** **ORM** **hooks** **/** **AI** **Tour** **rows.**
- **Preserve** **B9** **/** **B10** **separation:** **bridge** **(materialize** **instance)** **≠** **catalog** **activation** **≠** **Telegram** **publish** **≠** **booking** **/** **payment.**
- **No** **hidden** **bookability** **or** **activation:** **generated** **Tours** **default** **draft** **or** **otherwise** **inactive** **per** **policy** **unless** **a** **dedicated** **step** **implements** **safe,** **auditable** **activation** **rules.**
- **No** **booking** **/** **payment** **side** **effects** **during** **recurrence** **generation** **itself.**
- **No** **automatic** **Telegram** **channel** **publish** **from** **recurrence** **without** **explicit** **status** **/** **ops** **policy.**
- **Design** **first,** **then** **implementation** **—** **see** **B8** **row** **in** **BUSINESS** **plan** **and** **§5** **/** **§6** **dependencies.**

#### B8 slice 1 (draft-tours API) — shipped (2026)

- **Shipped:** **`POST` `/admin/supplier-offers/{id}/recurrence/draft-tours`** **—** see **[`docs/HANDOFF_B10X_TO_B8_RECURRING_SUPPLIER_OFFERS.md`](HANDOFF_B10X_TO_B8_RECURRING_SUPPLIER_OFFERS.md).**
- **No** **`SupplierOfferTourBridge`** **mutation** **in** **B8**; **B8** **reuses** **shared** **draft** **`Tour`** **mapping** from **`SupplierOfferTourBridgeService`** **+** **audit** **`supplier_offer_recurrence_generated_tours`.**
- **`start_offset_days=0`:** first instance can match the template (and B10-bridged) **departure**; still **separate** draft **`tour`**. **B8.3** **blocks** **duplicate** **`open_for_sale`** **for** **same** **source** **offer** **+** **departure** (see **below**). Handoffs: **[`docs/HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md`](HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md)**, B8.2: **[`docs/HANDOFF_B8_2_RECURRING_ACTIVATION_POLICY_TO_IMPLEMENTATION.md`](HANDOFF_B8_2_RECURRING_ACTIVATION_POLICY_TO_IMPLEMENTATION.md).**

#### B8 recurrence generation re-run idempotency

- **Current** **decision:** **Re-running** the **same** **recurrence** **input** **may** **create** **duplicate** **draft** `Tour` **rows.**
- **Acceptance** **now** **because** **generated** `Tour`s **stay** **draft** **and** **are** **not** **catalog**-**bookable** **without** **B10.2.**
- **Risk:** **admin** **list** **clutter;** **accidental** **duplicate** **activation** **attempts** ( **B8.3** **reduces** **the** **latter** **for** **same** **offer+departure** **).
- **Future** **options** **(open** **/** **non-blocking** **):** **`generation_batch_key`**, **uniqueness** **on** **`source_supplier_offer_id` +** **generated** **`departure_datetime`**, **admin** **preview** **before** **commit.**
- **Status:** **open** **/** **non**-**blocking.**

#### B8 duplicate active Tour guard (B8.3)

- **Current** **decision:** **Duplicate** **draft** `Tour` **rows** **are** **allowed.** **Duplicate** **`open_for_sale`** **B8**-**generated** ( **audit** **row** ) `Tour` **for** the **same** **source** **`SupplierOffer`** **+** **same** **`departure_datetime`** **are** **blocked** **at** **`activate_tour_for_catalog`**. **Conflicts** **include** a **sibling** **B8**-**active** `Tour` **and** the **B10** **primary** **bridged** **active** `Tour` ( **same** **offer+date** ).
- **Why** **accepted** **(MVP):** **avoids** **accidental** **duplicate** **live** **Mini** **App** **catalog** **rows.**
- **Risk:** **a** **legitimate** **second** **vehicle** **same** **route** **/** **date** **is** **blocked** **under** **one** **SupplierOffer** **without** **ops** **workaround** ( **see** **next** **subsection** ).
- **Status:** **implemented**; **ref** **commit** **`460ef50`** **(guard** **in** **service** **+** **tests** **).**

#### B8 legitimate second vehicle on same date

- **Current** **decision (MVP):** **B8.3** **blocks** **activating** a **second** **B8**-**audited** `Tour` **when** **another** **`open_for_sale`** `Tour` **matches** **same** **source** **offer+departure** ( **sibling** **B8** **or** **B10** **bridge** **).
- **Why** **accepted** **now:** **safer** **MVP;** **avoids** **confusing** **duplicate** **catalog** **cards.**
- **Preferred** **MVP** **/** **ops** **handling (no** **override** **in** **code** **):** **(1)** **If** **same** **product,** **raise** **capacity** **on** the **existing** **active** `Tour` ( **`seats_total`** / **`seats_available`** **coherent** **);** **(2)** **or** **separate** **`SupplierOffer`** / **`Tour`** **when** **the** **second** **run** **is** **operationally** **distinct.**
- **Future** **(not** **implemented** **):** **admin** **override** **+** **reason,** **audit,** **Mini** **App** **copy** **rules.**
- **Revisit** **when** **ops** **requires** **multiple** **vehicles** **for** one **offer**+**date.**
- **Status:** **open** **/** **future** **operational** **policy.** **Also** **[`docs/HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md`](HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md)** **(“Future** **vehicle”** **subsection** **).**

#### B7.3B / B10.6 / B11 (not B8.3)

- **B7.3B** **—** **optional** **metadata** **`publish_safe`** **stub** **(no** **download** **)** **—** only **if** **ops** **needs** **;** else **B7.3** **implementation** **stays** **at** **policy** **+** **existing** **metadata** **until** **storage** **slice.**
- **B10.6** **—** **Telegram** **private** **bot** **router** **/** **consultant** **:** **first** **slice** **`/start tour_<code>` →** **exact** **Mini** **App** **`/tours/{code}`** **:** **implemented.** **B10.6B** **—** **generic** **`/start`** **/** **`/tours`** **:** **router** **home** **no** **auto** **catalog** **cards** **.** **B10.6C** **—** **`router_home_body`** **/** **`assisted_booking_detail_note`** **copy** **polish** **(button** **alignment,** **full_bus** **wording** **)** **;** **no** **logic** **change** **.**
- **B11** **—** **`/start supoffer_<id>`** **deep** **link** **routing** **implemented** **(see** **`CHAT_HANDOFF`**, **§24** **Track** **3** **CTA** **).**

### Next safe step
- **B8** **(slice** **1** + **B8.2** + **B8.3** **):** **documented** **complete** for **continuity** **—** this **B8.4** **sync.**
- **B7.3A** **:** **media** **policy** **accepted** **(CHAT_HANDOFF,** **OPEN_QUESTIONS,** **B7** **design** **).**
- **Next** **(choose** **explicitly,** **not** **implied** **as** **approved** **):** **B7.3B** **stub** **/** **B7** **storage** **slice** **when** **ready** **;** **B11** **(deep** **links** **if** **product** **ready** **);** **B10.6** **(bot** **if** **priority** **);** **B12/B13** **further** **(showcase** **media** **`publish_safe`** **gate** **)** **when** **prioritized** **(** **read-only** **admin** **`GET /admin/supplier-offers/{id}/showcase-preview`** **—** **B13.4** **—** **done** **).** **B13.6** **(docs-only)** **—** **recommended** **preview-before-publish** **runbook** **(** **not** **enforced** **in** **code** **;** **no** **`preview_hash`** **/** **DB** **preview** **tracking** **in** **MVP** **)** **—** **[`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** **.** **B13.6A** **—** **runbook** **adds** **raw** **/** **AI-prepared** **copy** **/** **final** **deterministic** **preview** **layers** **;** **AI** **drafts** **not** **automatic** **publish** **source** **until** **explicitly** **wired** **and** **admin-approved** **.** **Track** **3** **showcase** **—** **B12/B13** **first** **implementation** **slice** **+** **B13.1** **branded** **RO** **emoji** **template** **`supplier_offer_showcase_message`** **(still** **text-only**, **safe** **`supoffer`**/**Mini** **App** **CTAs**, **no** **channel** **`/tours/{code}`**, **no** **photo**) **done** **(see** **`CHAT_HANDOFF`** **).**

---

## Checkpoint Sync — BUSINESS line: supplier offer → tour (B1–B13 design baseline, 2026-04-25)

**Docs-only** acceptance: forward **product** sequence for **supplier offer** intake, **AI** packaging, **admin** moderation, and **bridge** to **Layer A** **Tour** in the Mini App catalog. **V2** track numbering in `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` is **historical** delivery context; **B1**–**B13** in the BUSINESS plan is the **authoritative** ordered baseline for this domain.

**Closure note:** **BUSINESS** baseline **+** **B1** are **docs-accepted**; **B1** handoffs above. **B2** **(implementation)** **completed** **—** **data**/**persistence**/**contracts** **only**; **handoff:** [`docs/HANDOFF_B2_SUPPLIER_OFFER_CONTENT_DATA_UPGRADE.md`](HANDOFF_B2_SUPPLIER_OFFER_CONTENT_DATA_UPGRADE.md) **(migration** **`20260526_24`** **)**. **No** **AI,** **Tour,** **Mini** **App** **catalog,** **booking**/**payment,** **publish** **semantics,** or **supplier** **messaging** **in** **B2** **scope.**

### Accepted state
- **Roadmap (B1–B13):** [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) — includes **B1** intake + AI + moderation through **B13** smoke/production validation. **Core rule (accepted):** a **published** supplier offer **becomes** or **attaches** to a **Tour** visible in the Mini App **catalog** **only** via an **explicit** **bridge** (not silent ORM, not AI, not side-effect publication). **Supplier** provides **raw** **facts**; **AI** **draft** **packaging** **only**; **admin** **reviews**/**edits**/**approves**; **only** an **approved** **package** **may** **be** **published**. **AI** **draft-only** invariants: **no** invented **dates**/**prices**/**seats**; **no** **publishing**; **no** **booking**/**order**/**payment**; **no** **silent** **`Tour`** **creation**; **Layer** **A** **unchanged**.
- **B1 design (accepted):** [`docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md) — **§§1–8** cover **principle**, **intake** **requirements**, **dialog**, **AI** **packaging** **outputs**, **moderation** **flow**, **status** **model**, **guardrails**, **next** **steps** (**B2**, **B3**, **B4**, **B5** **admin** **moderation** **UI**, **B9** **offer**-**to**-**tour** **bridge**). **B2** **implemented** **extended** **persistence** **for** **intake**/**packaging** **metadata**; **tour** **link** **remains** **B9**/**B10** **(explicit** **bridge**).
- **B2 (implementation, completed):** same **BUSINESS** **rule** **set**; **see** **closure** **note** and [`HANDOFF_B2_SUPPLIER_OFFER_CONTENT_DATA_UPGRADE.md`](HANDOFF_B2_SUPPLIER_OFFER_CONTENT_DATA_UPGRADE.md).
- **B9 (design, accepted — 2026-04-26):** **Supplier** **offer** **→** **`Tour`** **bridge** **contract** **—** [`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md). **B10** **implements**; **no** **silent** **ORM/AI** **Tour** **create.**

### Next safe step (BUSINESS)
- **B3 — Supplier dialog upgrade** *(historical baseline; if that slice is already implemented in your branch, use the B7 / B9 lines below).*: Telegram **/supplier_offer** (and related) **intake** **FSM/UX** **—** **step**-**by**-**step**, **one** **question** **at** **a** **time**, **validation** **and** **`ready_for_moderation`** **criteria** per **B1** **§3**, **wiring** **to** **B2** **fields** **where** **product** **chooses** **(no** **Layer** **A,** **no** **publish** **logic** **change,** **no** **AI** **)**. **Source:** **B1** design **§3**; **BUSINESS** plan **B3** **row** in [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md).
- **B7.1 / B7.2 (photo & card, post-B6):** **Implemented** in-repo **(media_review** + **`card_render_preview`** **plan**); **next** **on** **that** **track** **(optional):** **B7.3** **publish-safe** **media** **—** see [`docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md`](SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md) **§8.**
- **B10 (offer → Tour bridge):** **Completed** **(B10** **+** **B10.1**–**B10.5** **smoke** **path).** **Record:** **[`docs/B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md).** **Forward** **BUSINESS** **priority** **(recommended):** **B8** **—** **recurring** **supplier** **offers**; **alternate** **B7.3.**

### B9 design checkpoint (supplier offer → Tour bridge, 2026-04-26)
**Docs-only** (no `app/`, no migrations in this gate). **Canonical design:** [`docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md) — **core** **principle,** **preconditions** **(packaging** **`approved_for_publish`,** **lifecycle** **gate,** **field** **completeness),** **create** **vs** **link** **to** **existing** **`Tour`,** **data** **mapping** **to** **`tours`/`tour_translations`,** **full_bus** **vs** **per_seat,** **Tour** **`draft`** **default,** **idempotency,** **audit,** **non-goals.** **B10** **implementation** **—** **completed** **(see** **[`docs/B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md)**).** **Relates** **to** **Y27** **`supplier_offer_execution_links`** **without** **replacing** **that** **table’s** **meaning.**

---

## Checkpoint Sync — B7 photo moderation & card generation (design only, 2026-04-25)

**Docs-only** checkpoint: **no** `app/`, **no** **migrations**, **no** **Telegram** **`getFile`**, **no** **image** **download**/**generation**/**channel** **publish** in this gate.

### Accepted state
- **B7** **design** **doc** **(canonical):** [`docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md`](SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md) — **photo** **state** **machine,** **media** **source** **rules,** **quality** **bar,** **card** **layout** **model,** **admin** **flows,** **JSON** **vs** **table** **tradeoffs,** **safety** **invariants,** **B7.1**–**B7.3** **slices.**
- **Depends** **on** **B6** **(branded** **`branded_telegram_preview`**, **cover** **refs,** **warnings).** B7 **does** **not** **change** **B5/B6** **“approve** **≠** **publish”** **semantics.**

### Next safe implementation
- **B7.3A** **—** **policy** **accepted** **(docs** **);** **B7.3** **implementation** **(download,** **S3,** **render,** **publish** **)** **not** **started** **—** see **B7.3** **subsection** **above** **in** **this** **file** **and** **[`docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md`](SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md) **(B7.3A** **).**
- **B7.3B** **—** **optional** **metadata** **stub;** **then** **future** **slice** **for** **storage** **or** **Telegram** **getFile** **only** **after** **explicit** **prompt.**
- **B7.1** **/** **B7.2** **(completed** **in** **repo):** **see** **CHAT_HANDOFF;** no **new** **B7.1/7.2** **gate** **items** **here.**

### Still open (by design in B7)
- **Minimum** **resolution** **threshold** (px) — **TBD** **in** **B7.1+** **implementation.**
- **Optional** **`supplier_offer_media`** **table** — **recommended** **when** **multi-asset** **or** **strong** **audit** **is** **required;** see **design** **§6.**

---

## Checkpoint Sync — Y37.5 operator decision expansion (2026-04-25)

**Docs-only acceptance** after **Y37.5** (second operator intent), closing the **Y37.4** + **Y37.5** operator **decision** intent chain. **No code, migration, or test changes** in this checkpoint.

### Accepted state
- **Y37.4** first operator intent **`need_manual_followup`** is **live** (admin API + Telegram internal ops).
- **Y37.5** added second intent **`need_supplier_offer`** (same service rules, idempotency, permissions as Y37.4).
- **Migration `20260501_20`** applied (adds **`need_supplier_offer`** to **`operator_workflow_intent`** enum).
- Telegram admin request detail shows **readable labels** for both intents: **Need manual follow-up**, **Need supplier offer** (buttons when **Owner = you**, **under_review**, **intent** unset; **Next step** after selection).
- **Raw enum display** for **`NEED_SUPPLIER_OFFER`** on the **Next step** line was **fixed** (must show human label, not `need_supplier_offer` string).
- Operator workflow intent remains **internal admin/ops only** (not a customer or supplier surface).
- **No** supplier action, RFQ automation, bridge, booking, payment, Mini App, customer notification, execution-link mutation, or identity bridge side effects in this slice.

### Tests (recorded for acceptance)
- `python -m pytest tests/unit/test_api_admin.py::AdminRouteTests::test_admin_custom_request_operator_decision`
- `python -m pytest tests/unit/test_telegram_admin_moderation_y281.py` — **54** passed (full file)

### Still genuinely open / postponed
- Semantics and automation for **`need_supplier_offer`** toward suppliers, RFQ, or bridge are **not** defined or implemented here.

### Next safe step pointer
- **Y38 — Supplier interaction gate (design, canonical):** **`docs/SUPPLIER_INTERACTION_GATE.md`**. It defines: operator workflow **decision-only**; **`operator_workflow_intent`** does **not** execute supplier logic; supplier interaction is a **separate future layer**; no automatic supplier messages, RFQ, bridge, booking, payment, Mini App, execution links, identity bridge, or customer notifications from intent; future supplier logic may **consume intent as input only** and must **not** be triggered **directly** by intent setting; Y36 / Y37.2 / Y37.4 / Y37.5 behavior **unchanged** by the gate file itself. (Legacy path **`docs/Y38_SUPPLIER_INTENT_INTERACTION_DESIGN_GATE.md`** redirects to the canonical file.)
- Before supplier/RFQ/bridge **implementation**, **accept** the Y38 gate and schedule **separate** minimal slices; **do not** auto-contact or notify suppliers from intent set alone. **Canonical “what’s next” after Y38:** `docs/SUPPLIER_INTERACTION_GATE.md` — section *Post–Y38: explicit next step* (Layer C is complete as implemented; in-code supplier automation is not next until a new gate + ticket).
- **Y39 (design, canonical):** **`docs/SUPPLIER_ENTRY_POINTS.md`** — **explicit** future entry types only; **`operator_workflow_intent`** and **`operator-decision`** are **not** triggers; first in-app supplier slice must **name** one **family** + **surface** (see that doc). **No** runtime in Y39; preserves Y38.
- **Y40 (design, canonical):** **`docs/SUPPLIER_EXECUTION_FLOW.md`** — after a Y39 start, **stages** (entry → validate → **audit** record → attempt → result → optional review); **operator intent = decision**; **entry = start**; **flow =** controlled pipeline; invariants: idempotency, audit, **retry** safety, no hidden triggers, **fail-closed**, explicit permissions. **No** `app/` in Y40; no messaging/RFQ/booking/Mini App/execution links/identity/notifications. **Cites** Y38 + Y39.
- **Y41 (design, canonical):** **`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`** — **logical** **execution request** + **attempt** + **result/audit** field lists; **status** set for requests; `operator_workflow_intent` **snapshot** on request, **not** live trigger, **not** primary execution state. **No** migrations/models in Y41. Forbids coupling to **orders**/**payments**/**bookings**, **Mini App**, **execution links**, **identity bridge**, **customer** notifications. **Cites** Y38–Y40.
- **Y42 (design, canonical):** **`docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md`** — who may **initiate** execution; **intent record** **≠** **execution** permission; **audit** and **fail-closed** rules; **no** **hidden** **DB** triggers. **No** `app/`. **Cites** Y38–Y41.
- **Y43 (runtime, persistence-only):** migration **`20260502_21`**, `supplier_execution_requests` + `supplier_execution_attempts`, ORM + `app/repositories/supplier_execution.py` validation. **No** **API**/**workers**/**messaging**; `operator_workflow_intent` **snapshot** only. **Cites** Y38–Y42.
- **Y45 (design, accepted):** **`docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md`** — **first** **trigger** = **admin** **explicit** **only**; **creates**/**validates** **`supplier_execution_request`** **only**; **does** **not** **contact** suppliers; **does** **not** **create** **`supplier_execution_attempt`** rows in this design slice; **preserves** **Y38**–**Y42**. **Y46** (runtime): **safe** **admin** **trigger** implemented — **`POST /admin/supplier-execution-requests`**. **Y47 (design, accepted):** **`docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md`** — **request** **≠** **attempt**; **attempts** **not** **created** **by** **Y46** **trigger**; **not** **automatic**; **separate** **explicit** **step**; **no** **messaging**/**API**/**workers**/RFQ/booking/**Mini** **App**/**links**/**bridge**/**notifications** in this **design**. **Y48 (runtime):** **`POST` …/supplier-execution-requests/{id}/attempts`**, **no** **outbound** **messaging** in that **handler** **(pending** + **channel** **none**)**. **Y49 (design, accepted):** **`docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md`** — **outbound** = **first** **external** **side** **effect**; **only** **in** **execution-attempt**-**tied** **send**; **permission** + **idempotency** + **audit**; **not** on **intent** / **request** **create** / **attempt** **row** **create** **alone**; **preserves** **Y38**–**Y48**; design **for** **Y50**. **Y50 (runtime, completed):** **Telegram**-**only** **outbound** **`POST` …/supplier-execution-attempts/{attempt_id}/send-telegram** — **`ADMIN_API_TOKEN`**, **explicit** **admin** **action** (**`X-Admin-Actor-Telegram-Id`**), **pending** **attempt** **only**, **required** **idempotency**; **migration `20260425_22`**: **`supplier_execution_attempt_telegram_idempotency`**, **`UNIQUE` (`supplier_execution_attempt_id`, `idempotency_key`)**; **no** **auto** / **Y46** / **Y48** / **intent** **sends**; **Y38**–**Y49** **guarantees** **preserved**. **Y51 (design, accepted):** **`docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md`** — **admin/operator** **visibility**; **audit** **hardening**; **retry** **principles**; **no** **automatic** **retries**; **no** **hidden** **retry** **on** **read**; **retry** (or re-send) **only** **after** **a** **future** **explicit** **gate**; **Y51** is **design**-**only** in **that** **file**. **Y38**–**Y50** **unchanged** in **meaning** as **documented** **in** this **line** and **Y51** **file**. **Y52 (runtime, completed):** **read/audit** **visibility** (no **retry** **execution**; **see** **Checkpoint** **Sync** **—** **Y52**). **Y53 (design-only, accepted checkpoint):** **`docs/SUPPLIER_MANUAL_RETRY_DESIGN.md`** — **manual** **retry** **only**; **no** **automatic** / **hidden** / **read**-**time** **retry**; **preferred** **new** **`supplier_execution_attempt`**, **not** **in**-**place** **resend** **by** **default**; **each** **retry** **send** **requires** **a** **new** **idempotency** **key**; **same** **`attempt_id` + `idempotency_key`** = **replay** / **no** **duplicate** **send** **(Y50)**. **Y54 (runtime, completed):** **`POST` …/supplier-execution-attempts/{attempt_id}/retry** — **manual** **retry** **implemented**; **new** **`supplier_execution_attempt`**; **no** **auto**-**send**; **failed**-**only** **eligibility**; **explicit** **admin**; **no** **Y50** **idempotency** **reuse** **in** **retry** **(new** **send** **=** **Y50** **+** **new** **key**)**; **audit** **`retry_from_supplier_execution_attempt_id`**, **`retry_reason`**, **`retry_requested_by_user_id`** **( **`20260526_23`**)**. **Y38**–**Y53** **unchanged** **in** **meaning**. **Handoff** **/** **next** **—** **Checkpoint** **Sync** **—** **Y54**.

---

## Checkpoint Sync — Y38 supplier interaction gate (post–Layer C boundary)

**Docs-only.** Y38 is **not** a runtime or migration. Source of truth: [`docs/SUPPLIER_INTERACTION_GATE.md`](SUPPLIER_INTERACTION_GATE.md) — **Post–Y38: explicit next step** (and boundary sections above it).

### Accepted state (Y38 boundary)
- **Layer C** (Y36 assign-to-me, Y37.2 `under_review`, Y37.4 / Y37.5 **`operator_workflow_intent`**) is **decision-only**: no execution, no side effects in supplier/RFQ/bridge/Layer A/customer/identity/execution-link paths.
- **`operator_workflow_intent`**: stored for **admin/ops**; **not** an action, **not** a trigger, **not** a workflow executor.
- **Supplier interaction** is **not** part of operator workflow, **not** implemented under Y38, and must **not** be **directly** triggered by intent. A **future** supplier layer may **read** intent only under a **separate** gate and implementation.

### Explicit next step (see gate file; do not guess elsewhere)
- **In-code supplier/RFQ automation or intent-as-trigger:** **not** next — use the table in `SUPPLIER_INTERACTION_GATE.md`.
- **When a supplier feature is scoped:** a **new** design gate and ticket first; then minimal code — still **uncoupled** from `POST .../operator-decision`.
- **Interim (ops):** manual / existing off-product processes remain OK; do not bypass the gate in **new** code.

### Still open
- The **concrete** first supplier-interaction feature (if any) is **TBD**; not defined by this checkpoint. **Entry-point rules** for any future implementation: **`docs/SUPPLIER_ENTRY_POINTS.md`** (Y39).

---

## Checkpoint Sync — Y39 supplier entry points (design-only, accepted)

**Docs-only.** No code, migration, or test changes. Complements and **does not replace** Y38.

### Accepted state
- **[`docs/SUPPLIER_ENTRY_POINTS.md`](SUPPLIER_ENTRY_POINTS.md)** (Y39): **Supplier interaction** (when any `app/` work exists) may **start** only at **explicit** entry types — e.g. admin/central **explicit** action, **scheduled/background** job, **external** trigger (webhook/integration), or **separate** operator “do” action; **not** from recording intent alone. Entry **surface** categories: **explicit API**, **background worker**, **admin/Telegram admin action** (design **types** only until implemented).
- **`operator_workflow_intent`** and **`POST /admin/custom-requests/{id}/operator-decision`** are **not** **triggers** for supplier-impacting execution; they remain **Layer C** persistence (Y38 boundaries **preserved**).
- Future **implementation** tickets for supplier automation must **name one** Y39 **entry family** and one **surface**; must satisfy invariants: **idempotency**, **auditability**, **explicit invocation**, **no hidden triggers** (per `SUPPLIER_ENTRY_POINTS.md` §5–7).
- This checkpoint: **no** supplier messaging, **no** new RFQ implementation, **no** booking/order/payment, **no** Mini App, **no** execution links, **no** identity bridge, **no** notifications.

### Next safe step
- **Pipeline design (Y40):** see **`docs/SUPPLIER_EXECUTION_FLOW.md`** for **stages** and **invariants**; implementation must align when code ships. **Data contract (Y41):** **`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`** before persisting execution rows.
- When a first **in-app** supplier-interaction slice is **scoped:** open a ticket that cites **Y38** + **Y39** + **Y40** + **Y41** + **Y42**; **name** **entry family** + **surface**; map to **Y40** **stages** and **Y41** **records**; **Y42** **permission/audit** and **fail-closed** rules; add idempotency/audit; **do not** wire `operator-decision` as executor.

---

## Checkpoint Sync — Y40 supplier execution flow (design-only, accepted)

**Docs-only.** Complements Y38 and Y39; **no** `app/`, `tests/`, or migrations. Source: [`docs/SUPPLIER_EXECUTION_FLOW.md`](SUPPLIER_EXECUTION_FLOW.md).

### Accepted state
- **Distinction (Y40):** `operator_workflow_intent` = **decision data**; **Y39** entry = **start signal**; **execution flow** = **controlled pipeline** after the start.
- **Logical stages (future code):** explicit entry point → **validation** → **execution request / audit** record → **supplier action attempt** → **result recording** → **operator/admin review** (if needed). Concrete persistence/APIs **TBD** per implementation ticket.
- **Safety invariants (required when implemented):** idempotency, **auditability**, **retry** safety, **no hidden triggers**, **fail-closed** behavior, **explicit permissions**.
- **May eventually (only in a future slice, not in Y40):** prepare supplier **contact**; **send** message / **record** response — when **explicitly** in scope. **Y40** itself adds no runtime.
- This checkpoint: **no** supplier **messaging**, **no** new **RFQ** implementation, **no** **booking/order/payment**, **no** **Mini App**, **no** **execution links**, **no** **identity bridge**, **no** **customer** notifications.

### Next safe step
- **Data contract (Y41):** see **`docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md`** before the first **migration** implementing execution persistence.
- First **in-app** supplier slice: ticket cites **Y38 + Y39 + Y40 + Y41 + Y42**; **name** one Y39 family + surface; **map** to Y40 **stages** and Y41 **records** and Y42 **RBAC/audit**; still **uncouple** from `POST .../operator-decision` as **executor**. **Migrations** = separate ticket after this design is accepted for implementation.

---

## Checkpoint Sync — Y41 supplier execution data contract (design-only, accepted)

**Docs-only.** **No** Alembic, **no** models, **no** `app/` or `tests/`. Complements Y38–Y40.

### Accepted state
- **Logical** **execution request** record fields: `id`, `source_entry_point`, `source_entity_type`, `source_entity_id`, `operator_workflow_intent_snapshot`, `requested_by_user_id`, `status`, `idempotency_key`, `created_at`, `updated_at` (see doc for meaning).
- **Logical** **execution attempt** record fields: `id`, `execution_request_id`, `attempt_number`, `channel_type`, `target_supplier_ref`, `status`, `provider_reference`, `error_code`, `error_message`, `created_at`.
- **Logical** **result/audit** fields: `final_status`, `completed_at`, `completed_by`, `raw_response_reference`, `audit_notes`.
- **Request `status` boundaries** (non-Layer-C): `pending`, `validated`, `blocked`, `attempted`, `succeeded`, `failed`, `cancelled`.
- **Intent:** `operator_workflow_intent` may be **snapshotted**; **must not** be a **live trigger** or **primary** execution state.
- **Separation:** no mutation of **orders** / **payments** / **bookings**; no **Mini App** dependency; no **execution link** or **identity bridge** mutation; no **customer** notifications from this line by default. **No** RFQ schema added by Y41.

### Next safe step
- **Y43 delivered:** see **Checkpoint Sync — Y43** and `CHAT_HANDOFF` (migration **`20260502_21`**, ORM, repository). **RBAC** at **entry** is still a **future** slice; snapshot column does **not** add triggers.
- **Permission & audit (Y42)** remains the design for when **entry** and **read** **APIs** ship.

---

## Checkpoint Sync — Y42 supplier execution permission & audit (design-only, accepted)

**Docs-only.** **No** Alembic, **no** models, **no** `app/` or `tests/`. Complements Y38–Y41.

### Accepted state
- **Initiation (future):** allowed classes — **central admin** explicit, **authorized operator** explicit (if policy), **authorized system job**, **authenticated external** integration; **not** from intent **alone** or from **unauthenticated** callers by default.
- **Permission rules:** **assigned** operator may **record** `operator_workflow_intent` (Layer C); that is **not** **supplier-execution** permission; execution requires **separate** check and **explicit** entry (Y39); `operator-decision` is **not** an execution **endpoint**.
- **Audit (must be capturable per run):** **who** initiated; **entry** point; **source** entity; **intent** **snapshot** if used; **idempotency** key; **validation** result; **attempt/result** state; **error** on **block/fail** (Y41 field alignment).
- **Fail-closed:** missing **permission**, **source** entity, **idempotency** (when required), or **ambiguous** source → **block**; **stale/invalid** **intent** **snapshot** must **not** **auto-refresh** into **execution** or revive terminal runs without a **new** **explicit** start.
- **Separation:** `operator_workflow_intent` = **context** only; **no** hidden **triggers** from **DB** **events/ORM** on intent.
- This checkpoint: **no** **messaging**, **no** new **RFQ**, **no** **booking/order/payment** mutation, **no** **Mini App**, **no** **execution links**, **no** **identity bridge**, **no** **customer** notifications.

### Next safe step
- **Y43 (persistence) implemented** — see Y43 checkpoint. **Next:** **entry** **handler** / **read** **API** (if any) with **Y42** **checks**, **or** keep tables **dormant**.

---

## Checkpoint Sync — Y43 supplier execution persistence (persistence-only, accepted)

**Schema + ORM + repository;** **no** public **HTTP**/**Telegram** **execution** **routes** in this slice, **no** **workers**, **no** **messaging**. **`operator_workflow_intent`**: **column** = **snapshot** on request row only; **no** **DB** **triggers** on `custom_marketplace_requests` **intent**.

### Accepted state
- **Migration `20260502_21`:** `supplier_execution_requests`, `supplier_execution_attempts` + new **enums**; **UNIQUE** `idempotency_key`; **CHECK**s for **idempotency** and `source_entity_id`. **`operator_workflow_intent`**: reuse PG **type** for **snapshot** only.
- **Code:** `app/models/supplier_execution.py`, `app/models/enums.py` (Y43 **StrEnum**s), `app/repositories/supplier_execution.py`, `app/models/__init__.py` exports.
- **Tests:** `tests/unit/test_supplier_execution_persistence.py`. **`POST .../operator-decision`**, **Mini** **App**, **Layer** **A** **tables** unchanged. **no** **customer** **notifications** from this slice.

### Next safe step
- **Y45**–**Y54** and **`CHAT_HANDOFF`**. **Y50**–**Y54** — see **Checkpoint Sync** **—** **Y50** **through** **Y54**.

---

## Checkpoint Sync — Y45 controlled execution trigger (design-only, accepted)

**Docs-only** acceptance of the **first** **trigger** specification. Source: [`docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md`](SUPPLIER_EXECUTION_TRIGGER_DESIGN.md). **Does** **not** **by** **itself** add or change **`app/`** code; **complements** Y38–Y42.

### Accepted state
- **First** **allowed** **trigger** (in this slice): **admin** **explicit** **action** **only** — mapped to **`source_entry_point`** **`admin_explicit`**; **not** **`POST /admin/custom-requests/{id}/operator-decision`**, **not** Layer C **intent** **write** as **start** signal (Y38, Y39).
- **What** the **trigger** **does** **when** **implemented**: **create** / **validate** a **`supplier_execution_request`** row per Y41 (and Y42 checks at the **entry**); **does** **not** **contact** suppliers; **does** **not** **create** **`supplier_execution_attempt`** rows in this **design** **slice**; **no** execution **runtime**, **no** **messaging**, **no** new **RFQ** **implementation**, **no** booking/order/payment, **no** Mini App, **no** execution **links**, **no** identity **bridge**, **no** **notifications**.
- **Y38**–**Y42** **boundaries** **preserved**: intent **≠** **execution**; **explicit** **entry** only; Y40 **flow** **integrity** for **stages** **1–3** on **trigger**; Y41 **contract**; Y42 **permission** + **audit** + **fail-closed**.

### Next safe step
- **Y46** **ships** the **safe** **admin** **trigger** — **`POST /admin/supplier-execution-requests`** (see **`tests/unit/test_api_admin_supplier_execution.py`** and **`CHAT_HANDOFF`**). **Y47** **attempt** **layer** **design** is **accepted** — see **Checkpoint Sync — Y47** below. **Next:** **Y48** **safe** **`supplier_execution_attempt`** **creation** (still **no** **outbound** **messaging**).

---

## Checkpoint Sync — Y47 supplier execution attempt (design-only, accepted)

**Docs-only** acceptance. Source: [`docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md`](SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md). **Complements** Y38–Y45 / **Y46**; **no** new **`app/`** in this checkpoint.

### Accepted state
- **Distinction:** **`supplier_execution_request`** = **intention** / **run** **anchor** (Y45/**Y46** **admin** **trigger**); **`supplier_execution_attempt`** = **one** **try** (Y40 **stage** **4** **unit**), **not** the **same** as **request**.
- **Attempts** are **not** **inserted** **by** the **Y46** **trigger**; **not** **automatic** from **intent** or **unrelated** **rows**; **not** from **hidden** **triggers** — only a **separate** **explicit** **entry** in a **future** **implementation** **ticket** (Y48+).
- This **design** **does** **not** add: supplier **messaging** **implementation**, **supplier** **HTTP**/**API** **clients**, **workers**, new **RFQ** **automation**, **booking**/**order**/**payment** **mutations**, **Mini** **App** **changes**, **execution** **link** **mutation**, **identity** **bridge** **changes**, **customer**/**supplier** **notifications** **pipelines**. **`operator-decision`** **unchanged** by this **doc** **alone**.

### Next safe step
- **Y48** **shipped** — **`CHAT_HANDOFF`**. **Y50**–**Y54** in **`OPEN_QUESTIONS`**. **Y54** **completed** — **Checkpoint Sync** **—** **Y54**.

---

## Checkpoint Sync — Y49 supplier outbound messaging (design-only, accepted)

**Docs-only** acceptance. Source: [`docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md`](SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md). **No** **`app/`** **sends** in this checkpoint.

### Accepted state
- **What** it **is** — **outbound** **supplier** **messaging** is the **first** **genuine** **external** **irreversible** **side** **effect** in the **Y38**–**Y48** **line** ( **real** **contact** to **suppliers** / **partner** **channels** ), **not** **DB**-**only** **rows** **alone**.
- **Where** **allowed** **(design)** — **only** **in** **execution-attempt**-**tied** **outbound** **logic**; **never** **in** **Y45**/**Y46** **trigger**; **never** **in** **request** **creation** **alone**; **never** **in** **Y48** **attempt** **row** **insert** **as** **a** **send** **without** a **further** **explicit** **Y50**+ **entry** **citing** this **doc**.
- **Required** for **sends** — **explicit** **permission** (Y42), **idempotency** ( **per**-**send** **scope** ), **audit** **trail** ( **correlation** / **outcome** on **`supplier_execution_attempt`** or **policy**-**linked** **storage**).
- **Must** **not** **fire** from — **`operator_workflow_intent`** ( **vs.** **Y38**), **`operator-decision`**, **request** **create**, **or** **attempt** **create** **alone**; **not** **automatic** / **hidden** **triggers** (Y39, Y47).
- **Y38**–**Y48** **design**+**shipped** **slices** **preserved**; this **file** does **not** add **RFQ**/**order**/**Mini** **App**/**execution** **links**/**identity**/**default** **customer** **notifications** (see **Y49** **§7**).

### Next safe step
- **Y50** **shipped** — **Checkpoint Sync — Y50**. **Y51**–**Y54** — **checkpoints** **below**.

---

## Checkpoint Sync — Y50 controlled Telegram supplier messaging (runtime, completed)

**Implementation** **merged**: **outbound** **Telegram** **messaging** **per** **`docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md`** (Y49) and **`CHAT_HANDOFF`**.

### Accepted state
- **What** **shipped** — **Telegram**-**only** **send** path: **`POST` `/admin/supplier-execution-attempts/{attempt_id}/send-telegram`**. **Requires** **`ADMIN_API_TOKEN`**, **explicit** **admin** **actor** (**`X-Admin-Actor-Telegram-Id`**), **pending** **`supplier_execution_attempt`**, **mandatory** **idempotency** (**`Idempotency-Key`**, **`X-Idempotency-Key`**, **or** **body** **`idempotency_key`**). **Succeeds**/**fails** **on** the **attempt** **row**; **`provider_reference`** stores **message** **id** **on** **success**.
- **Deduplication** — **`supplier_execution_attempt_telegram_idempotency`** (migration **`20260425_22`**), **constraint** **`UNIQUE` (`supplier_execution_attempt_id`, `idempotency_key`)**; **replay** **does** **not** **call** **Telegram** **again** **for** the **same** **successful** **logical** **send**.
- **Constraints** **(Y38**–**Y49** **unchanged** **in** **meaning**)** — **no** **automatic** **messaging**; **no** **sends** **from** **Y46** **request** **creation** **or** **Y48** **attempt** **row** **creation**; **no** **intent**-**triggered** **or** **`operator-decision`** **sends**; **no** **RFQ**/**booking**/**order**/**payment** **mutation**; **no** **Mini** **App**; **no** **execution** **link**; **no** **identity** **bridge**; **no** **customer** **notifications**; **no** **fan**-**out**; **no** **worker** **retry** **pipeline** in **this** **slice**.

### Next safe step
- **Y51**–**Y54** **—** see **checkpoints** **—** **Y51** **through** **Y54** (below).

---

## Checkpoint Sync — Y51 supplier messaging visibility / audit / retry (design-only, accepted)

**Docs-only** acceptance. Source: [`docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md`](SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md). **Complements** Y49 + Y50; **adds** **no** new **send** **endpoint** in **this** **checkpoint**.

### Accepted state
- **What** it **covers** — **admin/operator** **visibility** **requirements** for **messaging** **outcomes**; **audit** **hardening** ( **who** / **when** / **endpoint** / **target** / **result** / **failure** **reason** ); **retry** **principles** as **pattern**+**safety** only.
- **Retry** **stance** — **no** **automatic** **retries**; **no** **hidden** **retry** **on** **read** (e.g. **GET** must **not** **re**-**invoke** **send**); **manual** or **actionable** **retry** / **re-send** **only** **after** a **future** **explicit** **product**+**code** **gate** (separate from **Y51**); **Y38** / **Y45** / **Y47** / **Y48** / **Y50** **trigger** **rules** **unchanged** **in** **meaning**.
- **Y50** **remains** the **sole** **Telegram** **send** path **(until** a **separate** **gate** **adds** **channels** / **ops**); **Y51** does **not** add **RFQ** / **booking** / **Mini** **App** / **execution** **links** / **identity** **bridge** / **customer** **notifications**.

### Next safe step
- **Y52**–**Y54** **—** see **checkpoints** **below**.

---

## Checkpoint Sync — Y52 supplier messaging read / audit visibility (runtime, completed)

**Read-side** only; **no** **new** **send** or **retry** **execution** **path** in this slice. **Handoff:** [`docs/HANDOFF_Y52_SUPPLIER_MESSAGING_READ_AUDIT_VISIBILITY.md`](HANDOFF_Y52_SUPPLIER_MESSAGING_READ_AUDIT_VISIBILITY.md).

### Accepted state
- **Y50** **send** path **unchanged**; **admin** **reads** **expose** **attempt** **status**, **`target_supplier_ref`**, **`provider_reference`**, **error** **fields**, **idempotency** **evidence**, **timestamps** **as** **scoped** in **Y52** **implementation** **(align** **Y51** **visibility** **goals**)**.  
- **No** **retry** **execution**; **no** **automatic** **retry**; **no** **hidden** **retry** **on** **read**.  
- **Still** **out** **of** **scope** **(unless** **separate** **gate**)**:** **booking**/**order**/**payment**, **Mini** **App**, **execution** **links**, **identity** **bridge**, **default** **customer** **notifications**.

### Next safe step
- **Y53** **accepted** — see **Checkpoint** **Sync** **—** **Y53** (below). **Y54** **completed** — **Checkpoint** **Sync** **—** **Y54** (below).

---

## Checkpoint Sync — Y53 supplier manual retry (design-only, accepted)

**Y53** = **design-only** **accepted** **checkpoint** ( **no** **runtime** **or** **migrations** in **this** **gate**). **Source** **+** **handoff:** [`docs/SUPPLIER_MANUAL_RETRY_DESIGN.md`](SUPPLIER_MANUAL_RETRY_DESIGN.md), [`docs/HANDOFF_Y53_SUPPLIER_MANUAL_RETRY_DESIGN.md`](HANDOFF_Y53_SUPPLIER_MANUAL_RETRY_DESIGN.md).

### Accepted state
- **Manual** **retry** **only** — **explicit** **admin** **(or** **Y42**-**class** **operator** **as** **policy** **allows**)**; **not** a **side** **effect** **of** **unrelated** **work**.  
- **No** **automatic** **retry**; **no** **hidden** **retry**; **no** **retry** **on** **read** ( **list** / **GET** / **detail** must **not** **invoke** **send** ).  
- **No** **retry** **from** **Y46** **request** **create**, **Y48** **attempt** **create** **alone**, **`operator_workflow_intent`**, **or** **`POST` …/operator-decision** **(align** **Y49** **/** **Y51**)**.  
- **Preferred** **model** — **create** **a** **new** **`supplier_execution_attempt`** **for** a **retry**; **do** **not** **resend** a **failed** **attempt** **in**-**place** **by** **default** **(Y47**)**.  
- **Idempotency** — **each** **new** **retry** **send** **requires** **a** **new** **idempotency** **key** **(Y50** **per**-**`supplier_execution_attempt`** **scope**)**. **The** **same** **`attempt_id` + `idempotency_key`** = **Y50** **replay** **/ **no** **duplicate** **Telegram** **message**.  
- **Audit** **minimums** — **`original_attempt_id`**, **`retry_attempt_id`**, **`retry_requested_by`**, **`retry_reason`**, **timestamp**, **idempotency** **key** ( **Y54** **persists** **link** + **reason** + **requester** **on** **new** **attempt** **row**; **send**-**time** **idempotency** **still** **Y50** **`supplier_execution_attempt_telegram_idempotency`** ).  
- **Still** **forbidden** **(align** **Y49** **/** **Y51**)**:** **background** **retry** **workers**; **default** **customer** **notifications**; **booking** **/** **payment** **/** **Mini** **App** **/** **execution** **link** **/** **bridge** **changes** **as** **retry** **side** **effects**.

### Next safe step
- **Y54** **completed** **—** see **Checkpoint** **Sync** **—** **Y54** (below).

---

## Checkpoint Sync — Y54 supplier manual retry (runtime, completed)

**Handoff:** [`docs/HANDOFF_Y54_SUPPLIER_MANUAL_RETRY_IMPLEMENTATION.md`](HANDOFF_Y54_SUPPLIER_MANUAL_RETRY_IMPLEMENTATION.md). **Y53** **design** **(prerequisite):** [`docs/SUPPLIER_MANUAL_RETRY_DESIGN.md`](SUPPLIER_MANUAL_RETRY_DESIGN.md).

### Accepted state
- **Implemented** **behavior** **—** **manual** **retry** **is** **implemented**; **retry** **creates** **a** **new** **`supplier_execution_attempt`** **(next** **`attempt_number`**, **pending**)**; **retry** **does** **not** **send** **Telegram** **automatically**.  
- **Endpoint** **—** **`POST` `/admin/supplier-execution-attempts/{attempt_id}/retry`** **with** **`retry_reason`**, **`ADMIN_API_TOKEN`**, **`X-Admin-Actor-Telegram-Id`**.  
- **Constraints** **—** **retry** **only** **for** **`failed`** **original** **attempts**; **explicit** **admin** **action** **only** **(not** **intent** **/** **read** **/** **request** **or** **attempt** **create** **alone**)**; **retry** **does** **not** **reuse** **Y50** **send** **idempotency** **—** **outbound** **message** **requires** **`POST` …/send-telegram` (Y50)** on **the** **new** **attempt** **with** **a** **new** **idempotency** **key** **(Y50** **same** **`attempt_id` + `idempotency_key`** **=** **replay** **/** **no** **duplicate** **send** **for** **that** **send** **only**)**.  
- **Audit** **(migration** **`20260526_23`**, **on** **the** **new** **attempt** **row):** **`retry_from_supplier_execution_attempt_id`**, **`retry_reason`**, **`retry_requested_by_user_id`**.  
- **Y38**–**Y53** **—** **all** **prior** **rules** **and** **forbidden** **surfaces** **preserved** **(unchanged** **in** **meaning**)**; **Y54** **does** **not** **expand** **into** **booking** **/** **order** **/** **payment**, **Mini** **App**, **execution** **links**, **identity** **bridge**, **customer** **notifications**, **or** **fan**-**out**.

### Next safe step
- **Execution** **layer** **(Y38**–**Y54)** **—** **treat** **as** **MVP** **complete** **/ **closed** **for** **this** **scope** **(document** **if** **needed**)**. **Then** **—** **supplier** **onboarding** **/** **identity** **/** **other** **product** **flows** **(not** **ad** **hoc** **cross**-**layer** **work** **without** **gates**)**. **See** **`CHAT_HANDOFF`** **“Next** **safe** **order”** **item** **1**.

---

## Checkpoint Sync — Y36.2 + Y36.2A + Y36.3 (2026-04-25)

Documentation stabilization after **operator assignment** runtime on custom marketplace requests (RFQ) and the production **SQLAlchemy mapper** recovery. **No code changes** in this checkpoint.

### Accepted runtime state (Y36.3)
- **Y36.2 — Assign to me** works for **custom marketplace requests** (admin API + Telegram).
- **Y36.2A** fixed the production **SQLAlchemy mapper** crash (symmetric **`User`** ↔ **`CustomMarketplaceRequest`** relationships).
- **Railway migration** for RFQ assignment columns is **applied** (**`20260429_18`**).
- **Telegram admin requests** UI (**`/admin_requests`**) shows **Owner** / **Assign to me** / **Assigned to you** as implemented.

### Resolved and accepted (not open questions)
- **Y36.2 — Assign to me** is implemented for **custom marketplace requests** only: **`POST /admin/custom-requests/{request_id}/assign-to-me`** (actor **`X-Admin-Actor-Telegram-Id`** → **`User.id`**); Telegram **`/admin_requests`** shows **Owner** and **Assign to me**; assignment fields are internal **`users.id`**; request **lifecycle `status`** is unchanged by assignment in this slice; **bookings/payment**, **Mini App `My requests` privacy**, **supplier routes**, **execution links**, and **identity bridge** were **not** changed for this feature.
- **Migration `20260429_18`** added **`assigned_operator_id`**, **`assigned_by_user_id`**, **`assigned_at`** on **`custom_marketplace_requests`** (FKs to **`users.id`**). **Production (Railway):** migration applied via **`railway ssh`** with **`python -m alembic upgrade head`**, head verified with **`python -m alembic current`**.
- **Y36.2A — ORM regression fix:** `CustomMarketplaceRequest.assigned_operator` required **`User.ops_assigned_custom_marketplace_requests`**; the **`assigned_by`** side now has a symmetric inverse (**`User.ops_assigned_custom_marketplace_requests_by_actor`**). **`tests/unit/test_model_mappers.py`** calls **`configure_mappers()`** after importing **`app.models`**. **No** additional migration in Y36.2A.

### Production smoke (recorded)
- Bot recovered after deploy; **`/admin_requests`** works; request detail shows **Owner**; **Assign to me** updates display to **Assigned to you** for the acting operator.

### Tests (as confirmed for this handoff)
- `python -m compileall app tests/unit/test_api_admin.py tests/unit/test_telegram_admin_moderation_y281.py`
- `python -m pytest tests/unit/test_api_admin.py -k "assign"` — 21 passed
- `python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops"` — 4 passed

### Still genuinely open / postponed
- **Reassign**, **unassign**, and full assignment **history/audit** UI remain **postponed** (see **`docs/OPERATOR_ASSIGNMENT_GATE.md`**) until separately gated.

### Next safe step pointer
- **Y36.4** only after this docs checkpoint is **committed, pushed, and deployed**. **Y36.4** may cover operator-assignment **UI polish** or **list filtering** on admin/ops read surfaces. **Do not** implement **reassign** / **unassign** without a **separate design gate** (out of scope for Y36.4 unless explicitly accepted). **Update:** the **Y36.5** section below is the post-**Y36.4** **acceptance** checkpoint; treat it as the current pointer for this track.

---

## Checkpoint Sync — Y36.5 (2026-04-25)

**Docs-only acceptance** after **Y36.4** production smoke, closing the **Y36.2** (runtime) + **Y36.2A** (ORM) + **Y36.4** (Telegram UI) operator-assignment chain. **No code changes** in this checkpoint.

### Accepted state
- **Y36.2 — Assign to me** for **custom marketplace requests** (admin API + Telegram **`/admin_requests`**). Assignment stores internal **`users.id`** via **`assigned_operator_id`** and **`assigned_by_user_id`** (and **`assigned_at`**); not raw Telegram id in those columns.
- **Migration `20260429_18`** is **applied on Railway production** (operational path as run in production: **`alembic upgrade head`**, head verified e.g. **`alembic current`**).
- **Request lifecycle / `CustomMarketplaceRequest.status`** is **not** changed by assignment in this slice.
- **Y36.2A —** SQLAlchemy **mapper** crash fixed with symmetric **`User` ↔ `CustomMarketplaceRequest`** relationships (**`ops_assigned_custom_marketplace_requests`**, **`ops_assigned_custom_marketplace_requests_by_actor`**). **Mapper smoke:** **`tests/unit/test_model_mappers.py`** (`import app.models` + **`configure_mappers()`**).
- **Y36.4 —** Telegram **UI polish** accepted: list shows **Owner** early; unassigned owner **—**; self on list = compact **you**; detail = **Assigned to you** when you own it; **Assign to me** is **not** shown after assignment.
- **Production smoke (recorded):** **`/admin_requests`** works; detail shows **Owner**; **Assign to me** updates **Owner** to **Assigned to you**; **Railway** logs: webhook **200**, **no** mapper / `InvalidRequestError` class of failures.

### Tests (recorded for acceptance)
- `python -m compileall app tests/unit/test_api_admin.py tests/unit/test_telegram_admin_moderation_y281.py`
- `python -m pytest tests/unit/test_api_admin.py -k "assign"` — **21** passed
- `python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops"` — **8** passed when the full `admin_ops` slice is run (a narrower local run may show **4**)
- Y36.4-focused coverage lives in the same `admin_ops` tests; full slice **8** passed in acceptance run

### Next safe step pointer
- **Do not** implement **reassign** / **unassign** (or ad hoc **resolve** / **close**) without a **dedicated design gate** first.
- **Recommended next (pick one, product-prioritized):** **Y37** — operator custom-request **workflow** design gate, or **Y36.6** — small **formatting** polish (e.g. request dates / customer summary line) without changing assignment semantics.
- **Execution links**, **Mini App**, **Layer A** booking/payment, **supplier** routes, and **identity bridge** remain out of scope for this assignment track unless explicitly scoped.

---

## Checkpoint Sync — UVXWA1 (2026-04-19)

Documentation synchronization checkpoint after completion of Tracks **5g.4a–5g.4e**, **5g.5**, **5g.5b**, **U1/U2/U3**, **V1–V4**, **W1–W3**, **X1/X2**, **A1**, plus key hotfixes and production fixes.

### Resolved and accepted (not open questions)
- **Mode 2 catalog whole-bus line** (5g.4a–5g.4e, 5g.5, 5g.5b) is implemented and accepted for current scope.
- **Mode 3 customer, ops/admin read-side, messaging, supplier clarity** blocks (U/V/W/X) are implemented and accepted.
- **A1 admin operational UI surface** is implemented as additive read-only internal UX over existing admin custom-request APIs.
- **Hotfixes accepted:** supplier-offer `/start` payload/title; request-detail empty-control crash; production schema drift fix for `custom_request_booking_bridges`; custom request submit success-state; custom request **422** validation visibility.

### Compatibility baseline (must remain true)
- **Layer A** remains booking/payment source of truth.
- **`TemporaryReservationService`** remains the single hold path.
- **`PaymentEntryService`** remains the single payment-start path.
- **UI layers** consume read-side truth and must not duplicate backend business rules.
- **Mode 2** and **Mode 3** remain separate semantics.

### Still genuinely open / postponed
- Existing debt items in this file remain open unless explicitly marked closed in their own sections (payment-provider integration, admin payment mutation design gate, FSM storage hardening, notification expansion, etc.).
- Broader lifecycle/payment/bridge redesign is **postponed** and out of scope for UVXWA1 checkpoint sync.
- Historical prompt files are retained as implementation trail; they are **not** a mass-update active checklist.

### Next safe step pointer
- Continue with a narrow **A2** admin operational usability pass (read-side/UI only), without changing RFQ/bridge/payment/booking semantics.

---

## Checkpoint Sync — Y2.3 + Y2.1a (2026-04-20)

### Resolved and accepted (not open questions)
- Supplier v1 operational loop is now implemented in narrow scope: onboarding gate, supplier offer intake, moderation/publication actions, retract path, supplier read-side list, and supplier Telegram lifecycle notifications.
- Approve and publish are explicitly separate semantics (`approve != publish`); reject reason is supplier-visible.
- Supplier onboarding legal/compliance minimum identity fields are required on the pending-approval path: `legal_entity_type`, `legal_registered_name`, `legal_registration_code`, `permit_license_type`, `permit_license_number`.

### Compatibility baseline (must remain true)
- No Layer A booking/payment semantics change.
- No RFQ/bridge execution semantics change.
- No payment-entry/reconciliation semantics change.
- No Mode 2/Mode 3 merge.

### Explicitly accepted compatibility nuance
- Legacy already-approved suppliers remain operationally compatible.
- Existing approved supplier rows may still have NULL in new legal fields by design.
- Legal completeness guard applies to approving pending suppliers, not retroactive forced migration of all approved suppliers.

### Still open / postponed
- Clean-room live verification for a brand-new supplier completing the full legal-hardened onboarding path in production is still pending.
- Legal document upload/KYC file workflow remains postponed.
- Full compliance audit subsystem remains postponed.
- Supplier analytics/dashboard portal rewrite remains postponed.
- Full supplier org/RBAC redesign remains postponed.

### Next safe step pointer
- Narrow supplier operational visibility / basic stats (read-side only, no PII, no booking/payment controls).

---

## Checkpoint Sync — Y24 + Y25 (2026-04-20)

### Resolved and accepted (not open questions)
- Supplier read-side now includes narrow operational visibility in **`/supplier_offers`** for supplier-owned offers only.
- Supplier read-side now includes narrow operational alerts in **`/supplier_offers`** with deterministic non-PII signals:
  - `publication_retracted`
  - `offer_departing_soon`
  - `offer_departed`
- Y24/Y25 remained strictly read-side only and did not add booking/payment mutation controls.

### Current read-side boundaries (must remain true)
- Supplier sees own offers only.
- Supplier sees lifecycle status, reject-reason visibility, and publication/retraction visibility.
- Supplier does **not** get customer PII, customer list views, payment rows/provider details, or booking/payment control surfaces.
- Supplier analytics/finance dashboard scope remains postponed.

### Still open / postponed
- Booking-derived aggregate alerting remains postponed until authoritative offer→execution linkage is explicitly designed and accepted.
- Examples intentionally postponed for now: first confirmed booking, low remaining capacity, sold out/full alerts.
- No ad hoc booking-derived math should be added in bot handlers without that linkage.

### Next safe step pointer
- Narrow design gate for authoritative supplier offer→execution linkage (read-only design first), then additive supplier read-side extension if accepted.

---

## Checkpoint Sync — Y27 (design accepted, pre-Y27.1 implementation) (2026-04-20)

### Resolved and accepted (not open questions)
- Supplier v1 scope remains intact in narrow operational form: onboarding + legal/compliance pending-approval hardening, supplier offer intake, moderation/publication/retract, supplier workspace, narrow operational visibility, and narrow alerts.
- Y27 design gate is accepted: authoritative supplier booking-derived execution truth is Layer A `Tour + Order`.
- Y27 design recommends explicit additive linkage persistence (`supplier_offer_execution_links`) with one-active-link invariant.

### Current read-side boundaries (must remain true)
- Supplier sees own offers only.
- Supplier sees lifecycle status, reject-reason visibility, publication/retraction visibility, narrow operational visibility, and narrow alerts (`publication_retracted`, `offer_departing_soon`, `offer_departed`).
- Supplier does **not** see customer PII, customer lists, payment rows/provider details, booking/payment controls, or finance dashboards.

### Still open / postponed
- Booking-derived aggregate supplier metrics and richer booking-derived alerts remain postponed until Y27.1 linkage persistence is implemented.
- Legacy offers may remain unlinked; unlinked offers continue lifecycle-only fallback.
- No ad hoc booking-derived math in bot/read handlers before explicit linkage persistence.

### Compatibility baseline (must remain true)
- No Layer A booking/payment redesign.
- No RFQ/bridge redesign.
- No payment-entry/reconciliation redesign.
- No customer PII exposure.
- No broad supplier portal or RBAC redesign.

### Next safe step pointer
- **Y27.1 — supplier offer execution linkage persistence + admin link/unlink** (narrow additive implementation).

---

## Checkpoint Sync — Y28 (design accepted, pre-Y28.1 implementation) (2026-04-20)

### Resolved and accepted (not open questions)
- Telegram admin moderation/publication workspace design is accepted (`docs/TELEGRAM_ADMIN_MODERATION_WORKSPACE_DESIGN.md`).
- Admin role in Telegram workspace v1 remains moderator/publisher only; supplier remains content author.
- Accepted v1 Telegram admin scope: fail-closed allowlisted Telegram admin IDs, narrow commands (`/admin_ops`, `/admin_offers`, optional trivial `/admin_queue`), queue→detail→actions flow, navigation (`prev/next/back/home`), and actions (`approve`, `reject` with reason, `publish`, `retract`).
- `approve != publish` remains strict; supplier rework loop reuses current `rejected + reason` model in v1.

### Current boundaries (must remain true)
- Telegram admin workspace is an operational client layer over existing backend/service truth.
- No admin editing of supplier-authored content.
- No admin editing of supplier legal/commercial truth in Telegram workspace v1.
- No Layer A booking/payment redesign, no RFQ/bridge redesign, no payment-entry/reconciliation redesign.

### Still open / postponed
- Scheduled publish.
- Admin content editing.
- Mass moderation actions.
- RFQ Telegram admin workspace.
- Order/payment admin controls in Telegram.
- Analytics/finance dashboard expansion.
- Broad portal replacement / RBAC redesign.

### Next safe step pointer
- **Y28.1 — Telegram admin moderation workspace implementation** (narrow operational client scope).

---

## Checkpoint Sync — Y29.1 (supplier onboarding navigation polish) (2026-04-21)

### Resolved and accepted (not open questions)
- `/supplier` onboarding now supports safe navigation controls:
  - `Inapoi` => previous step with in-memory FSM draft preserved,
  - `Acasa` => full onboarding FSM cancel/reset (state + draft cleared).
- Navigation behavior is narrow UX-only and aligned with accepted supplier bot navigation patterns.

### Boundaries preserved (must remain true)
- No change to onboarding required fields.
- No change to onboarding approval lifecycle (`pending_review` / `approved` / `rejected`).
- No change to supplier profile lifecycle model.
- No change to supplier offer lifecycle or publication flow.
- No Layer A booking/payment redesign.
- No RFQ/bridge redesign.
- No payment-entry/reconciliation redesign.

### Still open / postponed
- Supplier Telegram moderation workspace (supplier profiles).
- Supplier suspend/revoke implementation.
- Supplier status gating integration against offer actions/visibility.
- Exclusion visibility policy implementation for supplier-level exclusion events.

### Next safe step pointer
- **Y28.2 — Telegram admin approved/published visibility expansion** (narrow read-side scope).

---

## Checkpoint Sync — Y28.2 (Telegram admin approved/published visibility expansion) (2026-04-22)

### Resolved and accepted (not open questions)
- Telegram admin offer surfaces now include:
  - `/admin_queue` => `ready_for_moderation`,
  - `/admin_approved` => approved/unpublished,
  - `/admin_published` => published.
- State-driven action separation is preserved:
  - `ready_for_moderation` => approve/reject,
  - approved/unpublished => publish,
  - published => retract.
- Existing moderation lifecycle semantics remain unchanged (`approve != publish` preserved).

### Boundaries preserved (must remain true)
- No admin content editing introduced.
- No lifecycle redesign introduced.
- No scheduling/mass moderation introduced.
- No Layer A booking/payment redesign.
- No RFQ/bridge redesign.
- No payment-entry/reconciliation redesign.

### Still open / postponed
- Supplier profile moderation Telegram workspace.
- Supplier suspend/revoke implementation.
- Supplier status gating integration.
- Exclusion visibility policy implementation.
- Scheduled publish.
- Mass moderation.

### Next safe step pointer
- **Y29.2 — additive supplier profile status model**.

---

## 1. Reservation expiry status semantics

### Current decision
After reservation expiry:
- `booking_status` remains `reserved`
- `payment_status` becomes `unpaid`
- `cancellation_status` becomes `cancelled_no_payment`
- `reservation_expires_at` becomes `None`

### Why accepted now
- keeps the expiry implementation minimal
- preserves idempotent worker behavior
- prevents double seat restoration
- avoids introducing a new booking terminal status too early

### Risk later
- admin views may interpret expired reservations as still reserved
- customer booking history may become confusing
- analytics and status-based filtering may become ambiguous
- future workflow code may incorrectly rely on `booking_status` alone

### Revisit trigger
- before admin order/status screens are finalized
- before analytics/reporting logic is finalized
- before production release if status-based filtering becomes ambiguous

### Status
open

---

## 1a. Admin read API vs raw reservation/order semantics

### Current decision
- **Phase 6 / Step 1** admin **list** endpoints (`GET /admin/orders`, etc.) expose orders with **`lifecycle_kind`** / **`lifecycle_summary`** (see `app/services/admin_order_lifecycle.py`) so operators are less likely to misread **expired unpaid holds** as active reservations when scanning lists.
- **Phase 6 / Step 16** extends **`GET /admin/orders/{order_id}`** with **read-only** **payment correction visibility** fields (hints, counts, latest payment metadata; see `app/services/admin_order_payment_visibility.py`). **`lifecycle_kind` / `lifecycle_summary`** remain **primary**; hints are **secondary** and conservative from persisted order + payment rows only. Step 16 is **intentionally** non-mutating; **refunds**, forced **paid-state** edits, and manual **reconciliation** commands stay **postponed** until product defines safety rules and an explicit slice.
- **Phase 6 / Step 17** adds **read-only** **action preview** fields on the same endpoint (**`suggested_admin_action`**, **`allowed_admin_actions`**, **`payment_action_preview`**; see `app/services/admin_order_action_preview.py`). These are **advisory** only and do **not** execute or authorize mutations; **payment**-row admin **mutations** (refund/capture/cancel-payment) remain **postponed** until explicit product approval (**Phase 6 / Steps 23–26** are narrow **order** mutations and do **not** write payment rows; **Steps 27–28** are read-side only — lifecycle alignment + move-readiness hints; **Step 29** is a narrow **order** move mutation and does **not** write payment rows).
- **Phase 6 / Step 18** adds **`GET /admin/handoffs`** and **`GET /admin/handoffs/{handoff_id}`** for **read-only** handoff **queue** visibility (**`is_open`**, **`needs_attention`**, **`age_bucket`**, plus persisted fields).
- **Phase 6 / Step 19** adds **`POST /admin/handoffs/{handoff_id}/mark-in-review`** (`open`→`in_review`, idempotent `in_review`, `closed` rejected). **Phase 6 / Step 20** adds **`POST /admin/handoffs/{handoff_id}/close`** (`in_review`→`closed`, idempotent `closed`, `open` rejected; unexpected statuses rejected narrowly). Admin **`close`** intentionally **depends** on moving **`open` → `in_review`** first — not a shortcut from **`open`**. **Phase 6 / Step 21** adds **`POST /admin/handoffs/{handoff_id}/assign`** (narrow **`assigned_operator_id`** on **`open`/`in_review`** only; **reassign** to another operator rejected once set — see `docs/CHAT_HANDOFF.md`). **Phase 6 / Step 22** adds **`POST /admin/handoffs/{handoff_id}/reopen`** (`closed`→`open`, idempotent `open`, `in_review` rejected; **`assigned_operator_id` preserved** on reopen). Handoff **admin** surface remains **intentionally narrow** (no general state machine). **Unassign**, broader **reassignment** policy, and full operator **workflow** remain **postponed**. Internal **ops** JSON remains a **separate** surface from **`/admin/*`**.
- **Phase 6 / Step 23** adds **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`**: **operator cancellation** for **active temporary holds** only (aligned with admin “active hold” lifecycle); **paid** orders and other disallowed state combinations are **rejected**; **no** payment-row mutation, **no** refund/reconciliation change.
- **Phase 6 / Step 24** adds **`POST /admin/orders/{order_id}/mark-duplicate`**: **duplicate** marking for **active temporary hold** or **expired unpaid hold** only; **paid** orders **rejected**; **no** merge, **no** payment-row mutation.
- **Phase 6 / Step 25** adds **`POST /admin/orders/{order_id}/mark-no-show`**: **confirmed + paid + active cancellation** only, **`tour.departure_datetime` in the past** (UTC); terminal **`no_show`/`no_show`**; **no** seat restoration, **no** payment-row mutation.
- **Phase 6 / Step 26** adds **`POST /admin/orders/{order_id}/mark-ready-for-departure`**: **confirmed + paid + active cancellation** only, **`tour.departure_datetime` strictly in the future** (UTC); **`booking_status` → `ready_for_departure` only**; **no** seat mutation, **no** payment-row mutation.
- **Phase 6 / Step 27** (read-only): **`AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID`** in **`app/services/admin_order_lifecycle.py`** so **`ready_for_departure` + paid + active** maps to a **first-class** admin lifecycle label (not generic **`other`**); **`sql_predicate_for_lifecycle_kind`** and **`GET /admin/orders?lifecycle_kind=`** stay consistent; **`admin_order_action_preview`** treats this kind like **confirmed paid** for preview noise.
- **Phase 6 / Step 28** (read-only): **`GET /admin/orders/{order_id}`** adds **`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`** (**`app/services/admin_order_move_readiness.py`**) — conservative decision-support for operators; **does not** perform a move by itself.
- **Phase 6 / Step 29** (narrow mutation): **`POST /admin/orders/{order_id}/move`** (**`app/services/admin_order_move_write.py`**) — move when Step **28**-style readiness passes; **no** payment-row writes, **no** reconciliation semantics change.
- **Phase 6 / Step 30** (read-only): **`GET /admin/orders/{order_id}`** adds **`move_placement_snapshot`** (**`app/services/admin_order_move_inspection.py`**) — **current** tour/boarding placement for inspection only; **`timeline_available`** is **false** because **no** persisted move audit/timeline rows exist yet. **Closure:** **`docs/PHASE_6_REVIEW.md`** — narrow Phase 6 track **closed**; default forward path **transition**, **not** payment admin. **Payment**-row admin **mutations** (refund/capture/cancel-payment) remain **postponed** (see **§1f** below).
- **Database fields are unchanged:** the combination described in **section 1** (`booking_status` may remain `reserved` after expiry, etc.) still exists at persistence layer.

### Why core debt remains open
- Raw status **semantics** in section 1 are still the source of truth for storage and workers; projection only helps **read** surfaces that use it.
- **Admin mutations**, **reporting**, **analytics**, or dashboards that filter on raw enums **without** the same projection rules can still misinterpret state.

### Revisit trigger
- before **admin mutation** flows (status changes, cancellations, manual fixes)
- before **richer admin reporting** or exports that aggregate by raw status
- before **analytics / dashboards** depend directly on raw status combinations without a documented projection layer

### Status
open (read-side **partially mitigated** for Phase 6 Step 1 list API, Steps 16–17 order-detail hints/preview, Step 18 handoff queue reads, Steps **19–22** narrow handoff mutations, Steps **23–26** narrow order mutations, Step **27** **`ready_for_departure_paid`** lifecycle read refinement, Step **28** move-readiness hints, Step **29** narrow move **mutation**, Step **30** **`move_placement_snapshot`** (current placement only); **section 1** remains open for semantics and non-projected consumers; **persisted** move timeline/audit and broader admin order workflow **postponed** — see **`docs/CHAT_HANDOFF.md` Next Safe Step**)

---

## 1b. Admin tour core create vs cover / media attachment

### Current decision
- **Phase 6 / Step 5** adds **`POST /admin/tours`** for **core** `Tour` fields only — **no** binary upload in that step.
- **Phase 6 / Step 6** adds **`PUT /admin/tours/{tour_id}/cover`** to persist **one** optional **`cover_media_reference`** string (URL or storage key) per tour — **not** a file upload endpoint and **not** a media library.
- **Real** upload subsystem, CDN/object-store integration, and **customer-facing** cover delivery via catalog/Mini App remain **intentionally postponed** until explicitly scheduled (see `docs/CHAT_HANDOFF.md` **Not Implemented Yet** / forward steps).

### Revisit trigger
- before admin **tour management** or **end-to-end media handling** is treated as **MVP-complete**
- before production reliance on **binary upload** or **public** cover URLs without a documented storage/delivery strategy

### Status
open (reference string can be set; **upload/delivery** not done)

---

## 1c. Admin boarding points — narrow create/update/delete vs full lifecycle

### Current decision
- **Phase 6 / Steps 8–10** add **`POST`**, **`PATCH`**, and **`DELETE /admin/boarding-points/{boarding_point_id}`** for core boarding fields; delete is blocked when **orders** reference the point (see implementation).
- **Phase 6 / Steps 13–14** add **per-language** **`PUT` / `DELETE`** under **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** (single row per language; allowlist matches **`telegram_supported_language_codes`**).
- **Full route/itinerary** editing, reorder, and **tour-level** archive/hard-delete remain **intentionally postponed** until scheduled (see `docs/CHAT_HANDOFF.md` **Next Safe Step**).

### Revisit trigger
- before admin treats **boarding management** as **complete** without reorder/itinerary workflows
- before **customer-facing** catalog or booking flows need structural changes tied to boarding CRUD beyond current slices

### Status
open (core CRUD + **narrow** per-language translations; **itinerary/reorder** not done)

---

## 1d. Admin translations — per-language upsert/delete vs bulk/publication

### Current decision
- **Tours:** **Phase 6 / Steps 11–12** — **`PUT`** and **`DELETE`** **`/admin/tours/{tour_id}/translations/{language_code}`** (one row per language).
- **Boarding points:** **Phase 6 / Steps 13–14** — **`PUT`** and **`DELETE`** **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** (table **`boarding_point_translations`**, migration **`20260405_05`**).
- **Bulk** translation import/export and **publication** workflow remain **intentionally postponed** (see `docs/CHAT_HANDOFF.md` **Not Implemented Yet**).

### Revisit trigger
- before admin treats **multilingual content ops** as **complete** without bulk tooling or publish pipeline
- before **customer-facing** catalog needs structural changes tied to translation CRUD beyond per-language slices

### Status
open (per-language **upsert/delete** done for tours and boarding points; **bulk** / **publication** **not done**)

---

## 1e. Admin tour archive / unarchive — narrow POST endpoints vs full status editor

### Current decision
- **Phase 6 / Step 15** adds **`POST /admin/tours/{tour_id}/archive`** and **`POST /admin/tours/{tour_id}/unarchive`** only (returns **`AdminTourDetailRead`**). **`sales_closed`** is reused as the **admin “archived”** bucket (no new enum member); **unarchive** sets **`open_for_sale`** only. **Archive** allowed from **draft**, **open_for_sale**, **collecting_group**, **guaranteed**; **not** from in-progress / completed / cancelled / postponed (see service). Idempotent **archive** when already **`sales_closed`**; idempotent **unarchive** when already **`open_for_sale`**.
- **Hard delete**, arbitrary **TourStatus** workflow UI, and **public** catalog semantics beyond existing **`OPEN_FOR_SALE`** scopes remain **out of scope** for this slice.

### Revisit trigger
- before admin needs **audit** fields, **batch** archive, or **status** rules that collide with operational **`sales_closed`** meaning
- before **public catalog** or **customer-facing** semantics assume **`sales_closed`** means only “admin archived” (vs operational “sales ended”)

### Status
open (narrow **two-endpoint** slice; **not** a full lifecycle editor)

---

## 1f. Admin payment-side operations vs reconciliation (future)

### Current decision
- **Admin payment mutations** (refund, capture, cancel-payment, forced paid-state edits, manual reconciliation commands) are **intentionally postponed** — no **`/admin/*`** payment-write slice is implied by Phase 6 Steps **1–30**.
- **Payment reconciliation** (service-layer, webhooks) remains the **single source of truth** for **confirmed paid-state transitions** on orders until product defines a different contract — **this boundary stays intact**; admin tooling must **not** silently bypass it.
- **Phase 6 review** is recorded in **`docs/PHASE_6_REVIEW.md`** (checkpoint **Step 30**). **Revisit** admin payment-side operations **only** via a **separate design checkpoint** (product + safety rules + reconciliation contract) — **not** as the default follow-up to Phase 6 closure.
- **Revisit** before: **real PSP-integrated** admin payment tooling, **refund workflow**, **production payment rollout**, **broader** admin-side payment operations.

### Status
open (by design; **not** default next implementation — see **`docs/PHASE_6_REVIEW.md`** and handoff **Next Safe Step**)

---

## 2. Temporary bot FSM storage uses MemoryStorage

### Current decision
The current bot foundation uses `MemoryStorage()` for FSM state.

### Why accepted now
- simplest safe option for early private bot foundation
- good enough for local development and early flow validation
- avoids introducing Redis complexity too early

### Risk later
- state is lost on bot restart
- unsuitable for more serious production traffic
- can break longer or more fragile user flows
- makes horizontal scaling impossible

### Revisit trigger
- before production-like deployment of Telegram bot
- before longer multi-step user flows are added
- before group and handoff flows become more complex

### Status
open

---

## 3. Payment provider is currently mock/provider-agnostic

### Current decision
Payment entry currently creates a minimal payment session/reference using a mock/provider-agnostic flow.

### Why accepted now
- allows payment flow structure to be built safely
- decouples order/payment architecture from a real provider too early
- enables reconciliation design and tests before real gateway integration

### Risk later
- real provider fields may not match current assumptions
- webhook payloads, status mapping, and error handling may need expansion
- payment entry UX may need revision after real provider adoption

### Revisit trigger
- before real provider SDK/API integration
- before production payment rollout
- before Mini App payment implementation

### Status
open

---

## 4. Payment status enum may become too narrow for real provider lifecycle

### Current decision
The existing `payment_status` enum is reused for both order-level payment status and payment records.

Current values include:
- `unpaid`
- `awaiting_payment`
- `paid`
- `refunded`
- `partial_refund`

### Why accepted now
- keeps the MVP schema simpler
- avoids over-modeling provider lifecycle too early
- sufficient for entry + reconciliation foundation

### Risk later
A real provider may require more detailed payment-record states, such as:
- failed
- pending_webhook
- cancelled
- provider_error
- expired

This may create ambiguity between:
- order payment state
- individual payment record state

### Revisit trigger
- before real payment provider integration
- before refund/failure handling is added
- before admin payment operations are expanded

### Status
open

---

## 5. Local test and app flow rely on PostgreSQL-first discipline, but SQLite is still possible in ad hoc contexts

### Current decision
The project is documented and implemented as PostgreSQL-first.

### Why accepted now
- correct choice for booking/payment-sensitive logic
- migrations and concurrency behavior are being verified against PostgreSQL
- aligns with Railway production target

### Risk later
If someone casually runs parts of the project against SQLite:
- lock behavior may differ
- enum behavior may differ
- transaction semantics may differ
- booking/payment assumptions may be misvalidated

### Revisit trigger
- before onboarding another developer
- before writing more concurrency-sensitive booking logic
- before CI environment is finalized

### Status
open

---

## 6. Bot and backend process separation must be preserved

### Current decision
The project keeps bot process and backend process conceptually separate.

### Why accepted now
- cleaner architecture
- prevents Telegram concerns from leaking into backend runtime
- aligns with worker/process model planned in implementation plan

### Risk later
- quick shortcuts may accidentally couple bot startup with API startup
- deployment shortcuts may collapse concerns into one process
- debugging and scaling will become harder

### Revisit trigger
- before production/staging process deployment is finalized
- before workers and reminders are introduced more broadly
- before Railway process layout is finalized

### Status
open

---

## 7. Deep-link tour browsing currently uses safe `tour_<CODE>` convention only

### Current decision
Private bot deep-link entry currently supports the safe pattern:
- `/start tour_<CODE>`

### Why accepted now
- simple and controlled
- easy to validate
- enough for current browsing/detail entry flow

### Risk later
- marketing/source attribution may need richer deep-link payloads
- campaign/channel tracking may need structured parameters
- language or source tags may need preservation

### Revisit trigger
- before marketing campaign deep links are introduced
- before source-channel analytics becomes important
- before Mini App/deep-link routing is expanded

### Status
open

---

## 8. Language handling currently uses simple normalized short codes

### Current decision
Language resolution currently:
- normalizes code
- lowers case
- converts `_` to `-`
- uses the short code before `-`
- accepts only supported languages

### Why accepted now
- simple
- safe
- sufficient for current private flow and early multilingual behavior

### Risk later
- region-specific variants may matter
- content fallback rules may need to become more explicit
- more complex multilingual personalization may outgrow the current simplification

### Revisit trigger
- before multilingual content becomes more complex
- before supporting more localized tour content variants
- before analytics/reporting by language becomes important

### Status
open

---

## 9. Current reservation expiration policy is embedded in service logic

### Current decision
Current implemented expiration assumption:
- departure in 1–3 days -> 6 hours
- departure in 4+ days -> 24 hours
- capped by `sales_deadline` if earlier

### Why accepted now
- enough for the first real reservation workflow
- allows payment-entry and expiry logic to move forward
- aligns with the current MVP-level booking flow

### Risk later
- business may want route-specific or campaign-specific reservation windows
- admin override may be needed
- analytics and payment conversion tuning may require revisiting this policy

### Revisit trigger
- before admin-side booking policy controls are added
- before production tuning of booking/payment conversion
- before route-specific business rules are introduced

### Status
open

---

## 10. Route/API delivery for payment is minimal and mock/provider-agnostic

### Current decision
Webhook/API delivery is intentionally minimal:
- thin route
- isolated verification/parsing helper
- provider-agnostic input mapping into reconciliation service

### Why accepted now
- keeps reconciliation logic clean
- avoids locking into provider SDK too early
- makes testing easier

### Risk later
- real provider SDK/webhook format may require more specific handling
- signature verification may become provider-specific
- retries, duplicates, and provider error semantics may need more nuance

### Revisit trigger
- before real provider integration
- before production payment rollout
- before multiple providers are supported

### Status
open

---

## 11. Seat restoration and seat decrement logic should remain tightly controlled

### Current decision
Seats are:
- decremented at temporary reservation creation
- restored by the expiry worker for eligible unpaid reservations

### Why accepted now
- creates a coherent temporary reservation lifecycle
- matches current write workflow
- supports payment-entry and expiry slices

### Risk later
- future waitlist logic will need to coordinate with restored seats
- handoff/admin manual operations could accidentally conflict
- duplicate restoration risks can reappear if state semantics become inconsistent

### Revisit trigger
- before waitlist release logic
- before admin manual reservation/order interventions
- before analytics around occupancy/load are finalized

### Status
open

---

## 12. Current test harness is now clean, but DB-backed test lifecycle remains important infrastructure

### Current decision
DB-backed unit test harness now centralizes engine disposal after class teardown.

### Why accepted now
- removed the `psycopg ResourceWarning`
- keeps test output clean
- avoids touching production code

### Risk later
- future tests may reintroduce resource leaks
- async or more complex DB usage may need a stronger shared test infrastructure
- test fixture complexity may grow with API/bot/worker layers

### Revisit trigger
- before adding broader API integration tests
- before worker integration tests
- before CI test matrix becomes larger

### Status
open

---

## 13. Repositories intentionally avoid workflow logic

### Current decision
Repositories are persistence-oriented only.

### Why accepted now
- keeps architecture clean
- prevents business logic from leaking into data access layer
- makes services the proper orchestration boundary

### Risk later
- rushed feature work may tempt adding workflow shortcuts into repositories
- duplicated business rules may appear if service boundaries weaken

### Revisit trigger
- on every major workflow addition
- especially booking, payment, waitlist, and handoff slices

### Status
open

---

## 14. Payment reconciliation service is the single source of truth for paid-state transitions

### Current decision
Payment reconciliation service is the only place that should confirm payment and update payment/order state.

### Why accepted now
- preserves idempotency
- avoids state mutation duplication
- creates a clean boundary between route delivery and business logic

### Risk later
- admin tools, provider integration, or bot shortcuts may attempt to bypass reconciliation service
- inconsistent order/payment state may appear if multiple paths can mark payment as paid

### Revisit trigger
- before admin-side payment operations
- before provider-specific payment integrations
- before refund workflow is introduced

### Status
open

---

## 15. Notification/reminder/worker layer is not yet implemented

### Current decision
Workers currently cover reservation expiry only.
Reminder/notification infrastructure is still postponed.

### Why accepted now
- keeps current scope focused
- avoids mixing booking/payment core with notification complexity too early

### Risk later
- delayed implementation may require refactoring order lifecycle triggers
- notification semantics may depend on status assumptions already made

### Revisit trigger
- next Phase 4 worker/reminder slice
- before production rollout of booking/payment flow

### Status
open

---

## 16. Phase 5 Mini App MVP closure — residual debt (non-blocking)

**Added:** Phase 5 / Step 20 consolidation. Phase 5 is **accepted** per `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`. The items below are **not** reopened as blockers; they stay on the backlog for later phases.

| Topic | Where tracked |
|-------|----------------|
| Production Telegram Web App init-data / Mini App API auth | **Resolved in Y30.4x:** local pinned SDK `assets/telegram-web-app.js` + bridge identity injection (`tg_bridge_user_id`) validated on runtime path; keep as regression-watch item only (see `docs/CHAT_HANDOFF.md`) |
| Real payment provider (mock/staging paths today) | Section 3 |
| Bot `MemoryStorage` | Section 2 |
| Expiry/booking status semantics for admin/analytics | Section 1 |
| Waitlist auto-promotion and customer notifications | Product / later phase |
| Handoff operator inbox and customer notifications | Phase 6–7 scope |
| Full shell i18n for all languages | Phase 5 used en/ro priority + English fallback |

Do **not** duplicate long analysis here — keep single source of truth in numbered sections above and in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`.

### Status
open (informational snapshot)

---

## 17. Production schema vs deployed code (Railway / Alembic operational risk)

### Current decision / current lesson
- **Production schema may lag behind deployed code** when Alembic migrations are **not** applied before or alongside a release that already uses new ORM columns. Example (resolved): Phase 6 / Step 6 added `tours.cover_media_reference` in code while production Postgres had not yet run the migration → `sqlalchemy.exc.ProgrammingError` / `psycopg.errors.UndefinedColumn`, breaking any path that loads `Tour` (e.g. **`/mini-app/catalog`**, **`/mini-app/bookings`**) until the schema matched.
- **Phase 7.1 — same class of failure:** code that maps **`Tour.sales_mode`** shipped while Postgres **lacked** **`tours.sales_mode`** (migration **`20260416_06`** not applied) → **`psycopg.errors.UndefinedColumn: column tours.sales_mode does not exist`** on any route or worker that loads **`Tour`**. **Recovery:** apply **`python -m alembic upgrade head`** (reachable DB URL) **before** treating the stack as healthy; **do not** mask with app-only “fixes.” **Release gate:** Phase **7.1** deploys **must** include migration apply — see **`COMMIT_PUSH_DEPLOY.md`** (**Deploy-critical**).
- **V2 Track 2 — analogous class of failure:** application code expects **`suppliers`**, **`supplier_api_credentials`**, **`supplier_offers`**, and related enums (Alembic **`20260417_07`**) while Postgres has not applied that revision → failures on **`/admin/suppliers*`**, **`/supplier-admin/*`**, or ORM loads of **`Supplier*`** models (**not** on core **`Tour`** / Mini App catalog **unless** something incorrectly joins supplier tables). **Gate:** same **`alembic current` == `heads`** rule before deploy; see **`COMMIT_PUSH_DEPLOY.md`** (Track **2** note).
- **V2 Track 3 — analogous class of failure:** code expects extended **`supplier_offer_lifecycle`** values and new **`supplier_offers`** columns (**`20260418_08`**) while DB is still at **`20260417_07`** → ORM/API errors on moderation/publish paths and possibly on **`SupplierOffer`** loads. **Gate:** apply **`20260418_08`** before or with deploy that ships Track **3**; see **`COMMIT_PUSH_DEPLOY.md`** (Track **3** note).
- **`railway shell`** (or shell on the platform) does not by itself fix **local** migration runs: internal DB hostnames such as **`*.railway.internal`** are **not resolvable** from a developer machine, so “run Alembic from my laptop against prod” typically requires the **public** Railway Postgres URL (or another supported access path).

### Why accepted now
- Release automation may not yet run **`alembic upgrade head`** on every deploy.
- Teams often validate app code first and treat DB migration as a follow-up — acceptable only until a repeatable release gate exists.

### Risk later
- Repeat **500**s on catalog, bookings, or admin routes after any deploy that ships ORM/model changes without matching DDL.
- Incidents look like “Mini App bugs” but are **pure schema drift**.

### Revisit trigger
- **Before** the next schema-changing deploy (new column/table/enum).
- Before a **release checklist** is considered complete without an explicit **migration + smoke** step.
- Before **production rollout automation** is treated as stable without DB migration in the path.

### Recovery path (documented pattern; not a substitute for automation)
- Confirm drift: e.g. `alembic current` vs `heads` against the target DB.
- Apply migrations using a **reachable** DB URL (often Railway **public** Postgres URL) and a driver-explicit SQLAlchemy URL such as **`postgresql+psycopg://...`** for local Alembic.
- **Redeploy** the backend service after migration; smoke **`/health`**, **`/mini-app/catalog`**, **`/mini-app/bookings`** (and any other routes touching changed models).

### Status
open

---

## 18. Admin `PATCH` `seats_total` vs order-level occupancy

### Current decision
- **Phase 6 / Step 7** — **PATCH /admin/tours/{tour_id}** — may update **`seats_total`** using a **conservative** rule: treat **committed seats** as `seats_total - seats_available`, require any new total **≥** that value, and set **`seats_available`** to `new_total - committed_seats`. This keeps ORM/check constraints coherent **without** summing live **`orders.seats_count`**.
- **Richer validation** (reconcile **`seats_total`** with actual reservations/orders, or block edits when orders exist) remains **postponed** until explicitly scheduled.

### Why accepted now
- Avoids unsafe automatic seat math and keeps the admin slice narrow.
- Order-accurate occupancy rules belong with booking domain work, not a minimal PATCH slice.

### Risk later
- Admin could theoretically set totals that are **inconsistent** with sum of order rows if historical data drifted — unlikely if **`seats_available`** was maintained by existing booking flows.

### Revisit trigger
- before admin tools are used to **reshape** capacity on tours with **many** active bookings
- before **analytics** or **ops** rely on **`seats_*`** alone without order-level checks

### Status
open (narrow rule shipped; **order-sum validation** not implemented)

---

## 19. Phase 7 group runtime vs rules documentation (Step 1 vs Step 2+)

### Current decision
- **Phase 7 / Step 1** delivered **`docs/GROUP_ASSISTANT_RULES.md`** — operational rules only (no code).
- **Phase 7 / Step 2** added **helper-layer** (**group trigger** + **handoff trigger** evaluation): `app/services/group_trigger_evaluation.py`, `handoff_trigger_evaluation.py`, `assistant_trigger_evaluation.py`; tests `tests/unit/test_group_assistant_triggers.py`.
- **Phase 7 / Step 3** added **minimal** **Telegram** **group** runtime: `app/bot/handlers/group_gating.py` + `app/services/group_chat_gating.py` — **group/supergroup text**; **non-trigger** silence; trigger → **one** short ack; **`TELEGRAM_BOT_USERNAME`** unset → silence.
- **Phase 7 / Step 4** wires **`evaluate_handoff_triggers`** in the **same** narrow path **after** **`evaluate_group_trigger`** succeeds — **reply shaping only** (handoff **categories** drive short safe lines in **`app/services/group_chat_gating.py`**); **no** handoff DB rows, **no** operator assignment, **no** workflow engine. Tests: **`tests/unit/test_group_chat_gating.py`** (category cases + non-trigger silence).
- **Phase 7 / Step 5** adds **`app/services/group_private_cta.py`** + **`app/schemas/group_private_cta.py`**: **`https://t.me/<bot>?start=grp_private`** (generic) or **`…grp_followup`** (after handoff-category line); appended to group replies. Tests: **`tests/unit/test_group_private_cta.py`**.
- **Phase 7 / Step 6** adds **narrow private `/start`** handling in **`app/bot/handlers/private_entry.py`**: **`match_group_cta_start_payload`**; **`start_grp_private_intro`** / **`start_grp_followup_intro`** in **`app/bot/messages.py`** (two **distinct** short entry messages; Phase **7** / Steps **16–17** add **`start_grp_followup_resolved_intro`**, **`start_grp_followup_readiness_*`**, via **`group_followup_private_intro_key`** when applicable); then catalog — **no** handoff persistence from **`grp_*`** in Step **6**. Tests: **`test_group_private_cta`** (matcher), **`test_private_start_grp_messages`**.
- **Phase 7 / Step 7** adds **narrow** **`handoffs`** persistence on **`/start grp_followup`** only (**reason** **`group_followup_start`**, dedupe **open** by user+reason; **`grp_private`** — **no** write). **`HandoffEntryService`**, **`HandoffRepository.find_open_by_user_reason`**. Tests: **`test_handoff_entry`**, **`test_group_private_cta`** (payload gate).
- **Phase 7 / Step 8** adds **focused runtime/bot-flow tests** for the private **`grp_followup`** chain — **`tests/unit/test_private_entry_grp_followup_chain.py`** (`handle_start` + **`SessionLocal`** test binding + mocked catalog) — **no** production behavior changes.
- **Phase 7 / Step 9** adds **explicit admin read-side visibility** for **`group_followup_start`**: derived **`is_group_followup`**, **`source_label`** on **`GET /admin/handoffs`**, handoff detail, and order-detail handoff summaries — **read-only**; tests **`test_admin_handoff_group_followup_visibility`**, **`test_api_admin`** (focused cases).
- **Phase 7 / Step 10** adds **`POST /admin/handoffs/{handoff_id}/assign-operator`** — **narrow operator assignment** for **`reason=group_followup_start`** **only** (same rules as Step **21** **`assign`**: open/in_review, operator exists, idempotent same id, **no** reassign); general **`POST .../assign`** **unchanged**; **no** notifications; tests **`test_api_admin`** (focused cases).
- **Phase 7 / Step 11** adds **read-side work-state visibility** for **`group_followup_start`**: derived **`is_assigned_group_followup`**, **`group_followup_work_label`** on **`GET /admin/handoffs`**, handoff detail, and order-detail handoff summaries — **read-only**; tests **`test_admin_handoff_group_followup_visibility`**, **`test_api_admin`** (focused cases).
- **Phase 7 / Step 12** adds **`POST /admin/handoffs/{handoff_id}/mark-in-work`** — **narrow take-in-work** for **assigned** **`group_followup_start`** only (**`open` → `in_review`**, **`in_review`** idempotent; **no** migration); tests **`test_api_admin`** (`mark_in_work` cases).
- **Combined Phase 7 / Steps 13–14** add **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`** — **narrow resolve/close** for **`group_followup_start`** only (**`in_review` → `closed`**, **`closed`** idempotent, **`open`** rejected; **no** replacement for Step **20** general **`close`**) and **read-only** **`group_followup_resolution_label`** on admin handoff reads when that reason is **`closed`**; tests **`test_api_admin`**, **`test_admin_handoff_group_followup_visibility`**.
- **Phase 7 / Step 15** adds **read-only** **`group_followup_queue_state`** on admin handoff **list** / **detail** / order-detail summaries and optional **`GET /admin/handoffs?group_followup_queue=`** filter (**`awaiting_assignment`**, **`assigned_open`**, **`in_work`**, **`resolved`**) — **no** write-path changes; tests **`test_api_admin`**, **`test_admin_handoff_group_followup_visibility`**.
- **Phase 7 / Step 16** adds **narrow private resolved-followup confirmation** on **`/start grp_followup`**: **`HandoffRepository.find_latest_by_user_reason`**, **`HandoffEntryService.should_show_group_followup_resolved_confirmation`**, **`start_grp_followup_resolved_intro`** when **no** **open** **`group_followup_start`** and **latest** row is **`closed`**; Step **7** persist semantics **unchanged**; **no** operator chat, **no** handoff push notifications; tests **`test_handoff_entry`**, **`test_private_entry_grp_followup_chain`**.
- **Phase 7 / Step 17** adds **narrow private followup history/readiness** on repeat **`/start grp_followup`**: **`HandoffEntryService.group_followup_private_intro_key`** → **`start_grp_followup_readiness_pending`** / **`_assigned`** / **`_in_progress`**, **`start_grp_followup_resolved_intro`**, or **`start_grp_followup_intro`**; **read-only**; **no** operator IDs in copy; tests **`test_handoff_entry`**, **`test_private_entry_grp_followup_chain`**.
- **Phase 7 final followup/operator consolidation block** — **safe polish only**: unified short private **`grp_followup`** wording, **`/contact`** / **`/human`** + browse-tours CTAs where applicable, admin **`group_followup_work_label`** / **`group_followup_resolution_label`** aligned to the same **queue/work** state model as private copy; tests include **`test_group_followup_phase7_consolidation`** and updates to existing **`grp_followup`** / admin visibility tests; **no** new persistence, **no** mutation/enum/API shape changes, **no** public booking/payment/waitlist/Mini App changes.
- **Continuity note:** **group** chat path (Steps **3–4**) remains **reply-only** (no DB handoff from group messages); **private** **`grp_followup`** chain persists intent (Step **7**), is **test-covered** (Step **8**), is **operator-visible in admin reads** (Steps **9–11** + Step **15** queue bucket), can be **narrow-assigned** via **`assign-operator`** (Step **10**), **taken in-work** via **`mark-in-work`** (Step **12**) after assignment, **resolved** via **`resolve-group-followup`** (Steps **13–14**), with **read-side triage labels** (Step **11**), **resolved** label (Steps **13–14**), **queue-state** (Step **15**), **private** **resolved** acknowledgment (Step **16**), **private** **readiness** copy for repeat entries (Step **17**), and **consolidation-aligned** wording (private + admin reads). **Phase 7** **implementation + consolidation + review** — **`docs/PHASE_7_REVIEW.md`** — is **closed** for this chain; **two-way operator chat** / **handoff push notifications** remain **postponed**.
- **Forward (documented):** **`docs/CHAT_HANDOFF.md`** — **Phase 7.1** **Steps 1–5** shipped; **Step 6** (direct whole-bus self-service **design gate**) remains the **product** next step where applicable; **separate** from Phase **7** **`group_followup_*`**. **V2 supplier marketplace:** **Track 0**–**3** complete (**Track 3** = moderated publication + showcase — **implementation** + stabilization review); **Track 4** (request marketplace) is the next **implementation** track when scheduled — see **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`**. Optional **later** slices: **i18n** polish, group **rate limits**.
- **Still postponed:** **broad** operator **assignment/claim** redesign, **full** **operator workflow engine**, **full** group assistant; **live** Telegram validation **may** still depend on **Railway** / bot deploy health — **product scope** unchanged. Optional later: **i18n** acks, **rate limits**, **structured logging** — product-scoped.

### Status
closed for Phase **7** narrative (**`docs/PHASE_7_REVIEW.md`**) — Steps **4–17** + **final consolidation** **shipped** (group + private **`grp_*`** + **`grp_followup`** persistence + tests + admin visibility + narrow assign / in-work / resolve + queue/read labels + aligned wording). **Postponed:** **operator chat**, **handoff push notifications**, **full** operator workflow — unchanged. **Related active work:** **Phase 7.1** (**`docs/CHAT_HANDOFF.md`**); **V2** supplier marketplace — **Track 0**–**3** shipped (**Layer B** + moderated publication); **Track 4** next — **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** (**not** mixed into Phase **7** handoff logic **ad hoc**).

---

## 20. Tour sales mode (`per_seat` / `full_bus`)

### Current decision
- **Tour sales mode** is an active **Phase 7.1** sub-track (**separate** from closed Phase **7** **`group_followup_*`** work).
- The design source is **`docs/TOUR_SALES_MODE_DESIGN.md`**.
- Implementation follows the design rollout order: **(1)** admin/source-of-truth → **(2)** backend policy → **(3)** read-side adaptation → **(4)** operator-assisted full-bus → **(5)** optional direct whole-bus self-service — **not** as ad hoc changes inside booking, Mini App, private bot, or Phase **7** handoff flows without an explicit slice.
- **`tour.sales_mode`** (Postgres + ORM) is the **commercial source of truth**; **`TourSalesModePolicyService`** in **`app/services/tour_sales_mode_policy.py`** is the **single service-layer interpretation** for **`per_seat` / `full_bus`** (read-only **`TourSalesModePolicyRead`**). Enum interpretation remains authoritative, and catalog full-bus actionability is now explicitly bounded by inventory snapshot: **`bookable`** only at virgin capacity (`seats_total > 0` and `seats_available == seats_total`), **`assisted_only`** for partial inventory, **`view_only`** for sold out, **`blocked`** for invalid snapshots. **Steps 3–4** wire read-side policy into Mini App and private bot; **Step 5** adds operator-assisted full-bus handoff context — see **`docs/CHAT_HANDOFF.md`** **Completed Steps**.
- **`per_seat` / `full_bus`** remains a **tour-level** product/domain concern, not a UI-only tweak.
- **Operations / schema:** Deploying Phase **7.1** tour code without applying **`alembic/versions/20260416_06_add_tour_sales_mode.py`** causes **`column tours.sales_mode does not exist`** — **not** a product logic bug. **Gate:** **`python -m alembic upgrade head`** on the target DB before or with the release (**`COMMIT_PUSH_DEPLOY.md`**, **§17** here).

### Status
open (**Phase 7.1 / Steps 1–5** shipped — admin field, policy service, Mini App + private bot read-side, operator-assisted full-bus path; **Step 6** optional direct whole-bus self-service — **design gate only** until approved — see **`docs/CHAT_HANDOFF.md` Next Safe Step**)

---

## 21. V2 Track 0 — Core Booking Platform freeze (supplier marketplace prep)

### Current decision
- **Track 0** documents the **frozen Layer A** (Core Booking Platform) so **V2** supplier-marketplace tracks do not break existing booking, payment, Mini App, private bot, Phase **7** handoff baseline, or Phase **7.1** **`sales_mode`** behavior by accident.
- **Source of truth:** **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`** (frozen core, compatibility contracts, must-not-break checklist, baseline smoke, migration/deploy guardrails).
- **Schema drift guardrail:** deploy must not outpace DB migrations (**`tours.cover_media_reference`**, **`tours.sales_mode`** / **`20260416_06`**, **V2 Track 2** **`20260417_07`**, **V2 Track 3** **`20260418_08`**, and any future DDL) — see **`COMMIT_PUSH_DEPLOY.md`** and **§17**.

### Status
closed (documentation/guardrails for Track **0**; **no** supplier marketplace implementation in Track **0**)

---

## 22. V2 Track 1 — Supplier marketplace design acceptance / alignment

### Current decision
- **Track 1** is a **documentation-only** gate: confirm the supplier-admin + request-marketplace **design package** aligns with **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`** before **Track 2** code.
- **Aligned:** Layers **B/C** are **extensions** on **Layer A**; **no** silent redefinition of booking/payment/reservation semantics; **no** default broadening of **Phase 7** **`grp_followup_*`**; **moderated** supplier publication; **RFQ** domain **separate** from normal order lifecycle until explicit bridge; **direct whole-bus self-service** **not** auto-approved (Phase **7.1** Step **6** / V2 **Track 6**).
- **Record:** **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** (Track **1** section) + **`docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`** §13a.

### Status
closed (documentation acceptance / alignment; **no** application code in Track **1**)

---

## 23. V2 Track 2 — Supplier admin foundation (Layer B) — implementation closure

### Current decision
- **Track 2** adds **only** new persistence and APIs: **`suppliers`**, **`supplier_api_credentials`** (SHA-256 hashed API tokens), **`supplier_offers`** with service composition, payment mode, lifecycle (**`draft`** / **`ready_for_moderation`**), commercial/timing/capacity fields; **`supplier_offers.sales_mode`** uses the **existing** PostgreSQL enum **`tour_sales_mode`** (same values as core **`tours.sales_mode`** — **reuse at DDL level**, not a change to **`tours`**).
- **Central admin** (`ADMIN_API_TOKEN`): additive **`POST /admin/suppliers`** (bootstrap + one-time plaintext token), **`GET /admin/suppliers`**, **`GET /admin/suppliers/{id}`**, **`GET /admin/suppliers/{id}/offers`**, **`GET /admin/supplier-offers/{offer_id}`** — **does not** replace or redefine existing admin tour/order/handoff semantics.
- **Supplier admin:** **`/supplier-admin/offers`** (list/detail/create/update) authenticated by **supplier bearer token** (DB lookup); scoped so a supplier cannot read or mutate another supplier’s offers (**404** on cross-tenant access).
- **Explicitly not in Track 2:** customer catalog/checkout changes, request marketplace, publication/moderation workflow beyond supplier-side **`ready_for_moderation`** flag, direct whole-bus self-service, order lifecycle replacement, payment execution changes, Phase **7** **`grp_followup_*`** expansion.

### Residual debt / forward hooks
- **Credential rotation**, multiple active credentials per supplier policy, and full RBAC are **postponed** (bootstrap path is intentional minimum).
- **Tests:** **`tests/unit/base.py`** gained **`create_supplier`**, **`create_supplier_credential`**, **`create_supplier_offer`** helpers for supplier-focused tests; existing **`create_tour` / `create_order`** behavior **unchanged** — see stabilization review (**`docs/CURSOR_PROMPT_TRACK_2_STABILIZATION_AND_REVIEW_V2.md`**).

### Status
closed for **Track 2** scope (foundation + stabilization review); **Track 3** delivered moderation/publication on top (see **§24**)

---

## 24. V2 Track 3 — Supplier offer publication / moderation — implementation + stabilization

### Current decision
- **Track 3** is **additive** on **Track 2**: extends **`supplier_offer_lifecycle`** (**`approved`**, **`rejected`**, **`published`**), adds **`moderation_rejection_reason`**, **`published_at`**, **`showcase_chat_id`**, **`showcase_message_id`** (**`20260418_08`**). **No** **`tours` / `orders` / `payments`** DDL changes.
- **Moderation enforcement:** **`POST /admin/supplier-offers/{id}/publish`** is **only** under **`ADMIN_API_TOKEN`**; **`SupplierOfferModerationService.publish`** accepts **`approved`** only; **rejected** / **draft** / **ready_for_moderation** cannot publish. **Suppliers** cannot call publish (no route on **`/supplier-admin/*`**) and **`SupplierOfferService`** rejects setting **`approved`**, **`rejected`**, or **`published`** on update; **`approved`**/**`published`** rows are **immutable** via supplier API.
- **Telegram:** channel post via Bot API **`sendMessage`** (HTML) to **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`**; **no** supplier direct-to-channel path in code.
- **CTA:** channel HTML includes bot deep link **`supoffer_<id>`**; private **`/start`** resolves **`published`** offers (**no** new booking semantics). **B11 (first slice):** when an **active** **`supplier_offer_execution_links`** row targets a **`Tour`** that is **`open_for_sale`** and **`tour_is_customer_catalog_visible`**, the bot sends a **primary WebApp** button to **`{MINI_APP_BASE}/tours/{tour.code}`** (`resolve_sup_offer_start_mini_app_routing`), **without** the subsequent **generic catalog overview** message (`_send_catalog_overview`) — router focus on exact Tour. **Fallback** (no link / not eligible / no Mini App base URL): intro + offer-landing or catalog keyboard + **generic catalog overview** **as before**.
- **Stabilization review:** no RFQ, bidding, whole-bus self-service, Mini App route churn, or group-gating redesign observed in Track **3** touchpoints; see **`docs/CURSOR_PROMPT_TRACK_3_STABILIZATION_AND_REVIEW_V2.md`**.

### Residual debt / forward hooks
- **Unpublish**, edit/delete channel messages, and linking showcase offers to core **`Tour`** SKUs remain **postponed**.

### Status
closed for **Track 3** scope (publication layer + stabilization review); **Track 4** closure recorded in **§25**; **Track 5a** in **§26**

---

## 25. V2 Track 4 — Custom request marketplace foundation (Layer C) — implementation + stabilization

### Current decision
- **Track 4** is **additive** Layer **C**: **`custom_marketplace_requests`** (customer context, type, dates, route notes, group size, specials, **`source_channel`**, **`status`**, **`admin_intervention_note`**) + **`supplier_custom_request_responses`** (**`declined`/`proposed`**, optional quote) — Alembic **`20260421_10`**. **No** DDL on **`tours`**, **`orders`**, **`payments`**, or **`supplier_offers`** lifecycle beyond pre-Track-4 state.
- **Separation from orders:** intake and services **do not** create **`Order`** rows, holds, or payment sessions; **no** bridge to booking in this track (explicit future track, e.g. **Track 5**).
- **Supplier visibility:** **open** requests listed to all authenticated suppliers (broadcast MVP); **no** ranking, auction, or automated matching.
- **Admin:** list/detail all statuses; **`PATCH`** for note and/or **`status`** (e.g. **`cancelled`**); responses visible on detail.
- **Layer A touchpoints (intentionally narrow):** additive Mini App **`POST /mini-app/custom-requests`**, optional **`/custom-request`** view from Help, private **`/custom_request`** command + FSM; **`help_command_reply`** text extended — core catalog/reservation/payment routes **unchanged**.
- **User model:** **`User.custom_marketplace_requests`** relationship only (ORM navigation + FK from requests to **`users.id`**); **no** change to order/handoff/waitlist relationships.
- **Bot routing:** **`custom_request`** router is registered before **`private_entry`** so FSM handlers win when state is set; **`private_entry`** still owns default private chat behavior when not in custom-request states — see **`docs/CURSOR_PROMPT_TRACK_4_STABILIZATION_AND_REVIEW_V2.md`**.

### Residual debt / forward hooks
- Request → booking/payment **transition contract**, winner selection, commercial ownership (**Track 5**), smarter supplier routing, notifications, customer-facing response UX.

### Status
closed for **Track 4** scope (foundation + stabilization review); **Track 5a** records commercial selection without orders — see **§26**; broader **Track 5** (RFQ→Layer A bridge) remains **when explicitly scoped**

---

## 26. V2 Track 5a — Commercial resolution selection foundation (Layer C) — stabilization

### Current decision
- **Additive only:** Alembic **`20260422_11`** extends **`custom_marketplace_request_status`** (new values), adds **`commercial_resolution_kind`** enum + nullable columns on **`custom_marketplace_requests`**; **no** DDL on **`orders`**, **`payments`**, **`tours`**, **`supplier_offers`**, or handoff tables.
- **No request→order bridge:** codebase review: **`app/services/custom_marketplace_request_service.py`** and related RFQ routes do **not** import or call reservation/payment/order write services; customer Mini App reads return **status + short summary** only.
- **Selection rules:** **`supplier_selected`** requires **`selected_supplier_response_id`** pointing at a **`proposed`** **`SupplierCustomRequestResponse`** with **`request_id`** equal to the parent request; cross-request IDs rejected with **400**.
- **Admin contract:** terminal commercial statuses (**`supplier_selected`**, **`closed_assisted`**, **`closed_external`**, legacy **`fulfilled`**) are **422** on **`PATCH /admin/custom-requests/{id}`**; use **`POST .../resolution`**. **`open`** / **`cancelled`** / notes remain on **`PATCH`** ( **`open`** and **`cancelled`** clear selection + resolution kind).
- **Supplier mutations:** **`PUT .../response`** allowed only for **`open`** and **`under_review`** — not after **`supplier_selected`** / **`closed_*`** / **`cancelled`**.
- **Customer surface:** list/detail endpoints do **not** expose other suppliers’ quotes — summaries are fixed strings from **`customer_visible_summary()`** (English-only MVP text).

### Residual debt / forward hooks
- **Enum downgrade:** **`downgrade`** drops FK columns and **`commercial_resolution_kind`** type but **cannot** remove **`ALTER TYPE ... ADD VALUE`** entries from **`custom_marketplace_request_status`** (PostgreSQL limitation) — documented in migration file comment; plan environments accordingly.
- **PATCH `under_review`:** **`PATCH`** may set **`under_review`** without the stricter field rules enforced on **`POST .../resolution`** (resolution **`under_review`** rejects `selected_supplier_response_id` / `commercial_resolution_kind`). If product needs a strict state machine, align **`PATCH`** with resolution rules or disallow **`under_review`** on **`PATCH`** in a future narrow slice.
- **Track 5 forward:** RFQ → **`Order`** / reservation / payment integration (**5b.2+**), customer-facing multi-quote UX, notifications — **postponed**; **5b.1** bridge record only — see **§27**.

### Status
closed for **Track 5a** scope (selection + resolution recording + review); **no** Layer A semantic change attributed to this track

---

## 27. V2 Track 5b.1 — RFQ booking bridge record (Layer C) — implementation

### Current decision
- **Additive only:** Alembic **`20260423_12`** — table **`custom_request_booking_bridges`** (`request_id`, `selected_supplier_response_id`, `user_id`, nullable `tour_id`, `bridge_status`, `admin_note`, timestamps); enum **`custom_request_booking_bridge_status`**. **No** DDL on **`orders`** / **`payments`**; **no** calls to **`TemporaryReservationService`** or payment entry from bridge code.
- **Admin-only explicit trigger:** **`POST /admin/custom-requests/{id}/booking-bridge`** (optional `tour_id`, `admin_note`); **`PATCH .../booking-bridge`** narrows to `tour_id` / `admin_note` updates. **Not** a side effect of Track **5a** resolution.
- **Eligibility:** request **`supplier_selected`** or **`closed_assisted`**; **`selected_supplier_response_id`** set; response **`proposed`** and same **`request_id`**. **Active bridge** uniqueness: at most one row in **`pending_validation`**, **`ready`**, **`linked_tour`**, **`customer_notified`** per request — second **`POST` → 409**.
- **Tour link (optional):** if `tour_id` set, Tour must exist, **`open_for_sale`**, future **`departure_datetime`**, **`sales_deadline`** null or future, **`seats_available` ≥ 1** — validation for **future** Layer A execution only; **no** hold.
- **Admin read:** **`GET /admin/custom-requests/{id}`** includes **`booking_bridge`** (latest row for that request).

### Residual debt / forward hooks
- **Track 5b.3+:** payment entry UX from bridge context (reuse existing **`payment-entry`** only); supersede/cancel bridge workflows; handoff integration; optional admin “open booking for customer” — **explicit** slices only.
- **Concurrency (low priority):** duplicate active bridge prevention is enforced in **`CustomRequestBookingBridgeService.create_bridge`** before insert (**409**). A rare double-**POST** race could still insert two rows until a **partial unique index** (one active status per **`request_id`**) is added — only if ops reports issues.

### Stabilization review (Track 5b.1 — closure)
- **Scope creep:** **None found** in **`app/services/custom_request_booking_bridge_service.py`**, **`app/repositories/custom_request_booking_bridge.py`**, **`app/api/routes/admin.py`** (booking-bridge routes), **`app/models/custom_request_booking_bridge.py`**, Alembic **`20260423_12`**: **no** `Order` / hold / payment-session writes; **no** **`TemporaryReservationService`**; **no** auto-**`Tour`** creation; **no** customer bridge routes; **no** auth/handoff/marketplace redesign.
- **Track 5a unchanged:** **`admin_apply_resolution`** (**`custom_marketplace_request_service.py`**) updates request/selection fields only — **does not** call **`CustomRequestBookingBridgeService.create_bridge`** or **`patch_bridge`**.
- **Selected response:** Bridge row stores **`selected_supplier_response_id`** from the validated **`SupplierCustomRequestResponse`** (same **`request_id`**, **`proposed`**); not a free-form id.
- **PATCH safety:** **`AdminCustomRequestBookingBridgePatch`** allows **`tour_id`** / **`admin_note`** only; **no** status transitions to execution states in **5b.1**; **no** checkout side effects.
- **Supplier / customer reads:** **`get_open_for_supplier`** builds detail **without** **`booking_bridge`** (remains **admin-only** inspection in **5b.1**).

### Status
closed for **Track 5b.1** scope (bridge persistence + admin API + tests + stabilization review); explicit customer execution entry — **§28**

---

## 28. V2 Track 5b.2 — RFQ bridge execution entry (preparation + existing hold)

### Current decision
- **No new migration** — orchestration + Mini App routes only.
- **Explicit customer entry:** **`GET /mini-app/custom-requests/{id}/booking-bridge/preparation`**, **`POST /mini-app/custom-requests/{id}/booking-bridge/reservations`** — **not** side effects of **5a** resolution or **5b.1** admin bridge create/patch.
- **Gates:** **`CustomRequestBookingBridgeService.resolve_customer_execution_context`** — active bridge, **`tour_id`** set, request/selection/bridge integrity, owning **`telegram_user_id`**, execution-time tour + **`tour_is_customer_catalog_visible`**.
- **Policy:** **`TourSalesModePolicyService`** before hold; **`full_bus`** / non-self-serve → **200** blocked envelope on preparation **`GET`**; **`400`** **`operator_assistance_required`** on **`POST`** hold — **no** silent whole-bus self-serve.
- **Layer A reuse:** **`MiniAppReservationPreparationService.get_preparation`**, **`MiniAppBookingService.create_temporary_reservation`** — **no** new payment path; **no** payment rows created by this slice.
- **Bridge status:** after successful hold, active bridge → **`customer_notified`** (minimal progression).

### Residual debt / forward hooks
- Customer Mini App UX copy/CTA wiring from RFQ detail to these routes; **`POST .../payment-entry`** after hold using existing order id; **`closed_external`** guardrails if needed on execution routes.

### Stabilization review (Track 5b.2 — closure)
- **Scope creep:** **None found** — **`custom_request_booking_bridge_execution.py`**, **`mini_app.py`** bridge routes, **`custom_request_booking_bridge_service.py`** execution context: **no** **`PaymentEntryService`**, **no** **`start_payment_entry`**, **no** implicit calls from **`admin_apply_resolution`** or **`create_bridge`** / **`patch_bridge`** (verified **`custom_marketplace_request_service`** still only **`read_for_admin_detail`** for bridges).
- **Policy:** **`TourSalesModePolicyService.policy_for_tour`** in **`get_execution_preparation`** and **`create_execution_reservation`** before Layer A prep/hold; **`MiniAppBookingService.create_temporary_reservation`** still enforces policy internally (**defense in depth**).
- **Layer A:** **`TemporaryReservationService`** only via existing **`MiniAppBookingService`**; **no** parallel reservation engine.
- **`full_bus`:** preparation returns **200** blocked envelope; reservation **400** **`operator_assistance_required`** — **no** self-serve hold.
- **Bridge status:** **`customer_notified`** only after **successful** hold (**acceptable** minimal slice); preparation **GET** does **not** mutate bridge.
- **HTTP nuance (deferrable):** unknown **`telegram_user_id`** raises **`BookingBridgeNotFoundError`** → **404** `"User not found."` — slightly coarse vs **`400`** on other RFQ routes; **narrow later** only if clients need distinct **`unknown_user`** vs **`no_bridge`**.

### Status
closed for **Track 5b.2** scope (explicit preparation + hold orchestration + tests + stabilization review); payment initiation from bridge context **postponed** (**5b.3+**). **Execution gate composition** extended in **Track 5b.3a** — see **§29** (**`EffectiveCommercialExecutionPolicyService`** **in addition to** **`TourSalesModePolicyService`**; does not widen self-serve eligibility).

---

## 29. V2 Track 5b.3a — RFQ supplier policy + effective commercial execution resolver

### Intent (scope)
- **Additive DDL only:** **`20260424_13`** on **`supplier_custom_request_responses`** — **no** `orders` / `payments` / `tours` semantic rewrites.
- **Supplier intent at RFQ response row:** declared **`tour_sales_mode`** + **`supplier_offer_payment_mode`** mirror offer-level vocabulary; **conservative** allowed pairs only.
- **Single read-model resolver:** **`EffectiveCommercialExecutionPolicyService.resolve`** — composes Layer A **`TourSalesModePolicyService`**, supplier declaration, request **`closed_external`** / **`commercial_resolution_kind=external_record`** — **for gating reads and bridge execution only**; **does not** create payments or reservations.

### Supplier policy validation (verified)
- **Proposed:** both **`supplier_declared_sales_mode`** and **`supplier_declared_payment_mode`** **required** (**`SupplierCustomRequestResponseUpsert`**); invalid pairs rejected (**`full_bus` + `platform_checkout`**; no other exotic combos).
- **Declined:** declaring either field **rejected** by schema; repository upsert passes **`None`** — **clears** stored policy on decline.
- **Legacy / incomplete rows:** **`proposed`** with **NULL** policy columns → resolver treats as **`supplier_policy_incomplete`** — **blocks** self-serve (does **not** widen vs post-migration suppliers who must resubmit with fields).

### Effective resolver (verified)
- **`self_service_preparation_allowed`** / **`self_service_hold_allowed`** / **`platform_checkout_allowed`** are **True** only when: not external, not incomplete, supplier declared **`per_seat` + `platform_checkout`**, and **`TourSalesModePolicyService`** allows per-seat self-service — **conjunctive** (strict **narrowing** vs tour-only gate when supplier chose assisted/full-bus intent).
- **Assisted supplier intent** (**`assisted_closure`**, **`full_bus` + `assisted_closure`**, etc.): **`supplier_platform_per_seat_intent`** false → self-serve and platform checkout **blocked**.
- **External:** **`closed_external`** or **`external_record`** → **`external_only`**, checkout and self-serve **blocked**.
- **Stability:** deterministic flags + **`blocked_code`** / **`blocked_reason`** / **`customer_blocked_code`**; no random widening paths identified.

### Bridge execution + payment side effects (verified)
- **`CustomRequestBookingBridgeExecutionService`:** calls resolver **before** prep/hold; **`create_temporary_reservation`** unchanged; **no** **`PaymentEntryService`** / payment-session code in execution module.
- **`full_bus` tour:** still blocked via **`tour_sales_mode_blocks_self_service`** (same customer envelope family as before).
- **Per-seat happy path:** unchanged when supplier declares **`per_seat` + `platform_checkout`** and tour allows per-seat self-service.

### Read contracts (verified)
- **Mini App bridge preparation:** **`effective_execution_policy`** added — JSON clients that ignore unknown keys **remain safe**; strict clients must accept new required field on this response type (additive contract on **one** response model).
- **Admin detail:** **`effective_execution_policy`** nullable — present only when **`booking_bridge.tour_id`** and selected response exist; **`SupplierCustomRequestResponseRead`** includes supplier-declared fields for inspection.

### Stabilization review (Track 5b.3a — closure)
- **Scope creep:** **None found** — **no** new payment routes, **no** payment row creation from RFQ policy code paths, **no** quote-comparison UI, **no** portal/auth/handoff redesign (grep/service review: **`custom_request_booking_bridge_execution`**, **`effective_commercial_execution_policy`**, **`custom_marketplace_request_service`**, **`mini_app`** bridge routes).
- **Layer A / Tracks 0–5b.2:** standard catalog booking, private bot booking, supplier publication, **5a** resolution, **5b.1** bridge persistence **unchanged** except **additive** supplier **`PUT`** payload requirement for **new/updated proposed** responses and additive API read fields; **migrate → deploy → smoke** discipline preserved (**`COMMIT_PUSH_DEPLOY.md`**).

### Residual / forward
- **Track 5b.3b** — bridge payment **eligibility** read (**§30**) — **completed**; actual payment session remains **`POST /mini-app/orders/{order_id}/payment-entry`** only.
- **Track 5c** — Mini App RFQ bridge UX (**§31**) — **completed** (Flet wiring only; eligibility → existing payment stack).
- **Forward:** optional thin delegate POST — **not** required when eligibility + existing route suffice; supersede/cancel bridge; **“my requests”** hub.

### Status
**closed** for **Track 5b.3a** scope (policy columns + validation + resolver + bridge integration + tests + stabilization review).

---

## 30. V2 Track 5b.3b — Bridge payment eligibility + existing payment-entry reuse

### Intent
- **Read-only gate:** **`GET /mini-app/custom-requests/{request_id}/booking-bridge/payment-eligibility`** (`telegram_user_id`, **`order_id`** required) — returns **`MiniAppBridgePaymentEligibilityRead`** (`payment_entry_allowed`, `order_id`, `effective_execution_policy`, `blocked_code`, `blocked_reason`).
- **No new payment engine:** eligibility does **not** call **`PaymentEntryService.start_payment_entry`**; **`PaymentEntryService.is_order_valid_for_payment_entry`** (read-only) reuses the same rules as payment entry for order state.
- **Anchor:** explicit **`order_id`** from the bridge hold response — **no** guessing among multiple orders.

### Gate (all must hold for `payment_entry_allowed`)
- Active bridge + **`resolve_customer_execution_context`** integrity (same as **5b.2**).
- **`effective.platform_checkout_allowed`** (**5b.3a** resolver).
- Order exists; **`order.user_id`** = bridge customer; **`order.tour_id`** = **`bridge.tour_id`**.
- **`is_order_valid_for_payment_entry`** (reserved, awaiting payment, active cancellation, reservation not expired).

### Explicit non-goals (verified)
- **No** payment rows from eligibility GET; **no** bridge-authoritative payment lifecycle; **no** implicit payment on bridge create/patch/resolution.
- **No** new provider or payment schema.

### Stabilization review (Track 5b.3b — closure)
- **Scope creep:** **None found** — **`get_payment_eligibility`**, **`mini_app`** eligibility route, **`PaymentEntryService.is_order_valid_for_payment_entry`**: **no** `PaymentRepository.create` from eligibility path; **no** `start_payment_entry` from eligibility; **no** bridge-specific payment POST; **no** auto payment after hold; **no** calls from admin bridge create/patch or **5a** resolution; **no** auth/handoff/RFQ UI redesign.
- **Layer A:** **`start_payment_entry`** unchanged except additive read-only helper sharing **`_is_order_valid_for_payment_entry`**; catalog **`POST .../orders/{id}/payment-entry`**, private bot payment entry, **5b.2**/**5b.3a** unchanged in meaning.
- **Payment gate:** **`platform_checkout_allowed`** first; then **`resolve_customer_execution_context`** (active bridge, **`tour_id`**, selection/bridge sync, owning user, tour execution validation); explicit **`order_id`** query param (**no** order guessing); order user/tour alignment; Layer A validity (expired / wrong status → **`order_not_valid_for_payment`**); assisted/external/incomplete policy → blocked before order checks.
- **Read-only:** Eligibility route **no** `session.commit` in handler; service **no** flushes on bridge for eligibility; **`is_order_valid_for_payment_entry`** uses **`OrderRepository.get`** (no `FOR UPDATE`) — same predicate as **`start_payment_entry`** pre-check (**TOCTOU** between GET eligibility and POST payment-entry acceptable; **`start_payment_entry`** re-validates under lock).
- **Read contract:** New **GET** path only — clients that never call it **unchanged**; blocked responses use stable **`blocked_code`** / **`blocked_reason`** for future Mini App wiring.
- **Tests:** **`test_custom_request_booking_bridge_payment_eligibility_track5b3b`** (allowed path + **`payment-entry`** reuse, no payment rows on GET, assisted block, order_not_found / tour_mismatch / expired); regressions **5b.2**, **5b.3a**, **`PaymentEntryService`** — **pass** (acceptance run).

### Status
**closed** for **Track 5b.3b** scope (eligibility route + service + tests + stabilization review).

---

## 31. V2 Track 5c — RFQ Mini App UX wiring (bridge execution + payment continuation)

### Intent
- **Mini App only:** wire **`/custom-requests/{request_id}/bridge`** to **existing** Track **5b.2** preparation/reservation and Track **5b.3b** payment eligibility — **no** new backend payment or booking semantics.
- **CTA policy:** **`Confirm reservation`** after preview when self-service preparation is allowed; **`Continue to payment`** only when overview shows an **active** hold **and** **`payment_entry_allowed`**; then navigate to the **standard** tour payment route so **`POST /mini-app/orders/{order_id}/payment-entry`** runs unchanged.

### Explicit non-goals (verified in scope)
- **No** second reservation or payment architecture in UI; **no** bypass of **`EffectiveCommercialExecutionPolicyService`** / **`PaymentEntryService`**; **no** **`full_bus`** self-serve enablement.

### Residual / forward
- Customer **multi-quote** comparison UI, bridge **supersede/cancel**, bot deep-link templates — **not** **5c**; **My Requests** hub — **Track 5d** (**§32**).

### Stabilization review (Track 5c — closure)
- **Scope creep:** **None found** — changes are confined to **`mini_app/`** (**`api_client`**, **`app.py`**, **`ui_strings`**, **`rfq_bridge_logic`**, unit test); **no** edits to **`app/services/*`** booking/payment, **no** new FastAPI routes, **no** provider/session model, **no** quote-comparison UI, **no** bridge lifecycle/admin/auth/handoff redesign (repo grep + file review).
- **Backend/API consumption:** **`MiniAppApiClient`** calls only **existing** **`GET/POST /mini-app/custom-requests/{id}/booking-bridge/preparation|reservations`**, **`GET .../payment-eligibility`**, plus **already-used** catalog helpers **`GET .../tours/{code}/preparation-summary`** and **`GET .../orders/{id}/reservation-overview`** — same shapes as Track **5b.2** / **5b.3b** / catalog; **no** client-side contract widening (no extra query/body fields beyond server-defined **`MiniAppCreateReservationRequest`** and eligibility params).
- **UI branches:** **`self_service_available`** false → blocked envelope only (**no** seat/boarding, **no** reserve/pay CTAs); true + **`preparation`** → mirrors catalog **`per_seat_self_service_allowed`** gate (assisted copy, **no** confirm row when not per-seat); confirm appears only after successful **preview** (summary block); post-hold **`Continue to payment`** enabled only when **`rfq_bridge_continue_to_payment_allowed`** (active hold **and** **`payment_entry_allowed`**); hold active + pay blocked shows **`blocked_reason`** or safe fallback copy; expired/unknown overview uses existing hold messaging patterns.
- **Payment reuse:** **`RfqBridgeExecutionScreen`** receives **`on_continue_to_payment=self.open_payment_entry`** → **`page.go(/tours/{tour_code}/prepare/payment/{order_id})`** → existing view stack loads **`PaymentEntryScreen.load_payment_entry`** → **`POST /mini-app/orders/{order_id}/payment-entry`** only — **no** parallel payment screen or bridge-specific payment POST.
- **Standard flow:** Catalog **`/`**, **`/tours/...`**, **`/prepare`**, reserved/payment stacks, **`/custom-request`** (exact path) unchanged in ordering; bridge route **`/custom-requests/{id}/bridge`** matched only by dedicated regex **after** **`/custom-request`** branch — **no** path collision.
- **Tests:** **`test_mini_app_rfq_bridge_wiring`** (CTA gating); **`test_custom_request_booking_bridge_execution_track5b2`**, **`test_custom_request_booking_bridge_payment_eligibility_track5b3b`**, **`test_api_mini_app`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5c** scope (Flet wiring + CTA gating test + documentation) — **stabilization reviewed**.

---

## 32. V2 Track 5d — Mini App “My Requests” / RFQ status hub

### Intent
- **Mini App only:** **`/my-requests`** list + **`/my-requests/{id}`** detail — consumes **existing** **`GET /mini-app/custom-requests`**, **`GET .../{id}`**, **`GET .../booking-bridge/preparation`**, **`GET /mini-app/bookings`**, and **`GET .../booking-bridge/payment-eligibility`** (when an active temporary hold exists on the bridge **`tour_code`**).
- **Dominant CTA** (detail): **`Continue to payment`** only when eligibility allows; else **`Continue booking`** when **`self_service_available`**; else **`Open booking`** when a **Layer A** row exists for the linked tour (e.g. confirmed); else **no** CTA — **no** new commercial predicates beyond composing existing reads.

### Explicit non-goals
- **No** multi-quote comparison, **no** bridge supersede/cancel, **no** backend RFQ schema changes, **no** new payment/booking execution paths.

### Residual / forward
- Richer admin/customer notifications, bot deep links to **`/my-requests/{id}`**, quote comparison — **not** **5d**.

### Stabilization review (Track 5d — closure)
- **Scope creep:** **None found** — implementation is confined to **`mini_app/`** (**`app.py`**, **`rfq_hub_cta.py`**, **`ui_strings`**, unit test); **no** new **`app/api/*`** routes, **no** service-layer booking/payment changes, **no** quote comparison, bridge supersede/cancel, notifications, auth, or handoff redesign (grep **`app/api`**, **`app/services`**).
- **Backend/API composition:** **`MiniAppApiClient`** unchanged for new endpoints — hub uses existing **`GET /mini-app/custom-requests`**, **`GET /mini-app/custom-requests/{id}`**, **`GET .../booking-bridge/preparation`**, **`GET /mini-app/bookings`**, **`GET .../booking-bridge/payment-eligibility`** (same query/body contracts as Tracks **5b.2** / **5b.3b** / bookings list); **no** client-side contract widening.
- **Routing:** **`/my-requests`** and **`/my-requests/{id}`** are Flet-only paths; **`_extract_my_request_detail_id`** regex does not collide with **`/custom-requests/{id}/bridge`** or **`/custom-request`**; detail stack mirrors **`/bookings/{id}`** pattern (catalog + list + detail views).
- **CTA resolution:** **`resolve_detail_primary_cta`** returns a **single** dominant kind (payment → confirmed/in-trip open booking → continue booking → any matching tour open booking → none); **`MyRequestDetailScreen`** exposes at most one **`FilledButton`** — mutually exclusive by construction.
- **Bridge/payment reuse:** **`Continue booking`** → **`on_open_bridge` → `open_rfq_bridge_booking` → `/custom-requests/{id}/bridge`** (Track **5c**); **`Continue to payment`** → **`on_continue_payment` → `open_payment_entry`** → standard payment stack + **`POST .../payment-entry`**; **`Open booking`** → **`open_booking_detail`** → **`/bookings/{order_id}`** — **no** parallel RFQ payment or hold UI.
- **Accepted limitation (documented):** **`pick_booking_for_bridge_tour`** runs only when **`prep` is not None** (linked **`tour_code`** from bridge). If preparation returns **404**, the hub does **not** infer **`Open booking`** from generic bookings alone — avoids false links between unrelated orders and RFQs; users still have **My bookings**.
- **Tests:** **`test_mini_app_rfq_hub_cta`**; regressions **`test_mini_app_rfq_bridge_wiring`**, **`test_api_mini_app`**, **`test_custom_marketplace_track5a`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5d** scope (Flet hub + **`mini_app/rfq_hub_cta`** + tests + documentation) — **stabilization reviewed**.

**Track 5e follow-on (hub):** **`MyRequestDetailScreen`** now uses **`latest_booking_bridge_tour_code`** from **`GET /mini-app/custom-requests/{id}`** when preparation is unavailable so **`pick_booking_for_bridge_tour`** can still align **Layer A** bookings to the linked tour after a terminal bridge — see **§33**.

---

## 33. V2 Track 5e — Bridge supersede / cancel lifecycle

### Intent
- **Admin-only** transitions: active bridge → **`superseded`** or **`cancelled`** (**`POST .../booking-bridge/close`**); **replace** path (**`POST .../booking-bridge/replace`**) sets active row to **`superseded`** (if any) then **`create_bridge`** in the **same** DB transaction — avoids the **409** window between close and recreate.
- **Orchestration only:** bridge rows remain **non-authoritative** for orders/payments; close/replace **must not** touch **`orders`** / **`payments`** or **`CustomMarketplaceRequest.status`**.
- **Customer fail-closed:** **`resolve_customer_execution_context`** uses **`get_active_for_request`** (terminal statuses excluded); preparation / reservations / payment-eligibility return **404** when no active bridge.

### Explicit non-goals (verified)
- **No** auto-supersede on winner change, **no** `superseded_by_bridge_id`, **no** refund/cancel-order from bridge, **no** new payment/booking **routes** or provider flows, **no** auth/handoff redesign, **no** RFQ request lifecycle redesign.

### Additive read contract
- **`MiniAppCustomRequestCustomerDetailRead`:** **`latest_booking_bridge_status`**, **`latest_booking_bridge_tour_code`** (nullable) — JSON clients that ignore unknown keys remain safe; strict clients must accept new optional fields on this response type. **Track 5f v1** adds **`proposed_response_count`**, **`offers_received_hint`**, **`selected_offer_summary`** — see **§34**. **Track 5g.1** adds **`commercial_mode`** — see **§35**.

### Residual / forward
- Partial unique index (one **active** bridge per **`request_id`**) if ops reports rare double-**POST** races (**§27**); structured closure reason / audit columns — **explicit** slices only.

### Stabilization review (Track 5e — closure)
- **Scope creep:** **None found** — changes are confined to bridge service/admin routes, customer detail enrichment, Mini App hub/bridge copy + **`rfq_hub_cta`**, **`ui_strings`**, **`tests/unit/test_custom_request_booking_bridge_track5e.py`**, **`test_mini_app_rfq_hub_cta`**; **no** order/payment write services invoked from close/replace; **no** **`TemporaryReservationService`** / **`PaymentEntryService`** mutations from bridge lifecycle.
- **Layer A:** holds and payment validity remain enforced by existing Layer A services; bridge close does not expire or cancel reservations; **Continue to payment** on terminal bridge + active hold uses **`order_id`** via existing **`open_payment_entry`** stack (**`POST .../payment-entry`** still authoritative).
- **Tests:** **`test_custom_request_booking_bridge_track5e`** (close, replace, 404 on execution paths, request status + order unchanged); **`test_mini_app_rfq_hub_cta`** (terminal + hold CTA); regressions **`test_custom_request_booking_bridge_execution_track5b2`**, **`test_custom_request_booking_bridge_payment_eligibility_track5b3b`**, **`test_custom_request_booking_bridge_track5b1`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5e** scope (admin close/replace + fail-closed customer bridge endpoints + hub/detail additive fields + tests + documentation) — **stabilization reviewed**.

---

## 34. V2 Track 5f v1 — Customer multi-quote summary / aggregate visibility

### Intent
- **Read-only** customer visibility on **`GET /mini-app/custom-requests/{id}`**: **`proposed_response_count`**, **`offers_received_hint`**, **`selected_offer_summary`** (nullable nested model).
- **Count:** **`proposed`** responses only — **`declined`** excluded (**`SupplierCustomRequestResponseRepository.count_proposed_for_request`**).
- **Hint:** status-aware neutral English strings (**same MVP style** as **`customer_visible_summary`**); not a bidding or choice prompt.
- **Selected snippet:** only when **`selected_supplier_response_id`** is set **and** request status is **`supplier_selected`**, **`closed_assisted`**, **`closed_external`**, or **`fulfilled`** **and** loaded row is **`proposed`** for the **same** **`request_id`** — allowlisted **`quoted_price`**, **`quoted_currency`**, truncated **`supplier_message_excerpt`** (200 chars), **`declared_sales_mode`**, **`declared_payment_mode`** — **no** supplier code/name/id.

### Explicit non-goals (verified)
- **No** customer winner choice, **no** comparison cards, **no** competing supplier UI, **no** new **`POST`** customer routes, **no** bridge/payment/booking execution changes, **no** request lifecycle redesign.

### Mini App
- **`MyRequestDetailScreen._render_body`** only — informational **`Text`** / **`Column`**; **no** changes to **`resolve_detail_primary_cta`** or hub primary button logic.

### Additive read contract
- **`MiniAppCustomRequestCustomerDetailRead`** extended per **§34**; strict JSON clients must accept new fields; ignores-unknown-keys clients remain safe.

### Residual / forward
- **5f v2+:** anonymized multi-card compare, localized **`offers_received_hint`**, list-row offer hints — **explicit** slices only.

### Stabilization review (Track 5f v1 — closure)
- **Scope creep:** **None found** — **`app/repositories/custom_marketplace.py`** (count), **`app/schemas/custom_marketplace.py`**, **`app/services/custom_marketplace_request_service.py`**, **`mini_app/app.py`** (detail body only), **`mini_app/ui_strings.py`**, **`tests/unit/test_custom_marketplace_track5f_v1.py`**; **no** edits to bridge execution, **`PaymentEntryService`**, or hub CTA helpers.
- **5a authority:** snippet is **derived** from admin **`selected_supplier_response_id`** only; **no** alternate actionable offers.
- **Tests:** **`test_custom_marketplace_track5f_v1`**; regressions **`test_custom_marketplace_track5a`**, **`test_mini_app_rfq_hub_cta`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5f v1** scope (aggregate + allowlisted selected snippet + My Requests detail read-only copy + tests + documentation) — **stabilization reviewed**.

---

## 35. V2 Track 5g.1 — Commercial mode classification (read-side only)

### Intent (Track 5g design gate)
- Explicit **presentation-level** distinction between **Mode 1** (**`supplier_route_per_seat`**), **Mode 2** (**`supplier_route_full_bus`** — catalog full-bus, not RFQ by default), and **Mode 3** (**`custom_bus_rental_request`** — Layer C RFQ).
- **Authoritative derivation:** catalog modes from **`Tour.sales_mode`** only; RFQ detail mode is **constant** **`custom_bus_rental_request`** for **`CustomMarketplaceRequest`** customer reads (no hybrid modes in this slice).

### Implementation surface
- **`CustomerCommercialMode`** (`app/models/enums.py`).
- **`commercial_mode_for_catalog_tour_sales_mode`** (`app/services/customer_commercial_mode_read.py`).
- **`MiniAppTourDetailRead.commercial_mode`** (`app/schemas/mini_app.py`; composed in **`MiniAppTourDetailService`**).
- **`MiniAppCustomRequestCustomerDetailRead.commercial_mode`** (`app/schemas/custom_marketplace.py`; set in **`CustomMarketplaceRequestService.get_customer_detail_mini_app`**).

### Explicit non-goals (verified)
- **No** booking/reserve/payment/bridge execution changes; **no** **`EffectiveCommercialExecutionPolicyService`** / **`PaymentEntryService`** behavior change; **no** RFQ resolution or supplier-response rules change; **no** Mini App CTA or bot routing driven by **`commercial_mode`** in this slice; **no** admin workflow; **no** reopening **Track 5f v1** semantics (**`proposed_response_count`**, hints, snippet unchanged in meaning).

### Additive read contract
- New JSON keys on two existing GET responses; clients that ignore unknown keys remain safe; strict clients must accept **`commercial_mode`** (string enum values as above).

### Stabilization review (Track 5g.1 — closure)
- **Scope creep:** **None found** — grep-confined to enums, mapper, **`mini_app`** / **`custom_marketplace`** schemas, **`mini_app_tour_detail`**, **`custom_marketplace_request_service`** (customer detail only), and focused tests; **no** edits to bridge services, payment entry, or order lifecycle.
- **Classification:** **`per_seat` → `supplier_route_per_seat`**, **`full_bus` → `supplier_route_full_bus`**, customer RFQ detail **`custom_bus_rental_request`** — matches Track **5g** three-mode model; **Mode 2** remains catalog (**Layer A**), **Mode 3** remains RFQ (**Layer C**).
- **Tests:** **`test_customer_commercial_mode_read`**, **`test_services_mini_app_tour_detail`** (incl. full-bus), **`test_api_mini_app`** (tour detail), **`test_custom_marketplace_track5f_v1`** (**`commercial_mode`** on detail); regressions **`test_custom_marketplace_track5a`**, **`test_custom_request_booking_bridge_track5e`**, **`test_custom_marketplace_track4`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5g.1** scope (read-side classification + documentation) — **stabilization reviewed**.

---

## 36. V2 Tracks 5g.4a–5g.4e — Catalog Mode 2 Mini App path (closure)

### Intent
- Record **acceptance** that **standalone catalog Mode 2** (virgin whole-bus catalog self-serve on **Layer A**) is **implemented and closed** through **5g.4d**; **5g.4e** is documentation-only.
- **Not** Mode 3 (RFQ), **not** bridge execution changes, **not** payment reconciliation redesign.

### Single source of truth for scope
- **`docs/TRACK_5G4_MODE2_ACCEPTANCE_SUMMARY.md`** — implemented slices, user behavior, non-goals, postponed items, test pointers.

### Non-regression boundaries (verified by track constraints)
- **Mode 1** per-seat semantics; **RFQ/bridge** execution; **`PaymentReconciliationService`**; supplier marketplace **admin/supplier** flows beyond shared **Layer A** reads; **charter pricing model**; **waitlist/handoff** workflows — **unchanged in meaning** by **5g.4** (presentation + narrow read/formatting only where documented in that summary).

### Status
**closed** for **Tracks 5g.4a–5g.4e** — reopen only for **regressions** or **security**; forward product work is **outside** this branch (see acceptance doc **Postponed**).
