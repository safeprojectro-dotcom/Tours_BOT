You are continuing Tours_BOT after B1.

Goal:
B2 — Supplier Offer Content/Data Upgrade.

This is the first implementation slice for the BUSINESS supplier-offer-to-tour line.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md

Scope:
Upgrade supplier_offer persistence/contracts so B1 intake and future packaging can be stored.

Allowed:
- Alembic migration
- ORM model fields
- Pydantic schemas
- supplier-admin offer create/update/read support for new fields
- admin read visibility for new fields
- focused tests

Add fields for supplier_offers or supporting tables as appropriate:
- cover_media_reference
- media_references / photo references if current style allows JSON
- program_text
- included_text
- excluded_text
- short_hook
- marketing_summary
- discount_code
- discount_percent
- discount_amount
- discount_valid_until
- recurrence_type
- recurrence_rule
- valid_from
- valid_until
- supplier_admin_notes
- admin_internal_notes
- packaging_status if safe and aligned with B1
- missing_fields_json / quality_warnings_json if safe and aligned with B1

Rules:
- no AI generation implementation yet
- no Tour creation
- no Mini App catalog changes
- no booking/order/payment changes
- no publishing behavior changes
- no Telegram post template changes
- no supplier messaging
- no bridge to Layer A yet
- preserve existing supplier offer publication behavior

Validation:
- prices/discounts must be non-negative when provided
- discount_percent must be within a sane range
- recurrence fields are stored but not executed
- media references are stored only, no upload pipeline yet
- packaging fields are draft/admin data only

Tests:
- migration/model persistence
- supplier-admin create/update/read with new fields
- admin read includes new fields
- existing supplier offer tests still pass
- no publish behavior regression

Before coding:
1. summarize B1 requirements
2. list expected files to change
3. explain why this does not affect Layer A booking/payment or Mini App catalog

After coding:
1. files changed
2. migration name
3. fields added
4. tests run
5. confirm no Tour/booking/payment/Mini App/publish behavior changed
6. next safe step: B3 Supplier Dialog Upgrade