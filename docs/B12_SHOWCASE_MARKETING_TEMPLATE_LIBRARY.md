# B12 — Showcase marketing template library

**Project:** Tours_BOT. **Scope:** supplier-offer **Telegram showcase** copy — template **classification** and **safe** metadata (B12A foundation).

**Related:** [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) · [`docs/AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md`](AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md) · [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (B12/B13 + B12A) · [`docs/HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP.md`](HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP.md).

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

## What the publish path does **not** use yet

- **`build_showcase_publication`** does **not** read `showcase_marketing_template_library_v1`.

- **`POST …/publish`** and **`GET …/showcase-preview`** still render the **same** Romanian branded template as before B12A.

- **`build_preview_fact_lines_for_template`** is **ops/tooling only** (tests + future admin preview); not wired to Telegram send.

---

## Non-goals (B12A)

- No auto-publish.

- No change to publish readiness, C2B8A cover gates, or **`operator_workflow`** semantics.

- No Mini App, booking, payment, or order changes.

- No migrations.

- No AI or external API calls in this slice.

- No hidden Tour / catalog / execution-link / bridge mutations.

---

## Next likely steps

1. **B12B** — Admin **preview** / **select** template (persist explicit choice, optional override of inferred id).

2. **B13** — **Channel adapter** design: map selected template id to **`build_showcase_publication`** (or sibling builders) with full regression tests; keep fact-lock and disable_web_page_preview behavior as today unless product specifies otherwise.

3. **Production content QA** — operator review of real offers (Mode A/B smoke, copy tone, bilingual needs).

---

## Code map (B12A)

| Piece | Location |
|-------|----------|
| Enum | `app/models/enums.py` — `ShowcaseMarketingTemplateId` |
| Library | `app/services/showcase_marketing_template_library.py` |
| Fact lines export | `app/services/supplier_offer_showcase_message.py` — `build_showcase_fact_lines_html` |
| Packaging merge | `app/services/supplier_offer_packaging_service.py` — after draft merge |
| Tests | `tests/unit/test_showcase_marketing_template_library.py`, `tests/unit/test_supplier_offer_b4_packaging.py` |
