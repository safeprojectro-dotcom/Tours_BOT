# B15O — Publishing Console Foundation Closure

**Slice:** B15O — formal **documentation / architecture** closure for the **Admin Publishing Console** foundation track.

---

## 1. Status

- **B15 Publishing Console Foundation:** **closed** (read-model + guarded internal preparation only; no public automation).
- **Closure type:** documentation / architecture checkpoint (**B15O**). **No code, schema, route, test, or migration changes** are part of B15O.
- **B15O introduces:** this document and minimal cross-links in other docs only.
- **No Telegram I/O,** **no scheduler,** **no auto-publish,** **no publish attempts** from the publishing-console **read** surfaces.

---

## 2. Scope closed (implementation + smoke / design record)

Supporting **B16** prepare-chain stack:

| Item | Role | Doc |
|------|------|-----|
| **B16D2C** | Guarded **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`** (admin auth, idempotency, confirm for live, dry_run). | [`HANDOFF_B16D2C_PREPARE_CONVERSION_CHAIN_API_ENDPOINT.md`](HANDOFF_B16D2C_PREPARE_CONVERSION_CHAIN_API_ENDPOINT.md), [`B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`](B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md) |
| **B16D2D** | Read-model **`prepare_conversion_chain_action`** affordance on review-package, publishing console, ops dashboard (metadata only). | [`HANDOFF_B16D2D_PREPARE_CONVERSION_CHAIN_ACTION_AFFORDANCES.md`](HANDOFF_B16D2D_PREPARE_CONVERSION_CHAIN_ACTION_AFFORDANCES.md) |
| **B16D2E** | Production / Railway smoke runbook for **`POST …/prepare-conversion-chain`**. | [`B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md`](B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md) |
| **B15E2** | Same execution as B16D2C from **`POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain`** (`actor_surface=publishing_console`). | [`HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md`](HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md), [`B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md`](B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md) |

Publishing-console **read track** (closed + smoke-verified per project records):

| Item | Role | Doc |
|------|------|-----|
| **B15G** | Guarded auto-publish — **design only** (no runtime). | [`B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md) |
| **B15H** | **`publish_readiness`** metadata (suggest-only). | [`HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md`](HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md), [`B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md`](B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md) |
| **B15I** | UX layer on **`publish_readiness`** (summary, badge, next action, gate summary, etc.). | [`HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md`](HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md), [`B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md`](B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md) |
| **B15F2/B15F3** | **`console_preview`** display metadata on console rows. | [`HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md`](HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md) |
| **B15K** | **`template_library`** metadata (variants, selection hints). | [`HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md`](HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md) |
| **B15L** | **`preview_payload`** structured showcase-oriented fields. | [`HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md`](HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md) |
| **B15M** | **`GET …/publishing-console/supplier-offers/{offer_id}`** detail read view. | [`HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md`](HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md) |

