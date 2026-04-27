You are continuing Tours_BOT after B9.

Goal:
B10 — Supplier Offer → Tour Bridge Implementation.

Read:
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md

Current state:
- Supplier offer can be packaged, truth-checked, approved for publish, branded-previewed, media-reviewed, and card-render-plan-ready.
- Supplier offer still does not become a Tour.
- B9 design says bridge must be explicit admin action.
- No silent ORM trigger.
- No AI-created Tour.
- No supplier bypass.

Goal:
Implement explicit admin bridge:
approved supplier offer → create/link Tour → bridge record.

Scope:
- Add bridge persistence.
- Add admin POST endpoint.
- Add admin read/status endpoint.
- Map SupplierOffer into Tour safely.
- Idempotent behavior.
- Tests.

Preferred data model:
Add table:
supplier_offer_tour_bridges

Fields:
- id
- supplier_offer_id
- tour_id
- status: active / superseded / cancelled
- bridge_kind: created_new_tour / linked_existing_tour
- created_by
- created_at
- updated_at
- source_packaging_status
- source_lifecycle_status
- packaging_snapshot_json
- notes

Rules:
1. Preconditions:
- SupplierOffer.packaging_status must be approved_for_publish.
- SupplierOffer.lifecycle_status must NOT be rejected.
- Required fields:
  - title
  - description or marketing_summary
  - departure_datetime
  - return_datetime
  - base_price
  - currency
  - seats_total
  - sales_mode
  - program_text
  - included_text
  - excluded_text
- If missing required fields: 422 with clear error list.
- quality warnings may exist, but B5 approval means admin accepted them.

2. Idempotency:
- If active bridge already exists for offer, return existing bridge + Tour.
- Do not create duplicate Tour on repeated call.

3. Tour creation:
- Create Tour from SupplierOffer.
- New Tour status should be draft by default.
- Do NOT auto-open for sale.
- Do NOT publish.
- Do NOT create orders/payments/reservations.
- Do NOT mutate Mini App directly; catalog visibility follows existing Tour.status policy.

4. Mapping:
- title → Tour title_default/code source
- description/marketing_summary → short/full description fields depending current model
- departure_datetime / return_datetime → Tour
- base_price / currency → Tour
- seats_total → seats_total
- seats_available:
  - per_seat: seats_total
  - full_bus: preserve safe policy; do not allow accidental per-seat self-service
- sales_mode → Tour.sales_mode
- cover_media_reference if Tour has such field; otherwise leave for later
- create default translation if current architecture requires tour_translations

5. Full bus safety:
- Tour.sales_mode must be full_bus.
- Do not create per-seat availability semantics by accident.
- If existing policy requires assisted closure, keep it as assisted.
- No direct whole-bus checkout unless already supported by existing policy.

6. API:
- POST /admin/supplier-offers/{offer_id}/tour-bridge
  Body optional:
  {
    "created_by": "...",
    "notes": "...",
    "existing_tour_id": optional
  }
- GET /admin/supplier-offers/{offer_id}/tour-bridge

7. Response:
Return:
- supplier_offer_id
- tour_id
- bridge_status
- bridge_kind
- tour_status
- created_at
- idempotent_replay bool
- warnings / notes

8. Tests:
- bridge create from approved offer creates Tour + bridge
- repeated POST returns existing bridge, no duplicate Tour
- non-approved packaging_status fails
- missing required fields returns 422-style error
- rejected offer lifecycle fails
- full_bus creates Tour.sales_mode full_bus
- created Tour status is draft, not open_for_sale
- no published_at/showcase_message_id changes
- no Order/Payment created
- GET bridge returns active bridge

Do NOT:
- send Telegram
- publish to channel
- create payment/order/reservation
- alter existing Mini App UI
- call AI
- download media
- implement recurring offers
- implement B7.3 media storage

Before coding:
1. summarize B9 design state
2. list files expected to change
3. explain why B10 is explicit bridge and safe
4. state exact non-goals

After coding:
1. files changed
2. migration name
3. API endpoints
4. mapping implemented
5. idempotency behavior
6. tests run
7. confirm no Telegram/publish/payment/order/reservation/AI/media download changes
8. next safe step: B10.1 smoke/docs sync or B8 recurring offers / B7.3 media prep