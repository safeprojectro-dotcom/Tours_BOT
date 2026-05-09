

---

## HANDOFF name

`HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP

## Status

**B12B implemented and documented (finalize pass).** Review-package **`showcase_template_preview`**; **`PATCH …/packaging/showcase-template`**; packaging regenerate preserves admin keys; Telegram read-only B12B block; **`flag_modified`** for JSONB. **Channel publish** and **publish readiness** unchanged.

## Checkpoint

- **B12A:** Template enum, library service, **`showcase_marketing_template_library_v1`** on packaging generate; **`LAST_SEATS_URGENT`** never auto-inferred.
- **B12B:** Ops can **read** preview on **`GET …/review-package`** and **write** optional admin template metadata via **PATCH**; effective preview respects last-seats gate; **no** channel wiring yet (**B13**).

## Files touched by B12B (implementation summary)

| Area | Path |
|------|------|
| Preview + merge preserve + resolve + PATCH helpers | `app/services/showcase_marketing_template_library.py` |
| Review-package aggregation | `app/services/supplier_offer_review_package_service.py` |
| Packaging review service | `app/services/supplier_offer_packaging_review_service.py` |
| Pydantic DTOs | `app/schemas/supplier_admin.py` |
| Admin routes | `app/api/routes/admin.py` |
| Operator workflow | `app/services/supplier_offer_operator_workflow.py` |
| Telegram | `app/bot/handlers/admin_moderation.py`, `app/bot/messages.py` |

## API behavior

### `GET /admin/supplier-offers/{offer_id}/review-package`

- Response includes **`showcase_template_preview`** (read-only).

### `PATCH /admin/supplier-offers/{offer_id}/packaging/showcase-template`

- Body: **`AdminPackagingShowcaseTemplatePatch`**: **`template_id`** (`str \| null`), **`live_seats_remaining`** (`int \| null`).
- Persists into **`packaging_draft_json.showcase_marketing_template_library_v1`**: **`admin_selected_template_id`**, **`admin_selected_at`**, **`admin_live_seats_remaining`** (when last-seats + count).
- **`template_id: null`**: clears admin selection keys from the v1 block.
- **`last_seats_urgent`**: requires **`live_seats_remaining >= 1`** — else **400**.
- **400** when **`packaging_status`** is **`approved_for_publish`** (same idea as telegram draft lock).

### `POST /admin/supplier-offers/{offer_id}/packaging/generate`

- **`merge_showcase_marketing_template_library_v1`** preserves **`admin_selected_*`** / **`admin_live_seats_remaining`** from the row before replacing inferred fields.

## Review-package field shape (`showcase_template_preview`)

- **`inferred_template_id`**, **`effective_template_id`**, **`selected_template_id`** (optional).
- **`selection_overrides_inference`**: boolean.
- **`preview_fact_lines_ro_html`**: list of HTML strings (ops preview for **effective** template).
- **`template_choices`**: `{ template_id, requires_verified_live_seats }[]`.
- **`notes`**: strings when stored selection is invalid (e.g. last seats without verified seats — effective falls back).
- **`channel_publish_unchanged`**: always **`true`**.

## Telegram behavior

- Private admin **offer detail** appends a **compact read-only** block (EN/RO) when **`review-package`** returns a real **`showcase_template_preview`** DTO (inferred / effective / optional notes; **channel unchanged** disclaimer).
- **No** inline “pick template” callbacks in B12B (optional **B12C**).

## Tests run (representative)

```text
pytest tests/unit/test_showcase_marketing_template_library.py \
  tests/unit/test_supplier_offer_b5_packaging_review.py \
  tests/unit/test_supplier_offer_b4_packaging.py \
  tests/unit/test_supplier_offer_review_package.py -q
```

## Non-goals (preserved)

- No auto-publish; no publish readiness changes; no **`build_showcase_publication`** / live channel HTML change in B12B.
- No Mini App, booking, payment, orders, migrations.
- No fake urgency / discount / last seats; last seats only with verified count on PATCH + stored **`admin_live_seats_remaining`**.

## Next likely steps

1. **B12C (optional)** — Telegram admin **interactive** template selection UI if ops need in-chat PATCH triggers.
2. **B13** — Channel adapter: wire **effective** template into **`build_showcase_publication`** with regression tests.
3. **Production content QA** — real offers, ops smoke, tone/locale.

```

---

## Notes (wrapper)

Portable payload for the next chat or PR. Implementation prompt + completion: [`docs/CURSOR_PROMPT_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT.md`](CURSOR_PROMPT_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT.md). Docs finalize prompt: [`docs/CURSOR_PROMPT_B12B_DOCS_FINALIZE.md`](CURSOR_PROMPT_B12B_DOCS_FINALIZE.md). Canonical spec: [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md).
