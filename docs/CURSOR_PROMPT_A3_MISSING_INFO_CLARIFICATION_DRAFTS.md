# CURSOR_PROMPT_A3_MISSING_INFO_CLARIFICATION_DRAFTS

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 79010f5 feat: add supplier intake auto validation
- ba6564b feat: standardize cockpit card detail UX
- 80a3a87 feat: standardize cockpit queue list UX
- 5112c21 feat: polish admin cockpit telegram ux
- d7bb44d feat: add visible admin automation cockpit buttons

## Current state

A1 Admin Automation Cockpit MVP v1 is visible in Telegram admin.

A2 Supplier Intake Auto-Validation is implemented.

A2 behavior:
- SupplierOfferIntakeValidationRead exists.
- SupplierOfferIntakeValidationService builds read-only validation from AdminPublishingConsoleItemRead.
- intake_validation is attached to cockpit cards for supplier-offer rows.
- Telegram card detail shows validation block.
- No DB, no migrations, no writes, no sends, no AI, no external calls.

Manual A2 UAT showed:
- validation appears for supplier-offer card.
- However, current “ask supplier next” content may include internal technical blockers:
  - execution link
  - conversion chain
  - plan status blocked
  - exact-tour CTA
  - blockers_count
  - media_review_replacement_requested
- This is not safe for supplier-facing messages.

## Critical product requirement

Supplier-side users may be:
- drivers
- elderly people
- non-technical users
- people who do not understand platform terminology
- people who only know the route, vehicle, price, and practical details

Therefore supplier-facing texts must be:

- short
- simple
- sequential
- polite
- understandable for elderly people
- free of internal platform words
- free of technical codes
- free of mixed Romanian/English/debug copy

Do NOT send technical terms to suppliers:
- execution link
- conversion chain
- CTA
- Mini App exact route
- blockers_count
- media_review_replacement_requested
- publish_safe
- catalog gate
- prepare_conversion_chain
- Layer A
- B11
- internal path names

---

# Current block

# A3 — Missing Info Clarification Drafts + Supplier/Internal Task Split

## Goal

Create a read-only clarification draft layer that separates:

1. Supplier-facing clarification asks  
   Simple questions that can be sent later to the supplier.

2. Internal admin/platform tasks  
   Technical tasks that must stay inside the platform/admin cockpit.

This block must NOT send anything.

It only prepares drafts and displays them to admin.

---

# Safety boundaries

Do NOT:
- add migrations
- add write endpoints
- mutate supplier_offers
- mutate tours
- mutate orders/payments/reservations
- publish to Telegram
- send supplier notifications
- schedule messages
- call AI
- call external providers
- change B11 routing
- change Layer A booking/payment logic
- execute prepare_conversion_chain
- create execution links
- auto-request supplier clarification

This is read-only draft generation only.

---

# Required references

Inspect and align with:

- docs/OPERATIONAL_AUTOMATION_ROADMAP.md
- docs/HANDOFF_A2_SUPPLIER_INTAKE_AUTO_VALIDATION.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- app/schemas/supplier_offer_intake_validation.py
- app/services/supplier_offer_intake_validation_service.py
- app/schemas/admin_automation_cockpit.py
- app/services/admin_automation_cockpit_service.py
- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py
- tests/unit/test_supplier_offer_intake_validation_service.py
- tests/unit/test_admin_automation_cockpit.py
- tests/unit/test_automation_cockpit_telegram.py

If exact file names differ, inspect project structure and report.

---

# Required implementation

## 1. Add clarification draft read model

Create a read-only schema such as:

```python
SupplierClarificationDraftRead  # see app/schemas/supplier_clarification_draft.py
```

Implemented: `SupplierClarificationDraftService` projects drafts from `SupplierOfferIntakeValidationRead`; cockpit exposes `AdminAutomationCockpitCardRead.clarification_draft`; Telegram shows supplier (RO) vs internal sections only (no auto-send).