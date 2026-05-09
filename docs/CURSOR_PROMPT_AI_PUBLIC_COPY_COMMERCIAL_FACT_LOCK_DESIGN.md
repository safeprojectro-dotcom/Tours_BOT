# CURSOR_PROMPT_AI_PUBLIC_COPY_COMMERCIAL_FACT_LOCK_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design/contract step.

Do not change code in this step.

---

## Functional block

AI PUBLIC COPY WITH COMMERCIAL FACT LOCK

---

## Business problem

Target business logic:

Supplier raw offer
→ AI prepares marketing/public copy
→ AI flags problems
→ Admin reviews raw facts + AI-prepared copy
→ Admin approves
→ Approved copy can be used for showcase / Mini App text
→ Commercial facts remain from source-of-truth fields

Critical risk:

AI might accidentally or creatively change commercial facts:

- price
- currency
- date/time
- route
- seats/capacity
- sales_mode
- full_bus vs per_seat
- discount/coupon
- included/excluded services
- payment terms
- cancellation terms

If AI changes facts and admin misses it, we can publish a misleading offer and create operational/legal/reputation risk.

Therefore:

AI must be treated as copywriter + validator, not source of commercial truth.

---

## Current checkpoint

Implemented / test-proven:

- Supplier Offer intake exists.
- Deterministic packaging draft exists.
- Admin packaging approval exists.
- Admin moderation approval exists.
- Showcase template exists.
- Admin showcase preview exists.
- Admin offer review-package exists.
- Supplier Offer → central Mini App catalog conversion is test-proven.
- Mini App remains execution truth.
- Layer A remains booking/payment authority.

Current gap:

AI-prepared public copy is not yet safely wired as canonical publish source.

---

## Core principle

AI may improve wording.

AI must not mutate facts.

Source facts must come from structured SupplierOffer/Tour/Layer A fields.

Examples of locked facts:

- title/route/destination facts
- departure_datetime
- return_datetime
- base_price
- currency
- sales_mode
- seats_total
- included_text
- excluded_text
- discount_code
- discount_percent
- discount_amount
- discount_valid_until
- payment_mode
- service_composition
- boarding_places_text
- transport/vehicle fields

AI can produce:

- public_title suggestion
- hook
- marketing summary
- cleaned program wording
- CTA wording
- tone/language improvements
- warnings
- missing field suggestions

AI cannot invent or silently change:

- “25 RON” to “250 RON”
- “transport only” to “transport + guide”
- per_seat to full_bus
- date/time
- coupon value
- availability
- seats remaining
- guarantee status

---

## Goal of this Plan step

Design a safe contract for AI-prepared public copy with commercial fact lock.

Answer:

1. What is the source-of-truth facts model?
2. What should AI output?
3. How do we detect fact drift?
4. How does admin review it?
5. What blocks approval/publish/catalog usage?
6. How does this integrate with existing packaging_draft_json / review-package / showcase preview?
7. What is the first safe implementation slice?

---

## Source docs/code to inspect

Read:

- docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md

Inspect code:

- app/models/supplier.py
- app/models/tour.py
- app/models/enums.py
- app/services/supplier_offer_packaging_service.py
- app/services/supplier_offer_packaging_review_service.py
- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_review_package_service.py
- app/schemas/supplier_admin.py
- app/api/routes/admin.py
- tests around packaging / showcase / review-package

If paths differ, find equivalents.

---

## Questions to answer

### 1. Current packaging behavior

Map current packaging pipeline:

- where packaging_draft_json is created
- what fields it contains
- whether it is AI-generated or deterministic
- what admin approves
- what publish/showcase currently uses
- whether approved packaging currently affects Tour / showcase / Mini App

### 2. Source facts contract

Define a stable source facts snapshot, e.g.

```json
{
  "source_facts_version": "v1",
  "supplier_offer_id": 11,
  "facts": {
    "title": "...",
    "route": "...",
    "departure_datetime": "...",
    "return_datetime": "...",
    "base_price": "25.00",
    "currency": "RON",
    "sales_mode": "per_seat",
    "seats_total": 21,
    "included": ["transport"],
    "excluded": ["bilete de intrare"],
    "discount": {
      "code": "Ura",
      "percent": null,
      "amount": "0.00",
      "valid_until": "..."
    }
  }
}