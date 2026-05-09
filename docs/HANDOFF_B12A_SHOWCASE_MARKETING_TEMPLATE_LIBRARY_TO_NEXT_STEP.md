
---

## HANDOFF name

`HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY_TO_NEXT_STEP

## Status

**B12A implemented.** Foundation only: template enum, deterministic inference, packaging JSON metadata, ops-only preview line builders. **`build_showcase_publication`** / channel **`POST …/publish`** unchanged.

## Project

Tours_BOT — Supplier Offer showcase marketing templates.

## Step

B12A — Showcase Marketing Copy Template Library foundation.

## Purpose

Standardize **safe** public showcase copy planning (structure + metadata) without inventing facts, weakening publish gates, or changing live channel output.

## Core rules (preserved)

- No fake urgency.
- No fake discount lines without real `discount_*` + (for early-bird inference) `discount_valid_until`.
- No fake “last seats” — **`LAST_SEATS_URGENT`** is **never** auto-inferred; preview helper adds a seats line **only** when `live_seats_remaining` is passed explicitly.
- Availability only from verified live data (future wiring; not in this slice).
- Templates structure / classify; they do not invent facts.
- Admin remains final approver.
- Publish / review-package gates unchanged.

## Delivered (code)

- **`ShowcaseMarketingTemplateId`** — `app/models/enums.py` — all nine ids:  
  `PER_SEAT_STANDARD`, `FULL_BUS_PRIVATE_GROUP`, `CUSTOM_REQUEST_CTA`, `EARLY_BIRD_DISCOUNT`, `LAST_SEATS_URGENT`, `SUPPLIER_SERVICE_PROMO`, `SHORT_ANNOUNCEMENT`, `IMAGE_ONLY_TEASER`, `BRAND_AWARENESS_POST`.
- **`app/services/showcase_marketing_template_library.py`** — `infer_showcase_marketing_template`, `build_showcase_marketing_template_library_v1`, `merge_showcase_marketing_template_library_v1`, `build_preview_fact_lines_for_template`, `early_bird_grounded`, `last_seats_urgent_allowed`.
- **`app/services/supplier_offer_showcase_message.py`** — public **`build_showcase_fact_lines_html`** (same body as channel facts block; for reuse only).
- **`app/services/supplier_offer_packaging_service.py`** — on **`generate_and_persist`**, merges **`packaging_draft_json.showcase_marketing_template_library_v1`** (no migration).

## Inference summary

- **FULL_BUS** (+ early-bird fields) → `FULL_BUS_PRIVATE_GROUP` or `EARLY_BIRD_DISCOUNT`.
- **PER_SEAT**: early-bird → `ASSISTED_CLOSURE` → non–`TRANSPORT_ONLY` composition → `PER_SEAT_STANDARD`.
- **`LAST_SEATS_URGENT` / `SHORT_ANNOUNCEMENT` / `IMAGE_ONLY_TEASER` / `BRAND_AWARENESS_POST`** — documented in `blocked_auto_inference`; not auto-selected from offer row alone.

## Tests

- **`tests/unit/test_showcase_marketing_template_library.py`** — inference, merge block, early-bird supplement, preview truncation, last-seats gate.
- **`tests/unit/test_supplier_offer_b4_packaging.py`** — asserts **`showcase_marketing_template_library_v1`** after packaging generate.

## Non-goals (unchanged)

- No auto-publish; no publish readiness change; no booking/payment/order changes; no Mini App changes; no media pipeline continuation; no AI/external calls; no hidden Tour/catalog/execution mutations.

## Docs

- **`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`** — canonical B12 / B12A spec (templates, inference, storage, non-goals, next steps).
- **`docs/CHAT_HANDOFF.md`** — B12A bullet.
- **`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`** — B12A metadata note.

## Next likely steps

1. **B12B** — Admin preview / select template (explicit override, persisted choice).
2. **B13** — Channel adapter design: wire chosen template to **`build_showcase_publication`** (or layered builders) with tests; preserve fact-lock and current send semantics unless product changes scope.
3. **Production content QA** — real offers, ops smoke, tone/locale review.
```

---

## Notes (wrapper)

Portable payload for the next chat or PR. Prompt: [`docs/CURSOR_PROMPT_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](CURSOR_PROMPT_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md). Canonical spec: [`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`](B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md).
