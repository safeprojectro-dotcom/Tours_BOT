# CURSOR_PROMPT_AI_FACT_LOCK_SLICE_1A_FINALIZE_TESTS_AND_DOCS

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Это finalization step после случайно запущенного HANDOFF_AI_PUBLIC_COPY_COMMERCIAL_FACT_LOCK_DESIGN_TO_IMPLEMENTATION.md.

Не переписывать реализацию с нуля.
Не менять booking/payment/order/reservation.
Не менять Mini App UI.
Не менять showcase/publish source.
Не менять Tour bridge/catalog activation.
Не вызывать external AI.
Не добавлять migrations.

## Current implemented state

A first implementation slice already exists:

- app/services/supplier_offer_source_facts_snapshot.py
- app/services/supplier_offer_ai_public_copy_fact_lock.py
- AdminSupplierOfferAiPublicCopyReviewRead in app/schemas/supplier_admin.py
- ai_public_copy_review exposed in AdminSupplierOfferReviewPackageRead
- SupplierOfferReviewPackageService builds fact-lock slice
- recommended_next_actions includes resolve_ai_public_copy_fact_lock when fact lock fails
- tests/unit/test_supplier_offer_ai_public_copy_fact_lock.py

The implementation reads optional:

packaging_draft_json["ai_public_copy_v1"]

and validates:

- snapshot stale
- unknown fact claim keys
- mismatched claimed facts
- invalid fact_claims structure

Boundaries must remain:

- no external AI
- no publish behavior change
- no showcase HTML source change
- no booking/payment change
- no bridge/catalog behavior change

## Goal

Finalize and document this as:

AI FACT LOCK — Slice 1A: Source facts snapshot + fact-claim validator

Do not implement the full ai_public_copy_v1 generation flow yet unless it is already trivial and fully covered. Prefer documentation/follow-up note over broad code.

## Required verification

Run:

python -m pytest tests/unit/test_supplier_offer_ai_public_copy_fact_lock.py -v
python -m pytest tests/unit/test_supplier_offer_review_package.py -v
python -m pytest tests/unit/test_supplier_offer_catalog_conversion_closure.py -v
python -m pytest tests/unit/test_supplier_offer_showcase_ro.py -v
python -m pytest tests/unit/test_supplier_offer_track3_moderation.py -v
python -m compileall app alembic -q

If anything fails, fix only the relevant issue.

## Required docs

Create or update:

docs/AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md

Document concisely:

1. AI is copywriter + validator, not source of commercial truth.
2. Source facts snapshot v1:
   - what it includes
   - hash/ref
   - commercial facts are locked
3. ai_public_copy_v1 expected shape:
   - snapshot_ref / snapshot_content_hash
   - fact_claims
   - future copy_slots
4. Fact lock behavior:
   - stale snapshot blocker
   - unknown fact claim key blocker
   - fact mismatch blocker
   - invalid fact_claims blocker
   - empty fact_claims warning
5. Current slice status:
   - validator implemented
   - review-package exposure implemented
   - no external AI
   - publish/showcase unchanged
   - packaging generate does not need to be fully wired unless already implemented
6. Future slices:
   - persist ai_public_copy_v1 stub on packaging generate
   - add AI copy generation
   - add admin approval semantics
   - use approved AI copy only for marketing slots, never factual lines

Also update briefly:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Add short notes:

- AI Fact Lock Slice 1A implemented.
- Source facts snapshot + fact-claim validator exist.
- Review package exposes ai_public_copy_review.
- Public behavior is unchanged.
- Next implementation slice should be ai_public_copy_v1 stub persistence on packaging generate OR admin AI copy workflow, depending on product decision.

Do not rewrite docs.

## Final report

Report exactly:

1. Files changed
2. Tests/checks run
3. Contract doc updated/created
4. Public behavior unchanged confirmation
5. What is implemented now
6. What remains for next slice
7. Risks/follow-up