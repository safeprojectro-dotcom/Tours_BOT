# B15 — Admin Publishing Console foundation closure checkpoint

**Status:** Closed (docs checkpoint).  
**Scope:** **B15B–B15F** plus **B15F2/B15F3**, **B15K**, and **B15L** (additive) — safe, **read-only** admin publishing console **foundation** + **template/preview display** (`console_preview`) + **template library** (`template_library`) + **preview payload** (`preview_payload`) metadata on console rows; execution-heavy product (auto-publish, console-side mutations, template/channel editors) stays **approval-gated**.  
**Handoff:** [`docs/HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT_TO_NEXT_STEP.md).  
**Prompt archive:** [`docs/CURSOR_PROMPT_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT.md`](CURSOR_PROMPT_B15_CLOSE_PUBLISHING_CONSOLE_FOUNDATION_CHECKPOINT.md).

**Related:** **B15A** umbrella design [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md); **B15C** exact CTA gate [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md); **B15C6** chain checkpoint [`docs/B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md`](B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md).

---

## 1. Scope

The **safe publishing console foundation** delivered across **B15B–B15F** is **closed** for its intended slice:

- **B15B** — read-only candidate queue API.
- **B15C** — exact-tour **Rezervă** / conversion safety chain (product + gates; not the console HTTP route itself).
- **B15D** — richer readiness, blockers, CTA safety, admin/preview paths on the console read model.
- **B15E** — read-only **`actions[]`** affordance metadata (no execution from the console **GET** route **prior** to **B15E2**).

**B15E2 (implemented):** narrow **POST** **`/admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain`** executes guarded **`prepare_conversion_chain`** only (**[`HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md`](HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md)**). Does **not** change **`GET /admin/publishing-console`** semantics (still read-only queue).

- **B15F** — source / template / channel / media metadata plus future-disabled capability hints.
- **B15F2/B15F3** — read-only **`console_preview`** (`AdminPublishingConsolePreviewRead`): compact template family, preview status, CTA/target hints, **`safety_note`**, and next-action labels for admin UX only (**separate** DTO from `AdminPublishingConsoleItemRead`); **no** Telegram I/O, publish attempts, scheduler, **`prepare_conversion_chain`** execution, Layer A mutation, or migration (**unit tests** extended in **`test_admin_publishing_console`**).
- **B15K** — read-only **`template_library`** (`AdminPublishingConsoleTemplateLibraryRead`): variant list (**`PublishingConsoleTemplateLibraryFamily`**, **`PublishingConsoleTemplateLibraryEntryStatus`**, **`AdminPublishingConsoleTemplateLibraryEntryRead`**), selected/recommended ids, **`selection_reason`**, **`safety_note`**. **`supplier_offer_initial`** rows expose **`supplier_offer_showcase`** metadata; **`custom_request_cta`** as a variant where applicable; **`tour_promotion`** rows remain placeholder/read-only (**`future`** variants). **`console_preview`** preserved. **No** Telegram I/O, publish attempts, scheduler, auto-publish, **`prepare_conversion_chain`** execution, Layer A mutation, Mini App/B11 routing changes, or migration.
- **B15L** — read-only **`preview_payload`** (`AdminPublishingConsolePreviewPayloadRead`): **`PublishingConsolePreviewPayloadStatus`**, **`PublishingConsolePreviewPayloadSource`**, title/body/caption/CTA/media/channel summaries, **`warnings`**, **`blockers`**, **`safety_note`**, **`generated_at`**; **`publish_readiness_note`** / **`template_library_note`** tie the payload to the same row’s **`publish_readiness`** and **`template_library`**. **`supplier_offer_initial`** rows use **`showcase_preview`** + supplier-offer/review-package data; **`tour_promotion`** rows use **`source=tour_placeholder`**. **No** Telegram I/O, publish attempts, scheduler, auto-publish, **`prepare_conversion_chain`** execution, Layer A mutation, Mini App/B11 routing changes, migration, or Telegram/provider API calls.

**B15C** remains documented as the **accepted operator conversion order** and production-smoke baseline; see §3–§4.

---

## 2. What is now available (`GET /admin/publishing-console`)

Single **read-only** endpoint (B15B) extended additively:

| Capability | Slice | Notes |
|------------|-------|--------|
| Candidate cards (supplier offers, tour promotion) | B15B | `limit` / `kind`; no mutations. |
| Readiness / blocker summaries | B15D | e.g. `readiness_summary`, `readiness_level`, `primary_blocker`, `blocker_codes`. |
| Exact CTA safety visibility | B15D | e.g. `cta_safety_status`, conversion target fields, B15C-aligned hints. |
| Next action hints | B15D | e.g. `next_action_code`, `next_action_label`, `admin_action_path`, `preview_path`, `audit_hint`. |
| Read-only action affordances | B15E | per-item `actions[]` — metadata only; mirrors `operator_workflow` / console / future. |
| Source / template / channel / media metadata | B15F | e.g. `source_*`, `template_*`, `channel_*`, `media_policy_status`, `media_summary`. |
| Future-disabled capability hints | B15F | `template_actions[]`, `channel_actions[]` (`implemented: false`). |
| Template / preview display metadata | B15F2/B15F3 | Per-item `console_preview` (`AdminPublishingConsolePreviewRead`): e.g. `preview_status`, `template_family`, optional title/summary/CTA/target/preview path, `safety_note`, `next_action_*`. Supplier-offer rows: showcase-oriented preview where data allows; tour-promotion rows: placeholder/read-only. |
| Template library (variants / selection hints) | B15K | Per-item `template_library` (`AdminPublishingConsoleTemplateLibraryRead`): `family`, `available_templates[]` (id, label, description, `status`, `disabled_reason`), `selected_template_id`, `recommended_template_id`, `template_version`, `selection_reason`, `safety_note`. Does not replace `console_preview`. |
| Showcase preview payload (structured) | B15L | Per-item `preview_payload` (`AdminPublishingConsolePreviewPayloadRead`): `payload_status`, `source`, title/subtitle, `body_text`, `caption_html`, primary/secondary CTA labels+URLs, `media_reference`, `media_status`, channel fields, `warnings[]`, `blockers[]`, `safety_note`, `generated_at`, `publish_readiness_note`, `template_library_note`. Supplier-offer rows: review-package `showcase_preview` + offer fallbacks; tour rows: `tour_placeholder`. |

Canonical field lists: [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md), [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md).

---

## 3. Correct supplier-offer publish / conversion order (B15C accepted chain)

1. Packaging / moderation **approved** for the path that allows bridge and showcase work.
2. **Tour bridge** created or linked (offer → `Tour` instance).
3. **Tour activated** for Mini App catalog (`open_for_sale` where applicable).
4. **Active execution link** created (booking link before channel publish when gates require it).
5. **Showcase / channel publish** allowed when workflow + B15C gates pass.
6. Channel **Rezervă** opens **exact Mini App tour** (e.g. short-name `startapp` link to `/tours/{tour_code}`).
7. **Layer A** handles reservation / payment after the customer lands on the tour.

Operators should treat **`GET …/review-package`** as the source of truth for what is blocking, not button order alone.

---

## 4. Production evidence (B15C / B15C5)

Recorded operator smoke — Offer **#15**, Tour **#9**, tour code **`B10-SO15-460344`**, execution link **#8**, publish attempt **#6**, showcase message **#28**, CTA  
`https://t.me/tours_tm_bot/banattours?startapp=tour_B10-SO15-460344`, temp hold/order **#55**, no identity warning, payment screen reached.  
Detail: [`docs/B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md`](B15C5_DIRECT_MINI_APP_LINK_PRODUCTION_SMOKE_RESULT.md); additional B15C notes: [`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md).

---

## 5. Safety boundaries preserved (B15B–B15F)

The console **foundation** does **not** introduce:

- **Auto-publish** or **scheduler** from `GET /admin/publishing-console`.
- **Action execution** endpoint on the console read path (B15E is metadata only).
- **Template editor** or **channel selector** (B15F hints only; `implemented: false`).
- **Telegram send / retry** triggered by the console read route.
- **Layer A** changes, **Mini App routing** / **B11** deep-link behavior, or **migrations** for these slices (including **B15K** / **B15L** read-model additions).
- **Supplier-side publish** (supplier marketplace remains out of scope for this checkpoint).
- **Fake urgency / availability** copy as a product requirement for the console (console remains observational).

Dangerous automation and execution UX remain **explicitly future-gated** (§7).

---

## 6. Tests and evidence pointers

- **Unit:** `tests/unit/test_admin_publishing_console.py` — **8 passed** (covers B15D / B15E / B15F / **B15F2–B15F3** `console_preview` / **B15K** `template_library` / **B15L** `preview_payload` additive read model on the same endpoint).
- **Production / operator smoke:** **B15C** docs (§4 and linked runbooks), not replaced by console unit tests.

---

## 7. Future gated options

**B15F2/B15F3 (closed in-repo):** Read-only **`console_preview`** / **`AdminPublishingConsolePreviewRead`** on **`GET /admin/publishing-console`** — **[`docs/HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md`](HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md)**. **`AdminPublishingConsolePreviewRead`** is **separate** from **`AdminPublishingConsoleItemRead`**; **`supplier_offer_initial`** rows carry showcase-oriented preview metadata; **`tour_promotion`** rows remain placeholder/read-only. **`tests/unit/test_admin_publishing_console.py`** covers **`console_preview`**. **No** Telegram I/O, publish attempts, scheduler/auto-publish, prepare-chain execution, Layer A mutation, migration, commits, or pushes were touched. *(A future **template editor** or **channel selector** would need a new charter.)*

**B15K (closed in-repo):** Read-only **`template_library`** on **`GET /admin/publishing-console`** — **[`docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md`](HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md)**. Schema: **`PublishingConsoleTemplateLibraryFamily`**, **`PublishingConsoleTemplateLibraryEntryStatus`**, **`AdminPublishingConsoleTemplateLibraryEntryRead`**, **`AdminPublishingConsoleTemplateLibraryRead`**; **`AdminPublishingConsoleItemRead.template_library`**. **`supplier_offer_initial`**: **`supplier_offer_showcase`** metadata; **`custom_request_cta`** variant when applicable. **`tour_promotion`**: placeholder/read-only; **`future`** variants only. **`console_preview`** not replaced. **No** Telegram I/O, publish attempts, scheduler, auto-publish, **`prepare_conversion_chain`** execution, Layer A mutation, Mini App/B11 routing changes, migration.

**B15L (closed in-repo):** Read-only **`preview_payload`** on **`GET /admin/publishing-console`** — **[`docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md`](HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md)**. Schema: **`PublishingConsolePreviewPayloadStatus`**, **`PublishingConsolePreviewPayloadSource`**, **`AdminPublishingConsolePreviewPayloadRead`**; **`AdminPublishingConsoleItemRead.preview_payload`**. Supplier-offer rows: **`showcase_preview`** / offer / review-package data; cross-DTO **`publish_readiness_note`** and **`template_library_note`**. Tour rows: **`source=tour_placeholder`**. **No** Telegram I/O, publish attempts, scheduler, auto-publish, **`prepare_conversion_chain`** execution, Layer A mutation, Mini App/B11 routing changes, migration, or provider API calls.

**Only** after explicit product / security / design approval:

| Option | Intent |
|--------|--------|
| **B15E2** | Explicit **action execution** from console or sibling flows (not metadata only). |
| **B15G** | Guarded **auto-publish** — **design only:** **[`docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md)** (**no** runtime in this gate). |
| **B15H** | Read-only **publish readiness** on **review-package** + publishing-console supplier-offer rows — **[`docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md`](HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md)** (**suggest-only**; **no** Telegram I/O). |
| **B15I** | **UX layer** on **`publish_readiness`** (summary, badge, next-action hints, blockers, gate_summary) — **[`docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md`](HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md)** (**read-only**). |
| **B16** / **Admin OPS visibility** | If roadmap priority shifts to broader ops surfaces outside this foundation. |

**Related (design record — not implemented by B15B–F):** **[`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md)** — guarded **`prepare_conversion_chain`** (internal bridge / catalog / execution link **without** Telegram); **B15** read-only foundation unchanged until **B16D2** / **B15E2**.

---

## 8. Recommended next step

1. **Pause B15** and return to the **broader business plan** / next product block **until** a slice above is chartered, **or**
2. Open a **new** gated slice (e.g. template/channel **editor** UX, or other console execution beyond existing **B15E2**) with an explicit charter — **B15F2/B15F3**, **B15K**, and **B15L** read-model metadata are already closed; **B15E2** already covers prepare-chain execution from the publishing console.

---

## 9. Slice index (implementation record)

| Slice | Doc |
|-------|-----|
| B15B | [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md) |
| B15C | [`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md) |
| B15D | [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md) |
| B15E | [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md) |
| B15F | [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md) |
| B15F2/B15F3 | [`docs/HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md`](HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md) — read-only `console_preview` |
| B15K | [`docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md`](HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md) — read-only `template_library` |
| B15L | [`docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md`](HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md) — read-only `preview_payload` |
| B15G | [`docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md`](B15G_GUARDED_AUTO_PUBLISH_DESIGN.md) — design only |
| B15H | [`docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md`](HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md) — read-only suggest-only readiness |
| B15I | [`docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md`](HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md) — compact UX fields on same DTO |
| B15E2 | [`docs/HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md`](HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md) |
