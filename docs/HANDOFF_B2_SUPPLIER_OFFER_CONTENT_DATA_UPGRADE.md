# B2 — Supplier offer content/data upgrade — completed

**Scope:** **First implementation slice** for the BUSINESS **supplier offer → tour** line: **persistence and API contracts** only. **Migration:** `20260526_24_supplier_offer_b2_content_data`.

## Source of truth

- [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md)
- [`docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md)
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)
- [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md)

## What B2 added

Supplier offers can store **richer content** needed for future **packaging** and **admin** review:

- **Media / photo references** (e.g. `cover_media_reference`, `media_references` JSONB)
- **Program** (existing `program_text` + structured adjacent fields as designed)
- **Included / excluded** text
- **Marketing** hook and summary
- **Discounts / promos** (code, percent, amount, valid-until) with validation
- **Recurrence** metadata (stored; **not** executed in product logic in B2)
- **Validity** window (`valid_from` / `valid_until`)
- **Admin** / **supplier** notes (admin-only + supplier-facing split where applicable)
- **`packaging_status`**, **`missing_fields_json`**, **`quality_warnings_json`** (admin read model) where implemented

**API:** Supplier **create/update/read** carry B2 **supplier** fields; **admin** list/detail use **`AdminSupplierOfferRead`** for full columns including admin-only metadata.

## Important (non-goals, preserved)

- **B2** is **data / storage** (and read surfaces) **only**
- **No** AI generation
- **No** `Tour` creation
- **No** Mini App catalog / visibility changes
- **No** booking / payment changes
- **No** **publish** / **showcase** **behavior** **change** (showcase build path unchanged)
- **No** supplier **messaging** changes

## Next safe step

**B3 — Supplier dialog upgrade** (Telegram intake FSM/UX: stepwise flow, optional wiring to B2 fields per [`SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md) **§3**).
