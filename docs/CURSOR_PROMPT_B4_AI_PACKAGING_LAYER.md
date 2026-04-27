You are continuing Tours_BOT after B3.1.

Goal:
B4 — AI Packaging Layer.

Implement AI-assisted packaging draft generation for supplier offers.

Current state:
- B1 design exists
- B2 supplier offer content/data fields exist
- B3 supplier dialog collects structured facts
- B3.1 supplier can upload one Telegram cover photo
- supplier_offer can be ready_for_moderation

Important:
AI is draft-only.
Admin approval remains mandatory.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md

Scope:
Create service-layer AI packaging draft foundation.

Allowed:
- packaging service
- packaging prompt builder
- deterministic fallback draft generator if AI client is not configured
- admin endpoint to generate packaging draft
- store generated draft fields into supplier_offer packaging fields / JSON fields where already available
- update packaging_status
- admin read returns packaging fields
- tests with fake AI client / deterministic fallback

AI output should include:
- short_hook
- marketing_summary
- Telegram post draft
- brief_program
- Mini App short_description
- Mini App full_description
- normalized program_text
- included_text
- excluded_text
- CTA variants
- image/card prompt or layout data
- missing_fields_json
- quality_warnings_json

Guardrails:
- AI must not invent dates/prices/seats
- if required facts are missing, produce warnings instead of inventing
- AI must not publish
- AI must not create Tour
- AI must not create booking/order/payment
- AI must not modify Layer A
- AI must not send Telegram messages
- AI must not change supplier offer lifecycle to published
- AI may update packaging_status only

Suggested status behavior:
- before generation: packaging_pending or none
- after successful draft: packaging_generated or needs_admin_review
- if missing critical fields: needs_admin_review with warnings

Admin route suggestion:
POST /admin/supplier-offers/{offer_id}/packaging/generate

Must require ADMIN_API_TOKEN.

Must NOT:
- publish to Telegram channel
- generate branded image file
- download Telegram photo
- call Bot API
- create/link Tour
- touch Mini App catalog
- touch booking/order/payment
- change supplier public flow beyond existing data reads

Tests:
- auth required
- unknown offer 404
- generated packaging updates draft fields/status
- missing facts create warnings, not invented values
- AI disabled fallback works
- no publish/Tour/booking/payment side effects
- existing supplier offer tests still pass

Before coding:
1. summarize B1–B3.1 state
2. list files expected to change
3. explain how AI remains draft-only and safe

After coding:
1. files changed
2. endpoint/service added
3. packaging fields updated
4. tests run
5. confirm no publish/Tour/Mini App/booking/payment changes
6. next safe step: B5 Admin Moderation & Review