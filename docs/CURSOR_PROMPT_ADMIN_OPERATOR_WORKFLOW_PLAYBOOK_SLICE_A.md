# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_PLAYBOOK_SLICE_A

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only step.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

We just completed design for ADMIN UX / OPERATOR WORKFLOW.

Decision:

- Do not implement Telegram buttons yet.
- Do not implement web admin UI yet.
- Do not add batch/macro actions.
- Do not add auto-publish / auto-bridge / auto-activation.
- First create a short canonical operator playbook.
- Next implementation slice after this should be read-only `operator_workflow` in review-package.

Existing backend building blocks:

- GET /admin/supplier-offers/{offer_id}/review-package
- content_quality_review
- ai_public_copy_review
- bridge_readiness
- active_tour_bridge
- linked_tour_catalog
- showcase_preview
- execution_links_review
- conversion_closure
- recommended_next_actions

Recent production smoke proved:

- Supplier Offer #11 → Tour #5 → central Mini App catalog PASS.
- Publish/execution-link/landing/bot exact route NOT RUN because real channel publish was unsafe for test copy.

## Goal

Create a concise canonical admin operator playbook.

Create:

docs/ADMIN_OPERATOR_WORKFLOW.md

Language: Russian.

This must be practical and compact. Do not write a long theory document.

## Required sections

### 1. Purpose

Explain:

- This is the canonical operator sequence for supplier offer review → catalog/showcase/conversion.
- It exists because backend gates are safe but fragmented.
- Admin must not rely on memory of endpoint order.

### 2. Golden rule

Always start with:

GET /admin/supplier-offers/{offer_id}/review-package

Explain that review-package is the single observation surface and is read-only.

### 3. Canonical sequence

Create a table:

Columns:

```text
Step | What operator checks | Action endpoint | Verification | Safety note