Earlier foundation slices (**B15B–B15F**, **B15C** chain) remain recorded in [`B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md).

---

## 3. Available admin read surfaces

| GET | Purpose |
|-----|---------|
| **`GET /admin/publishing-console`** | Read-only **candidate queue**: supplier-offer rows and tour-promotion rows; **`limit`**, optional **`kind`** (`supplier_offer_initial`, `tour_promotion`, or console status filters per API contract). Carries **`publish_readiness`**, **`console_preview`**, **`template_library`**, **`preview_payload`**, **`actions[]`**, paths, B15D/B15F fields. **No mutations.** |
| **`GET /admin/publishing-console?kind=supplier_offer_initial`** | Same endpoint; narrows to **supplier-offer** candidates only. |
| **`GET /admin/publishing-console/supplier-offers/{offer_id}`** (**B15M**) | **Single-offer** publishing-console detail: aggregates the same nested read objects as list rows plus **conversion / linked-tour / publication / safety** summaries. **404** if missing. **Not** filtered like the list queue (offers omitted from the queue may still have detail). |
| **`GET /admin/supplier-offers/{offer_id}/review-package`** | Canonical **operator** read model: offer, packaging, moderation, showcase preview, bridge/catalog/execution closure, **`operator_workflow`**, **`publish_readiness`**, prepare-chain plan path/status, warnings, recommended actions. **No mutations from GET.** |
| **`GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan`** (**B16D1**) | Read-only **plan preview**: future prepare-chain steps, blockers, recommended action, explicit **will-not-do** boundaries. **Does not** execute the chain. |

---

## 4. Available guarded mutation surfaces (not public publish automation)

Both endpoints invoke the same internal **prepare_conversion_chain** execution (**below Telegram showcase publish**):

- **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`** (**B16D2C**)
- **`POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain`** (**B15E2**)

**Behavior (summary):**

- **Internal chain only:** tour bridge materialization/linking, catalog activation when eligible, active execution link — via existing admin services and audit/idempotency (**B16D2A/B**).
- **`idempotency_key`:** required (non-blank); replays return stored attempt semantics.
- **Live run:** **`confirm=true`** required when **`dry_run`** is false.
- **`dry_run`:** supported for safe preview of intent.
- **Not in scope:** Telegram send/publish/retry; **`POST …/publish`**; Layer A booking/payment/reservation/seat mutation; Mini App/B11 routing changes (see [`B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md`](B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md)).

---

## 5. Read-model objects now available

### `publish_readiness` (`AdminPublishReadinessRead`)

- **`status`**, **`recommended_action`**, **`gates[]`** (code, label, status, reason, severity), gate counts.
- **`can_suggest_manual_publish`**
- **`can_auto_publish`:** always **`false`**
- **`auto_publish_mode`:** always **`disabled`**
- **`publish_action_path`**, **`prepare_conversion_chain_plan_path`**, **`generated_at`**
- **B15I UX:** **`summary`**, **`badge`**, **`next_action_code`**, **`next_action_label`**, **`primary_blocker`**, **`warning_summary`**, **`gate_summary`**

### `console_preview`

Compact **preview status**, **template family**, titles/summaries, CTA/target hints, preview path, **`safety_note`**, next-action labels — **read-only** admin UX (**B15F2/B15F3**).

### `template_library`

**Family**, **selected / recommended template ids**, **available_templates[]** (status per variant: available, future, not_applicable, blocked), **`selection_reason`**, **`safety_note`** (**B15K**). Tour-promotion rows use placeholder / **future** variants.

### `preview_payload`

**Payload status**, **source**, title/subtitle, body, caption, primary/secondary CTA, media/channel summaries, **`warnings`**, **`blockers`**, **`safety_note`**, **`generated_at`**, cross-notes to **`publish_readiness`** and **`template_library`** (**B15L**).

### Supplier-offer publishing-console detail (**B15M**)

Aggregates **`publish_readiness`**, **`console_preview`**, **`template_library`**, **`preview_payload`**, **`actions`**, path metadata (**`review_package_path`**, **`prepare_conversion_chain_plan_path`**, **`publish_action_path`**, **`prepare_conversion_chain_action`**), **`conversion_summary`**, **`linked_tour_summary`**, **`publication_summary`**, **`safety_summary`**, **`generated_at`**, **`detail_notice`**.

---

## 6. Safety boundaries preserved

- **No auto-publish** and **no scheduler** on publishing-console **GET** routes or B15O.
- **No Telegram send/publish/retry** triggered by publishing-console read endpoints.
- **No hidden publish**; **no publish attempts** created from **GET** read surfaces.
- **No `prepare_conversion_chain` execution** from **GET** / plan-only reads; execution only via the two guarded **POST**s above.
- **No Layer A** booking/payment/order/reservation/seat mutation from this track’s publishing-console read paths or from prepare-chain **POST** (internal conversion prep only).
- **No Mini App/B11 routing changes** from B15 read-model work.
- **No migration** in the B15 read-model line (**B15H–B15M**).
- **`can_auto_publish`** remains **false**; **`auto_publish_mode`** remains **disabled**.
- **Public showcase publish** remains an **explicit, separate** operator action (e.g. existing publish flows), **not** implied by readiness metadata.
- **Telegram channel** remains a softer **showcase/discovery** surface; **Mini App + catalog + execution link** remain the **strict execution truth** for booking.
- **visibility ≠ bookability** (catalog/activation/execution-link gates stay explicit).

---

## 7. Railway / production smoke evidence (operator-recorded)

Summaries below align with project smoke runbooks and manual verification. Detailed steps: linked docs.

### B16D2E — `POST …/supplier-offers/{id}/prepare-conversion-chain` (e.g. offer **12**)

- **dry_run:** passed  
- **live:** passed  
- **replay / idempotency:** passed  
- **Outcome context:** chain **already_prepared** where bridge + catalog + execution link already exist  
- **Boundaries:** no Telegram I/O; no Layer A mutation  

Record: [`B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md`](B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md)

### B15E2 — `POST …/publishing-console/supplier-offers/{id}/prepare-conversion-chain`

- **dry_run / live / replay:** passed  
- **`actor_surface=publishing_console`**  
- **No Telegram / no Layer A**  

Record: [`B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md`](B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md)

### B15H

- **`publish_readiness`** visible on **review-package** and **publishing-console** supplier-offer rows  
- **`can_auto_publish=false`**, **`auto_publish_mode=disabled`**  

Record: [`B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md`](B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md)

### B15I

- **summary / badge / next action / gate_summary** visible  
- **`can_auto_publish=false`**  

Record: [`B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md`](B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md)

### B15F2/B15F3

- **`console_preview`** visible on console items  
- **tour_promotion** rows: **placeholder / read-only** preview semantics  

### B15K

- **`template_library`** visible  
- **tour_promotion:** variants **future / not implemented**  

### B15L

- **`preview_payload`** visible  
- **tour_promotion:** **`source=tour_placeholder`**  
- **Safety note** documents **no Telegram API calls** from the read model  

### B15M — `GET /admin/publishing-console/supplier-offers/12` (Railway sample)

Operator-recorded response highlights:

- **`supplier_offer_id=12`**, **`candidate_key=supplier_offer:12`**, **`kind=supplier_offer_initial`**
- **`publish_readiness.status=already_published`**
- **`console_preview.preview_status=available`**
- **`template_library.family=supplier_offer_showcase`**
- **`preview_payload.payload_status=available`**
- **`tour_code=B10-SO12-04fb1f`**
- **`conversion_summary`:** **`has_tour_bridge=true`**, **`has_catalog_visible_tour=true`**, **`has_active_execution_link=true`**
- **`publication_summary.already_published=true`**
- **`safety_summary`:** **`read_only`**, **`no_telegram_io`**, **`no_publish_attempt`**, **`no_prepare_chain_execution`**, **`no_layer_a_mutation`** all **true**

*(Stored as closure evidence in B15O; operator offers may differ.)*

---

## 8. What is intentionally not done

- Public **auto-publish**, **scheduled publish**, **Telegram automatic send**, **batch publish**
- **Channel editor**; **template editor** that **persists** template selections
- **Real tour-promotion post generator** (placeholder read models only)
- **Mini App** / **B11** routing changes driven by this foundation
- **Payment / order / reservation / seat** changes from publishing-console reads or from prepare-chain POST
- **Supplier execution retries** as part of this track
- **AI-generated public text auto-send**

---

## 9. Future work gates (separate design / go–no-go only)

Requires explicit product, security, and design approval before implementation:

- **Channel editor** / **template editor** UX
- **Scheduled publish** (even after approval, needs charter)
- **Batch approval** workflows
- **Telegram publish automation** (send, retry policy)
- **Auto-publish** modes beyond today’s **disabled** metadata (see **B15G**)
- **Durable media storage/rendering** for marketing-grade assets
- **Provider retry policy** for channel operations
- **Public post edit/delete/unpublish** workflow
- **Admin frontend buttons that execute publish** (must stay confirmation-gated and out of “read-only” slices)

Design pointers: [`B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md), [`B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md) (where referenced from [`CHAT_HANDOFF.md`](CHAT_HANDOFF.md)).

---

## 10. Recommended next track

**Close B15 foundation here (B15O).** Prefer a **conservative** next step:

| Option | Description |
|--------|-------------|
| **A — B15P (suggested)** | Admin **UI polish / read-only frontend alignment**: copy, labels, button affordances, display groups — **no new backend mutation**. |
| **B — B17** | **Channel/template editor design gate:** **design-only first**; **no** send/publish implementation in the same slice. |
| **C — B18** | **Public publish automation** go/no-go — **only if** stakeholders explicitly choose to move toward Telegram automation. |

**Recommendation:** **Option A** or **Option B** next. **Do not** jump straight to **auto-publish** (**C**) without explicit charter and risk review.

**Clean checkpoint (git):** record the commit that adds B15O docs after operator review — **pending commit** until committed locally.

---

## Related

- Narrative slice index + table: [`B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)
- Living continuity log: [`CHAT_HANDOFF.md`](CHAT_HANDOFF.md)
- Implementation / marketplace context (superset): [`IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`](IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md), [`TECH_SPEC_TOURS_BOT_v1.1.md`](TECH_SPEC_TOURS_BOT_v1.1.md)
