# CURSOR_PROMPT_A2_SUPPLIER_INTAKE_AUTO_VALIDATION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- ba6564b feat: standardize cockpit card detail UX
- 80a3a87 feat: standardize cockpit queue list UX
- 5112c21 feat: polish admin cockpit telegram ux
- d7bb44d feat: add visible admin automation cockpit buttons
- 1dfc53c feat: add cockpit commercial marketing conversion queues

## Context

A1 Admin Automation Cockpit MVP v1 is now visible and usable through Telegram admin buttons.

Completed:
- read-only automation cockpit backend
- commercial / marketing / conversion queues
- Telegram admin cockpit surface
- compact summary
- standardized queue lists
- standardized card details
- safety / fact-lock visible
- no dangerous actions

Now stop cockpit polishing.

The next production-relevant block is:

# A2 — Supplier Intake Auto-Validation

## Goal

Add a read-only supplier-offer validation layer that automatically evaluates supplier offer completeness and risk before admin review.

The system should answer:

- What supplier facts are present?
- What required facts are missing?
- What fields are weak/unclear?
- What blocks publication?
- What blocks catalog/conversion preparation?
- What should be requested from the supplier next?

This must reduce manual admin workload when many suppliers submit routes/offers.

## Block mode

Functional-block mode.

This is allowed to be a larger block because it is validation/read-model only.

## Safety boundaries

Do NOT:
- add migrations
- add write endpoints
- mutate supplier_offers
- mutate tours
- mutate orders/payments/reservations
- publish to Telegram
- send supplier notifications
- create clarification messages
- call AI
- call external providers
- change B11 routing
- change Layer A booking/payment logic
- change prepare_conversion_chain execution
- change Mini App customer booking paths

This block is read-only validation only.

---

# Required references

Inspect and align with:

- docs/OPERATIONAL_AUTOMATION_ROADMAP.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/HANDOFF_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION.md
- docs/HANDOFF_A1_BLOCK2_COMMERCIAL_MARKETING_CONVERSION_QUEUES.md
- docs/HANDOFF_A1V4_COCKPIT_CARD_DETAIL_STANDARDIZATION.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- app/services/admin_automation_cockpit_service.py
- app/schemas/admin_automation_cockpit.py
- existing supplier offer models/schemas/services/repositories
- existing supplier offer review-package / publishing-console / readiness services
- tests/unit/test_admin_automation_cockpit.py
- tests/unit/test_admin_publishing_console.py

If exact file names differ, inspect project structure and report.

---

# Required design / implementation

## 1. Add supplier intake validation read model

Create a service-layer read-only validator, for example:

- `SupplierOfferIntakeValidationService`

or extend an existing supplier offer readiness/review service if that is the project convention.

The validator should produce a structured read model such as:

```python
SupplierOfferIntakeValidationRead  # see app/schemas/supplier_offer_intake_validation.py for fields
```

Implemented: `SupplierOfferIntakeValidationService` (`app/services/supplier_offer_intake_validation_service.py`) derives this from each read-only `AdminPublishingConsoleItemRead`; cockpit cards expose it as `AdminAutomationCockpitCardRead.intake_validation` (A2).