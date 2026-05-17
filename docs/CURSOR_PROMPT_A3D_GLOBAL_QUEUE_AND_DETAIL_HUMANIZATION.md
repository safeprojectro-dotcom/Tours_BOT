# CURSOR_PROMPT_A3D_GLOBAL_QUEUE_AND_DETAIL_HUMANIZATION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 483c38b fix: clean up admin cockpit card readability
- 29e5c8 fix: humanize supplier clarification drafts
- b0143e7 feat: add supplier clarification draft split
- 79010f5 feat: add supplier intake auto validation
- ba6564b feat: standardize cockpit card detail UX

## Current state

A3C improved default Telegram cockpit card detail readability.

Manual UAT after A3C shows improvement:
- supplier offer detail is much more readable
- supplier draft is simple
- fact-lock is shorter
- safety is compact

Remaining global problems still visible:

1. Queue list rows still show raw English/debug-like warnings:
   - Candidate for tour promotion / last-seats style posts (B15B does not send)
   - Departure is in the past.
   - Not ideal for catalog promotion until gates pass.

2. Tour card detail still shows raw English:
   - Departure is in the past.
   - Not ideal for catalog promotion until gates pass.

3. Internal tasks in supplier-offer detail are human-readable but duplicated:
   - same photo task repeated
   - same reservation link task repeated
   - too many internal tasks shown

4. This must be fixed globally, not only for Ofertă #8.

## Current block

# A3D — Global Queue List + Detail Deduplication & Humanization

## Goal

Make all Telegram Admin Automation Cockpit queue lists and card details readable for non-technical admins.

This must apply globally to:

- queue list rows
- card detail screens
- supplier offer cards
- tour cards
- missing info
- offer readiness
- risk/conflict
- marketing review
- publishing
- catalog/conversion

Default admin UI must not leak raw English/debug/internal labels.

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
- change Layer A logic
- execute prepare_conversion_chain
- create execution links

This is read-only rendering / humanization only.

---

# Required references

Inspect and align with:

- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py
- app/schemas/admin_automation_cockpit.py
- app/schemas/supplier_clarification_draft.py
- app/services/supplier_clarification_draft_service.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_supplier_clarification_draft_service.py
- tests/unit/test_admin_automation_cockpit.py
- docs/HANDOFF_A3C_GLOBAL_ADMIN_CARD_READABILITY_CLEANUP.md
- docs/HANDOFF_A3B_CLARIFICATION_DRAFT_HUMANIZATION_FILTER.md

If exact file names differ, inspect project structure and report.

---

# Required behavior

## 1. One shared humanization helper

Create or strengthen a shared helper used by both:

- queue list rendering
- card detail rendering

Suggested helper names:

```python
_humanize_admin_text(...)
_humanize_admin_warning(...)
_humanize_admin_blocker(...)
_humanize_admin_task(...)