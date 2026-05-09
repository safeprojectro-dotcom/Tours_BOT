# CURSOR_PROMPT_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT

You are working on Tours_BOT.

Implement B12B: Admin preview/select marketing template for Supplier Offer showcase packaging.

This is a larger functional block, but must remain safe:

- no auto-publish;
- no publish readiness changes;
- no booking/payment/orders;
- no Mini App;
- no migrations unless absolutely required — prefer JSON metadata only.

## Current checkpoint

B12A is closed and pushed:

- `ShowcaseMarketingTemplateId` enum added with 9 template ids.
- `app/services/showcase_marketing_template_library.py` added.
- Packaging generation stores `showcase_marketing_template_library_v1` metadata in `packaging_draft_json`.
- `LAST_SEATS_URGENT` is never auto-inferred.
- Early-bird line only from real discount fields + deadline.
- Public publish output is unchanged.
- No publish readiness changes.
- No Mini App / booking / orders.
- No migrations.

## Goal

Allow admin/operator to preview and optionally select a marketing template for Supplier Offer showcase packaging.

The goal is to make B12A useful operationally without changing live publish semantics.

## Core rules

Preserve:

- Template structures copy; it does not invent facts.
- Admin remains final approver.
- Publish remains separate.
- Publish readiness gates remain unchanged.
- No fake urgency.
- No fake discount.
- No fake last seats.
- Availability only from verified live data.
- Discounts only from real fields.
- Published offer != bookable Tour.
- Layer A remains booking/payment/order truth.

## Documents to inspect

Inspect:

- `docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`
- `docs/HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/ADMIN_OPERATOR_WORKFLOW.md`
- `docs/CHAT_HANDOFF.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

## Code to inspect

Inspect current implementation:

- `app/models/enums.py`
- `app/services/showcase_marketing_template_library.py`
- `app/services/supplier_offer_packaging_service.py`
- `app/services/supplier_offer_review_package_service.py`
- `app/bot/handlers/admin_moderation.py`
- `app/bot/messages.py`
- admin API routes for supplier offer review/package/packaging
- tests:
  - `tests/unit/test_showcase_marketing_template_library.py`
  - `tests/unit/test_supplier_offer_b4_packaging.py`
  - `tests/unit/test_supplier_offer_review_package.py`
  - `tests/unit/test_supplier_offer_b5_packaging_review.py`
  - `tests/unit/test_telegram_admin_moderation_y281.py` (regression only if Telegram append changes)

## Desired behavior

### 1. Review-package exposes template library preview

Add read-only B12B preview info to review-package.

Field: **`showcase_template_preview`** (`AdminSupplierOfferShowcaseTemplatePreviewRead`):

- **`inferred_template_id`** — from `infer_showcase_marketing_template(offer)`.
- **`effective_template_id`** — admin selection when valid; else inferred.
- **`selected_template_id`** — raw persisted admin id when set.
- **`selection_overrides_inference`** — `effective != inferred`.
- **`preview_fact_lines_ro_html`** — ops-only HTML lines for the effective template (same family as `build_preview_fact_lines_for_template`; not channel publish).
- **`template_choices`** — all enum ids with **`requires_verified_live_seats`** for `last_seats_urgent`.
- **`notes`** — e.g. invalid last-seats selection without verified seat count (effective falls back to inferred).
- **`channel_publish_unchanged`** — always `true` for this slice.

### 2. Admin PATCH selection (metadata only)

- **`PATCH /admin/supplier-offers/{offer_id}/packaging/showcase-template`**
- Body: **`AdminPackagingShowcaseTemplatePatch`** — **`template_id`** (`str | null`), **`live_seats_remaining`** (`int | null`).
- Writes into **`packaging_draft_json.showcase_marketing_template_library_v1`**: **`admin_selected_template_id`**, **`admin_selected_at`**, and when applicable **`admin_live_seats_remaining`**.
- **`template_id: null`** clears admin selection keys (and live seats key) from the library block.
- **`last_seats_urgent`** requires **`live_seats_remaining >= 1`** on PATCH.
- Same lock as telegram draft: **no PATCH when `packaging_status` is `approved_for_publish`**.
- After nested JSONB mutation, callers must persist reliably (e.g. **`flag_modified(row, "packaging_draft_json")`** before flush).

### 3. Regenerate packaging preserves admin keys

On **`POST …/packaging/generate`**, **`merge_showcase_marketing_template_library_v1`** must copy **`admin_selected_*`** / **`admin_live_seats_remaining`** from the existing row into the new merged block.

### 4. Operator workflow + Telegram (read-only hints)

- **`operator_workflow.actions`**: include **`patch_showcase_marketing_template`** (HTTP **PATCH**, endpoint hint).
- Telegram admin offer detail: optional short read-only block summarizing inferred/effective/selection when review-package returns a real preview DTO.

### 5. Unchanged

- **`build_showcase_publication`** / **`POST …/publish`** / **`GET …/showcase-preview`** channel HTML unchanged.
- No publish readiness field changes.
- No Mini App / booking / payment / orders.

---

## Completion (B12B — implemented)

**Status:** Done. Docs finalize: `docs/CURSOR_PROMPT_B12B_DOCS_FINALIZE.md`.

### Implemented behavior

- **`GET /admin/supplier-offers/{id}/review-package`** includes **`showcase_template_preview`** with inferred / effective / optional admin selection, RO HTML fact lines, **`template_choices`**, **`notes`** for invalid selection, **`channel_publish_unchanged: true`**.
- **`PATCH /admin/supplier-offers/{id}/packaging/showcase-template`** with **`AdminPackagingShowcaseTemplatePatch`** updates **`packaging_draft_json.showcase_marketing_template_library_v1`**; **`template_id: null`** clears admin keys; **`last_seats_urgent`** requires **`live_seats_remaining >= 1`**; blocked when packaging is **`approved_for_publish`**.
- Packaging regenerate preserves admin template / live seats via merge; **`flag_modified(row, "packaging_draft_json")`** after nested JSONB updates.
- Operator workflow exposes **`patch_showcase_marketing_template`** (**PATCH**). Telegram detail appends a compact B12B read-only block (EN/RO).

### Tests (verified with implementation)

- `pytest tests/unit/test_showcase_marketing_template_library.py tests/unit/test_supplier_offer_b5_packaging_review.py tests/unit/test_supplier_offer_b4_packaging.py tests/unit/test_supplier_offer_review_package.py` (and related operator-workflow smoke as needed).

### Safety confirmations

- Channel publish output and **`build_showcase_publication`** unchanged; no publish readiness changes; no Mini App / booking / payment / orders; no migrations; selection is packaging JSON metadata only; selecting a template does not publish and does not approve packaging.
