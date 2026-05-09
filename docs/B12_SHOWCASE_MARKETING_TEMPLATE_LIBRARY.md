# B12 — Showcase marketing template library

**Project:** Tours_BOT. **Scope:** supplier-offer **Telegram showcase** copy — template **classification** and **safe** metadata (B12A foundation).

**Related:** [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) · [`docs/AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md`](AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md) · [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (B12/B13 + B12A–C) · [`docs/HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP.md`](HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP.md) · [`docs/HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP.md`](HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP.md) · [`docs/HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP.md`](HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP.md).

---

## Implemented template ids (`ShowcaseMarketingTemplateId`)

Defined in `app/models/enums.py`:

| Id | Role (summary) |
|----|------------------|
| `PER_SEAT_STANDARD` | Default per-seat catalog-style positioning. |
| `FULL_BUS_PRIVATE_GROUP` | Whole-vehicle / group package positioning. |
| `CUSTOM_REQUEST_CTA` | Assisted / closure-oriented commercial path (`ASSISTED_CLOSURE`). |
| `EARLY_BIRD_DISCOUNT` | When **real** discount value **and** `discount_valid_until` are both set. |
| `LAST_SEATS_URGENT` | **Never** auto-inferred; ops preview only with explicit verified seat count. |
| `SUPPLIER_SERVICE_PROMO` | Bundled services beyond transport-only (`service_composition` ≠ `TRANSPORT_ONLY`). |
| `SHORT_ANNOUNCEMENT` | Explicit / future admin choice; preview helper truncates facts. |
| `IMAGE_ONLY_TEASER` | Explicit / future admin choice; preview helper = minimal lines. |
| `BRAND_AWARENESS_POST` | Explicit / future admin choice; preview helper adds soft brand line. |

---

## MVP inference rules (deterministic, `SupplierOffer` row only)

Implemented in `app/services/showcase_marketing_template_library.py` — **`infer_showcase_marketing_template`**:

1. **If `sales_mode == FULL_BUS`:**  
   - If **early-bird grounded** → `EARLY_BIRD_DISCOUNT`.  
   - Else → `FULL_BUS_PRIVATE_GROUP`.

2. **If `sales_mode == PER_SEAT`:**  
   - If **early-bird grounded** → `EARLY_BIRD_DISCOUNT`.  
   - Else if `payment_mode == ASSISTED_CLOSURE` → `CUSTOM_REQUEST_CTA`.  
   - Else if `service_composition != TRANSPORT_ONLY` → `SUPPLIER_SERVICE_PROMO`.  
   - Else → `PER_SEAT_STANDARD`.

**Early-bird grounded** means: (`discount_percent > 0` or `discount_amount > 0`) **and** `discount_valid_until` is set. No orphan promo deadlines.

Priority is fixed: early bird beats assisted closure and service promo on per-seat offers.

---

## Blocked / explicit-only templates

These ids exist in the library but are **not** chosen by `infer_showcase_marketing_template` from the offer row alone:

- **`LAST_SEATS_URGENT`** — requires **verified** live seat remaining count; documented under `blocked_auto_inference` in `showcase_marketing_template_library_v1`. Preview helper **`build_preview_fact_lines_for_template`** may add a factual seats line **only** when `live_seats_remaining` is passed and `> 0`.

- **`SHORT_ANNOUNCEMENT`**, **`IMAGE_ONLY_TEASER`**, **`BRAND_AWARENESS_POST`** — reserved for **admin explicit choice** or future wiring; listed in `blocked_auto_inference` with rationale.

---

## Fact-lock and honesty rules

- **Templates structure / classify** marketing posture; they **do not invent** price, dates, program, availability, or execution truth.

- **No fake urgency** — no “last seats” / hurry copy from inference; no live inventory in this slice.

- **Discounts** — supplemental RO line (`safe_supplemental_lines_ro`) for early bird uses **only** `discount_percent`, `discount_amount`, `discount_code`, `discount_valid_until`, `currency` as present on the row.

- **Channel showcase HTML** remains the single deterministic builder **`build_showcase_publication`** (`app/services/supplier_offer_showcase_message.py`). Template metadata is **advisory** for packaging / review-package until a future step selects it for publish.

- **`AI_PUBLIC_COPY_FACT_LOCK_CONTRACT`** and packaging truth warnings (`assess_packaging_truth_warnings`, etc.) remain authoritative for AI / draft gaps; B12A does not weaken them.

- **Admin** remains final publisher; **publish readiness** and **`operator_workflow`** gates are **unchanged**.

---

## Metadata storage

On **`POST /admin/supplier-offers/{offer_id}/packaging/generate`** (and the same path when deterministic draft is persisted), `SupplierOfferPackagingService.generate_and_persist` merges into **`packaging_draft_json`** (JSONB on `supplier_offers` — **no new migration**):

**Key:** `showcase_marketing_template_library_v1`

**Shape (conceptual):**

- `schema_version` — `1`.

- `inferred_template_id` — string value of `ShowcaseMarketingTemplateId`.

- `selection_rules` — trace strings for ops/debug (e.g. `sales_mode=per_seat`, `early_bird_fields_complete`, `resolved=…`).

- `blocked_auto_inference` — map of template id → short reason (e.g. `LAST_SEATS_URGENT` → `requires_verified_live_seats_remaining`).

- `safe_supplemental_lines_ro` — list of plain-text RO lines (today: early-bird factual line when applicable).

This block is **read-only** for consumers of **`GET …/review-package`**: it reflects post-generate state; it does not by itself change **`can_publish_now`** or moderation.

---

## B12B (implemented) — admin preview + optional template selection

**Purpose:** Make the library operationally usable for admin/ops: **read** a structured preview on **`GET …/review-package`**, and **optionally persist** an explicit template choice as **JSON metadata only** (no channel publish change).

### Review-package preview

- Field **`showcase_template_preview`** (`AdminSupplierOfferShowcaseTemplatePreviewRead`) on **`GET /admin/supplier-offers/{offer_id}/review-package`**.
- Includes: **`inferred_template_id`**, **`effective_template_id`** (valid admin selection wins; else inferred), **`selected_template_id`** (stored admin id if any), **`selection_overrides_inference`**, **`preview_fact_lines_ro_html`** (ops-oriented HTML for the **effective** template — factual; same “no fake last seats” rules as preview helpers), **`template_choices`** (all ids + **`requires_verified_live_seats`** for **`last_seats_urgent`**), **`notes`** when the stored selection is invalid (e.g. last seats without verified seat count — effective falls back to inferred), and **`channel_publish_unchanged: true`**.

### PATCH selection endpoint

- **`PATCH /admin/supplier-offers/{offer_id}/packaging/showcase-template`**
- Body: **`AdminPackagingShowcaseTemplatePatch`**: **`template_id`** (`string | null`), **`live_seats_remaining`** (`integer | null`).
- Writes under **`packaging_draft_json.showcase_marketing_template_library_v1`**:
  - **`admin_selected_template_id`**, **`admin_selected_at`** (ISO timestamp);
  - **`admin_live_seats_remaining`** when **`template_id`** is **`last_seats_urgent`** and a seat count is supplied.
- **`template_id: null`**: clears **`admin_selected_template_id`**, **`admin_selected_at`**, **`admin_live_seats_remaining`** from the v1 block (does not remove the whole block).

### Template selection rules (B12B)

- **Inference** unchanged from B12A (`infer_showcase_marketing_template`).
- **Effective template for preview:** if admin selected id is valid and satisfies **last-seats gate** (`verified` **`admin_live_seats_remaining`** > 0 when template is **`last_seats_urgent`**), use selection; else use inferred and surface reasons in **`notes`**.
- **PATCH validation:** **`last_seats_urgent`** requires **`live_seats_remaining >= 1`** on the request body.
- **Approved packaging lock:** PATCH is **rejected** when **`packaging_status`** is **`approved_for_publish`** (same class of guard as editing **`telegram_post_draft`** after approval).
- **Regenerate packaging:** **`merge_showcase_marketing_template_library_v1`** preserves admin keys from the existing row when refreshing inferred fields.
- **JSONB persistence:** after mutating nested keys, **`flag_modified(row, "packaging_draft_json")`** ensures the ORM persists the update.

### Telegram (read-only in B12B)

- Private admin offer detail may still append a **short B12B summary** when **`showcase_template_preview`** exists. **B12B** did not add template callbacks; **B12C** adds the interactive picker (below).

### Publish path (still unchanged in B12B / B12C)

- **`build_showcase_publication`**, **`GET …/showcase-preview`**, and **`POST …/publish`** do **not** read admin template selection yet. **`B13`** may wire **effective** template into the channel builder.

---

## B12C (implemented) — Telegram admin template selection UI

**Purpose:** Let operators pick or clear the showcase marketing template from **Telegram** admin workflow, using the **same** persistence path as B12B (**`SupplierOfferPackagingReviewService.patch_showcase_marketing_template`** + approved-packaging lock + **`flag_modified`** on JSONB).

### Placement and gating

- **Template** / **Șablon** appears on the private admin **offer detail** when **`operator_workflow.patch_showcase_marketing_template`** is **enabled** (same action as HTTP PATCH).
- **Order:** after **Approve text** / **Aprobă text** (`approve_packaging_for_publish`), **before** bridge / publish workflow actions.

### Picker content (from review-package)

- **Inferred** template, **effective** template, **selected** template or none.
- **`notes`** from review-package when the stored selection is invalid or blocked.
- **Blocked / one-tap** messaging when **`LAST_SEATS_URGENT`** (or any choice with **`requires_verified_live_seats`**) cannot be applied without a verified seat count — **no** fake last-seats copy from inference; inventory remains explicit.

### Safe direct apply

- Inline buttons apply **only** templates that are **allowed for one-tap apply** (not seat-gated per **`template_choices`**).
- Handler **re-reads** **`GET …/review-package`**, checks workflow action still enabled, and **`_template_id_allowed_for_telegram_direct_apply`** before calling **`patch_showcase_marketing_template`**.

### Last seats (`LAST_SEATS_URGENT`)

- Dedicated callback opens FSM **`AdminModerationState.awaiting_showcase_template_last_seats`**.
- Operator must send a **positive integer**; then PATCH includes **`last_seats_urgent`** and **`live_seats_remaining`** (same validation as B12B).
- Back / cancel returns to a **fresh** offer detail.

### Clear selection

- **Clear** uses **`template_id: null`** via the same service (clears admin selection / seat override fields per B12B rules).

### Honesty / non-goals (B12C)

- **No** publish output or **publish readiness** changes — channel HTML and gates unchanged.
- **No** auto-publish, packaging **approval**, lifecycle or **media_review** changes beyond **selected template metadata** in packaging JSON.
- **No** Mini App, booking, payment, orders, or migrations.
- **No fake urgency, discount, or availability** — templates **classify** posture; inference never invents last seats; early bird and discounts stay tied to real **`SupplierOffer`** fields and B12A/B12B rules.

---

## What the publish path does **not** use yet

- **`build_showcase_publication`** does **not** read `showcase_marketing_template_library_v1` (including **B12B** **`admin_selected_*`** fields).

- **`POST …/publish`** and **`GET …/showcase-preview`** still render the **same** Romanian branded template as before B12A.

- **`build_preview_fact_lines_for_template`** (and review-package **`preview_fact_lines_ro_html`**) are **ops/tooling only**; not wired to Telegram channel send.

---

## Non-goals (B12A)

- No auto-publish.

- No change to publish readiness, C2B8A cover gates, or **`operator_workflow`** **publish** / **bridge** / **catalog** gate semantics (B12B adds an optional **metadata** PATCH hint action only).

- No Mini App, booking, payment, or order changes.

- No migrations.

- No AI or external API calls in this slice.

- No hidden Tour / catalog / execution-link / bridge mutations.

---

## Next likely steps

1. **B13** — **Channel adapter** design: map selected / effective template id to **`build_showcase_publication`** (or sibling builders) with full regression tests; keep fact-lock and disable_web_page_preview behavior as today unless product specifies otherwise.

2. **Production content QA** — operator review of real offers (Mode A/B smoke, copy tone, bilingual needs).

3. **Optional** — Template picker / library copy polish; extra locales beyond EN/RO for B12C strings if needed. Handoff: **[`HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP.md`](HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP.md)**.

---

## Code map (B12A + B12B + B12C)

| Piece | Location |
|-------|----------|
| Enum | `app/models/enums.py` — `ShowcaseMarketingTemplateId` |
| Library | `app/services/showcase_marketing_template_library.py` — inference, v1 block, merge (preserve admin keys), preview payload, PATCH helpers |
| Fact lines export | `app/services/supplier_offer_showcase_message.py` — `build_showcase_fact_lines_html` |
| Packaging merge | `app/services/supplier_offer_packaging_service.py` — after draft merge |
| Review-package preview | `app/services/supplier_offer_review_package_service.py` — `showcase_template_preview` |
| Packaging PATCH | `app/services/supplier_offer_packaging_review_service.py` — `patch_showcase_marketing_template` + `flag_modified` |
| Admin DTOs / body | `app/schemas/supplier_admin.py` |
| HTTP | `app/api/routes/admin.py` — `PATCH …/packaging/showcase-template` |
| Operator workflow | `app/services/supplier_offer_operator_workflow.py` — `patch_showcase_marketing_template` |
| Telegram B12B summary + **B12C picker** | `app/bot/handlers/admin_moderation.py`, `app/bot/messages.py`; B12C callbacks in `app/bot/constants.py`; FSM `awaiting_showcase_template_last_seats` in `app/bot/state.py` |
| Tests | `tests/unit/test_showcase_marketing_template_library.py`, `tests/unit/test_supplier_offer_b4_packaging.py`, `tests/unit/test_supplier_offer_review_package.py`, `tests/unit/test_supplier_offer_b5_packaging_review.py`; B12C: `tests/unit/test_operator_workflow_b12c_specs.py`, `test_operator_workflow_c2b3_keyboard.py`, `test_telegram_admin_moderation_y281.py` |
