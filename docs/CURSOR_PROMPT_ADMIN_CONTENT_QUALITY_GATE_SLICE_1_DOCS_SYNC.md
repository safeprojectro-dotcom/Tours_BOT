# CURSOR_PROMPT_ADMIN_CONTENT_QUALITY_GATE_SLICE_1_DOCS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync after implementation.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

Admin Content Quality Gate Slice 1 has been implemented:

- app/services/supplier_offer_content_quality_review.py
- content_quality_review in AdminSupplierOfferReviewPackageRead
- review-package includes content_quality_review
- aggregated warnings include content quality warnings
- recommended_next_actions includes review_supplier_offer_content_quality
- read-only only
- no public behavior changes
- no publish blocking
- no bridge/catalog blocking
- no booking/payment changes
- no migrations
- no external AI

Tests passed: 53 passed on relevant suites; compileall OK.

## Goal

Create/update concise docs for Slice 1.

## Required docs

Create:

docs/ADMIN_CONTENT_QUALITY_GATE.md

It should explain:

1. Purpose:
   - production smoke showed a technically valid offer can still contain weak/test/placeholder content.
   - admin needs warnings before publish/catalog/AI public copy decisions.

2. Current Slice 1 behavior:
   - read-only content_quality_review in GET /admin/supplier-offers/{offer_id}/review-package.
   - warnings only.
   - recommended_next_actions may include review_supplier_offer_content_quality.

3. What it checks:
   - orphan promo / discount_code without real discount value.
   - discount deadline without value.
   - thin description/program/marketing_summary.
   - very short short_hook.
   - short_hook_equals_title.
   - existing packaging truth warnings reused.

4. What it does not do:
   - does not block publish.
   - does not block tour bridge.
   - does not block catalog activation.
   - does not auto-fix supplier data.
   - does not call AI.
   - does not change showcase/Mini App/booking.

5. Relation to AI Fact Lock:
   - AI Fact Lock protects commercial facts from AI drift.
   - Content Quality Gate warns about weak/messy source/public content.
   - Both are admin safeguards.

6. Future slices:
   - stronger pre-publish gate if needed.
   - admin UX around review-package.
   - AI copy generation with fact lock.
   - content cleanup workflow.

Also update briefly:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Add short notes:

- Admin Content Quality Gate Slice 1 implemented.
- Read-only warnings in review-package.
- Public behavior unchanged.
- Next possible block: Admin UX/operator workflow or AI copy generation with fact lock.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. ADMIN_CONTENT_QUALITY_GATE doc created
3. Pointers added
4. Confirmation docs-only