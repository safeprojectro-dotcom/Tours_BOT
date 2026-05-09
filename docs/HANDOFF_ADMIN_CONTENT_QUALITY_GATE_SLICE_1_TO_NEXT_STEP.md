# HANDOFF_ADMIN_CONTENT_QUALITY_GATE_SLICE_1_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN WORKFLOW / CONTENT QUALITY GATE

## Why this exists

Production smoke proved that Supplier Offer → Tour → central Mini App catalog works.

But it also showed an operator/content risk:

- a technically valid offer can contain weak or placeholder text;
- discount_code can exist without real discount value;
- program/route/copy can be too weak for real public publishing;
- admin needs quality warnings before publish/catalog decisions.

## Slice 1 goal

Add read-only content quality warnings to:

GET /admin/supplier-offers/{offer_id}/review-package

## Checklist artifact — Slice 1 delivered

**Done:** deterministic **`content_quality_review`** on **`GET …/review-package`** — module **`app/services/supplier_offer_content_quality_review.py`** (**`evaluate_content_quality_review`**). Aggregates **`assess_missing_and_warnings`** and **`assess_packaging_truth_warnings`**, plus **`short_hook`**, **`marketing_summary`**, **`description`** heuristics **;** merged into top-level **`warnings`** as **`Content quality [{code}]: …`**. **`recommended_next_actions`** includes **`review_supplier_offer_content_quality`** when **`has_quality_warnings`** (**informational — does not block APIs**). **Tests:** **`tests/unit/test_supplier_offer_content_quality_review.py`**, **`tests/unit/test_supplier_offer_review_package.py`**.

Public surfaces unchanged (**booking/payment**, showcase publish, bridge/catalog**) — same as § Boundaries **.**

## Boundaries

Slice 1 must not block existing flows.

It must not change:

- booking/payment
- Mini App UI
- publish behavior
- showcase template
- Tour bridge
- catalog activation
- execution link
- AI generation

## Expected result (**met for Slice 1**)

review-package includes:

- **`content_quality_review`** (**`warnings[]`**, **`has_quality_warnings`**)
- warnings surfaced via **`assess_packaging_truth_warnings`** (e.g. discount inconsistencies**,** scarcity language heuristic**)**, **`assess_missing_and_warnings`** (e.g. weak **/** missing **`program_text`**)**, plus thin **`short_hook`**, **`marketing_summary`**, **`description`** rules
- aggregated **`warnings`** include prefixed lines as above
- **`recommended_next_actions`** includes **`review_supplier_offer_content_quality`** when **`has_quality_warnings`** **.**

## Relationship to AI Fact Lock

AI Fact Lock protects commercial facts from AI drift.

Content Quality Gate protects operator workflow from weak/messy source content and public copy quality problems.

Both are admin-review safeguards.

## Next possible slices

1. Admin UX/operator workflow screen around review-package.
2. Stronger gating before publish only.
3. AI copy generation with fact lock.
4. Dedicated content cleanup/edit workflow.