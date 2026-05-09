# CURSOR_PROMPT_BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a docs-only audit step.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

---

## Goal

Create a compact completion audit for BUSINESS-plan-v2 after the core conversion chain was closed.

We do NOT create BUSINESS_PLAN_V3 yet.

We do NOT rewrite the whole roadmap.

We only document:

- what BUSINESS-plan-v2 wanted;
- what is now done;
- what is partially done;
- what is still open;
- what should be the next large functional block.

---

## Current milestone

The core supplier offer conversion chain is now test-proven:

Supplier Offer
→ Admin review/approval
→ create/link Tour
→ activate Tour for central Mini App catalog
→ active execution link
→ supplier-offer landing / bot deep link routes to exact Tour
→ Mini App central catalog shows Tour
→ booking/payment remains Layer A

Recent block:

SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE

Important proven facts:

- Approval alone does not create Tour.
- Tour bridge is explicit.
- Catalog activation is explicit.
- Central Mini App catalog visibility is Tour-driven.
- Supplier offer landing and bot exact routing require active execution link.
- Layer A booking/payment unchanged.
- Tests passed: 66 passed, compileall OK.

---

## Source docs to read

Read:

- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md if present
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md if present
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/IMPLEMENTATION_PLAN.md

If exact filenames differ, use closest equivalents.

---

## Create new audit doc

Create:

```text
docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md