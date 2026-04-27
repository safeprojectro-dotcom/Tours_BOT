You are continuing Tours_BOT after B4.3.

Goal:
B5 — Admin Moderation & Review.

Current state:
Supplier offers can be collected, enriched, packaged, formatted, and truth-checked.
B4.3 can set packaging_status = needs_admin_review and quality_warnings_json.
Now admin needs a safe review layer before any publication.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/AI_ASSISTANT_SPEC.md

Goal:
Add admin-facing review API for packaged supplier offers.

Core rule:
Approve package ≠ publish.
B5 must not publish to Telegram and must not create Tour.

Admin should be able to:
1. open review detail
2. see raw supplier facts
3. see packaging draft
4. see warnings/missing fields
5. approve packaging
6. reject packaging with reason
7. request clarification with reason
8. optionally edit the packaged Telegram draft text before approval

Expected API:
- GET /admin/supplier-offers/{offer_id}/packaging/review
- POST /admin/supplier-offers/{offer_id}/packaging/approve
- POST /admin/supplier-offers/{offer_id}/packaging/reject
- POST /admin/supplier-offers/{offer_id}/packaging/request-clarification
- optional: PATCH /admin/supplier-offers/{offer_id}/packaging/draft

Status logic:
- packaging_generated → can approve
- needs_admin_review → can approve only if admin explicitly accepts warnings
- approved_for_publish → package approved, but not published
- packaging_rejected → rejected package
- clarification_requested → supplier/admin clarification needed

If enum already exists, extend carefully. If not, extend SupplierOfferPackagingStatus with only additive values.

Data:
Use existing fields where possible:
- packaging_status
- packaging_draft_json
- missing_fields_json
- quality_warnings_json
- admin_internal_notes
- supplier_admin_notes

Add fields only if necessary:
- packaging_reviewed_at
- packaging_reviewed_by
- packaging_rejection_reason
- clarification_reason
Prefer minimal additive migration if needed.

Safety:
- no publish
- no Telegram send
- no Tour creation
- no Mini App catalog changes
- no booking/order/payment changes
- no AI call
- no lifecycle_status change unless existing moderation policy requires it; prefer packaging_status only

Tests:
- review endpoint returns raw + draft + warnings
- approve from packaging_generated works
- approve from needs_admin_review requires accept_warnings=true
- approve from needs_admin_review without accept_warnings fails
- reject stores reason and status
- request clarification stores reason and status
- draft edit updates packaging_draft_json.telegram_post_draft only
- no publish fields changed
- no lifecycle_status changed
- existing B4 tests still pass

Before coding:
1. summarize B1–B4.3 state
2. list files expected to change
3. explain why B5 is review-only and safe
4. state exact non-goals

After coding:
1. files changed
2. API endpoints added
3. status transitions
4. tests run
5. confirm no publish/Tour/Mini App/booking/payment/AI changes
6. next safe step: B6 Branded Telegram Post/Card Template or B9/B10 Offer → Tour Bridge design/implementation