# CURSOR_PROMPT_A4_SUPPLIER_CLARIFICATION_OUTBOX_FOUNDATION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 0f97a8b fix: humanize admin cockpit text surfaces
- 483c38b fix: clean up admin cockpit card readability
- 29e5c8 fix: humanize supplier clarification drafts
- b0143e7 feat: add supplier clarification draft split
- 79010f5 feat: add supplier intake auto validation

## Current state

Admin Automation Cockpit is visible in Telegram.

A2:
- read-only Supplier Intake Auto-Validation.

A3:
- read-only Supplier Clarification Drafts.
- supplier-facing questions are separated from internal platform tasks.

A3B:
- supplier-facing message is hard-filtered and whitelist-based.
- supplier-facing text is simple Romanian.

A3C/A3D/A3E:
- admin card details and queue rows were humanized.
- raw debug/English/platform text should no longer leak in default admin UI.

Current gap:
The system can show a clarification draft, but it does not persist it as an admin-managed work item.
If admin closes Telegram, the clarification task is not tracked.

## Current block

# A4 — Supplier Clarification Outbox Foundation

## Goal

Create a durable internal outbox for supplier clarification drafts.

This is an internal admin workflow only.

The system must allow an admin to create/save a supplier clarification draft from an existing cockpit supplier-offer card, so the clarification is tracked and not lost.

## Important product rule

This block must NOT send anything to supplier.

A4 is an internal outbox foundation:
- create draft
- list/read drafts
- display in Telegram
- track status
- no external send

Actual supplier sending may come later in a separate explicit gated block.

---

# Safety boundaries

Do NOT:
- send Telegram messages to suppliers
- publish to Telegram channel
- schedule messages
- call AI
- call external providers
- change booking/payment/order/reservation logic
- change Layer A
- change B11 routing
- execute prepare_conversion_chain
- create supplier execution links
- auto-notify suppliers
- add broadcast
- add WhatsApp/Email sending

Allowed:
- DB migration for internal outbox table
- internal admin API read/create endpoints
- internal service/repository
- Telegram admin button to create/view internal draft
- tests

---

# Required references

Inspect and align with:

- app/bot/automation_cockpit_telegram.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/messages.py
- app/schemas/supplier_clarification_draft.py
- app/services/supplier_clarification_draft_service.py
- app/schemas/admin_automation_cockpit.py
- app/services/admin_automation_cockpit_service.py
- app/api/routes/admin.py
- app/api/dependencies or existing admin auth dependency
- app/db / app/models / app/repositories patterns
- alembic migration patterns
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_supplier_clarification_draft_service.py
- tests/unit/test_admin_automation_cockpit.py
- existing admin API tests if present

Also inspect existing patterns for:
- admin protected endpoints
- repository/service layer separation
- SQLAlchemy/SQLModel model style
- timestamp columns
- enums/statuses
- idempotency style if used nearby

---

# Architecture rules

Follow existing project architecture:

- PostgreSQL-first.
- Service layer owns business rules.
- Repository layer is persistence-only.
- API route is thin.
- Telegram handler is UI orchestration only.
- Do not put business rules in Telegram rendering.
- Do not mutate source supplier_offer/tour from outbox creation.
- Outbox must not be a second source of truth for supplier offer facts.

Outbox stores the draft snapshot and admin workflow state only.

---

# Required data model

Create a new internal table/model, suggested name:

```text
supplier_clarification_outbox_items