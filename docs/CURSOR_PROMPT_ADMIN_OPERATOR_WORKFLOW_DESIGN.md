# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design/contract step.

Do not change code in this step.

---

## Functional block

ADMIN UX / OPERATOR WORKFLOW

---

## Current checkpoint

The project now has the backend building blocks for supplier offer operations:

- Supplier offer intake
- Packaging generate/review/approve
- Moderation approve/reject
- Showcase preview/publish/retract
- Tour bridge create/link
- Tour activate-for-catalog
- Execution link
- Supplier offer landing
- Bot deep-link routing
- Mini App catalog conversion
- Admin review-package endpoint
- conversion_closure in review-package
- ai_public_copy_review / fact lock review
- content_quality_review

Recent closed blocks:

- Supplier Offer → Central Mini App Catalog Conversion Closure
- BUSINESS-plan-v2 audit after core conversion
- Production/staging E2E walkthrough doc
- AI Fact Lock Slice 1A
- Admin Content Quality Gate Slice 1

Important production smoke result:

- Supplier Offer #11 became Tour #5 and appeared in central Mini App catalog.
- Publish / execution-link / landing / bot exact route were not run because the test offer was not safe to publish to real channel.

---

## Business problem

The system now has many safe backend gates, but the admin/operator workflow is still fragmented.

Admin currently needs to know multiple endpoints and their order:

1. review-package
2. packaging generate
3. packaging approve
4. moderation approve
5. tour-bridge
6. activate-for-catalog
7. showcase-preview
8. publish
9. execution-link
10. catalog / landing / bot checks

This is operationally risky.

We need a clear operator workflow before adding more AI/media/campaign features.

---

## Goal of this Plan step

Design the first practical admin/operator workflow layer.

Answer:

1. What is the recommended admin workflow sequence?
2. Which existing endpoint/action powers each step?
3. Which checks must be visible before each action?
4. What should be the first implementation slice?
5. Should first implementation be Telegram admin buttons, API helper endpoint, or docs/checklist only?
6. How to avoid unsafe auto-actions?

---

## Source docs/code to read

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md
- docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md
- docs/ADMIN_CONTENT_QUALITY_GATE.md
- docs/AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/TELEGRAM_ADMIN_MODERATION_WORKSPACE_DESIGN.md if present
- docs/MINI_APP_UX.md
- docs/TESTING_STRATEGY.md

Inspect:

- app/api/routes/admin.py
- app/schemas/supplier_admin.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_content_quality_review.py
- app/services/supplier_offer_ai_public_copy_fact_lock.py
- app/services/supplier_offer_packaging_service.py
- app/services/supplier_offer_packaging_review_service.py
- app/services/supplier_offer_tour_bridge_service.py
- app/services/admin_tour_write.py
- app/services/supplier_offer_execution_link_service.py
- app/services/supplier_offer_moderation_service.py
- any Telegram admin moderation handlers
- tests around admin/review-package/catalog conversion

---

## Architecture / safety rules

Preserve:

- Admin actions remain explicit.
- No auto-publish.
- No auto-create Tour on approval.
- No auto-activate catalog on approval.
- No auto-execution-link on publish unless explicitly designed later.
- Review package is read-only.
- Mini App remains execution truth.
- Layer A remains booking/payment authority.
- Channel showcase is marketing.
- AI is copywriter/validator, not commercial source of truth.
- Content quality warnings are advisory for now.
- visibility != bookability.
- publish != catalog visibility.
- bridge != open_for_sale.
- execution link != inventory truth.

---

## Questions to answer

### 1. Current operator surfaces

Map current available operator/admin surfaces:

- central admin API
- Telegram admin workspace if implemented
- supplier-facing bot flow
- Mini App admin UI if any
- docs/checklists only

For each, say:
- implemented / partial / not implemented
- what actions can be done there
- what is missing

### 2. Current full workflow

Define the explicit safe admin sequence:

Suggested:

1. Open review-package
2. Resolve content_quality_review warnings if needed
3. Resolve ai_public_copy_review / fact lock warnings if needed
4. Generate packaging if needed
5. Approve packaging
6. Approve moderation
7. Create/link Tour bridge
8. Activate Tour for catalog
9. Verify central Mini App catalog
10. Showcase preview
11. Publish showcase only if content safe/channel safe
12. Create execution link
13. Verify supplier offer landing
14. Verify bot deep-link exact Tour

Clarify which steps are required, optional, or conditional.

### 3. Admin decision states

Design simple operator states derived from review-package:

Examples:

```text
needs_packaging_generation
needs_packaging_approval
needs_content_review
needs_moderation_approval
ready_to_create_tour_bridge
ready_to_activate_catalog
catalog_visible
ready_for_showcase_preview
ready_to_publish_showcase
ready_to_create_execution_link
conversion_complete
blocked