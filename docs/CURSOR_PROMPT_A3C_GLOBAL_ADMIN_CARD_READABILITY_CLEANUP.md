# CURSOR_PROMPT_A3C_GLOBAL_ADMIN_CARD_READABILITY_CLEANUP

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 29e5c8 fix: humanize supplier clarification drafts
- b0143e7 feat: add supplier clarification draft split
- 79010f5 feat: add supplier intake auto validation
- ba6564b feat: standardize cockpit card detail UX
- 80a3a87 feat: standardize cockpit queue list UX

## Current state

A1 Admin Automation Cockpit MVP is visible in Telegram.

A2 added read-only Supplier Intake Auto-Validation.

A3 added supplier clarification drafts and split supplier-facing questions from internal tasks.

A3B added a hard supplier-facing filter:
- supplier_facing_message_ro is now simple
- supplier-facing draft uses whitelist questions only
- no technical terms should appear in supplier-facing copy
- no sending / no supplier notification / no publish

Manual UAT after A3B confirms:

PASS:
- supplier-facing draft is now simple
- supplier-facing draft asks for a clear photo
- no technical garbage appears in the supplier-facing message

Remaining problem:
- the overall card detail still shows too much raw technical/debug text to admins.
- this is not only Ofertă #8; it is likely global across many card types/queues.

Bad examples still visible in default admin card detail:

- Cover/media gate: [media_review_replacement_requested] B7.1 ...
- publication blocked; conversion not green
- content_quality, publish_safe
- prepare_chain:blocked:create_tour_bridge
- cta_safety:missing_execution_link
- offer_debug.flags_publish_not_ready
- publish_readiness:blocked
- gate:showcase_media
- gate:showcase_preview
- execution link is required before channel publish...
- Context comercial with many empty “—” rows
- English fact-lock paragraph

This is not acceptable for a non-technical external admin.

## Critical product requirement

A cockpit card detail must be understandable by:

- an admin from another organization
- a dispatcher
- a non-technical operator
- a person who does not know internal project terms
- someone who only needs to decide what to do next

Default card detail must NOT look like a debug log.

Technical raw values may be kept in code/tests but must not be shown in the default Telegram card detail.

---

# Current block

# A3C — Global Admin Card Readability Cleanup

## Goal

Make all Telegram cockpit card detail screens globally business-readable.

Do NOT fix only supplier offer #8.

Apply to all card detail screens/cards using the shared renderer:

- tour cards
- supplier offer cards
- missing info cards
- risk/conflict cards
- marketing review cards
- publishing cards
- catalog/conversion cards
- any card rendered through the cockpit Telegram detail formatter

The admin should understand:

1. What is this card?
2. What is the status?
3. What is the main blocker / reason?
4. What can be asked from supplier?
5. What are internal platform/admin tasks?
6. What is safe / not automatic?

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

This block is read-only Telegram rendering / mapping only.

---

# Required references

Inspect and align with:

- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py
- app/schemas/admin_automation_cockpit.py
- app/schemas/supplier_clarification_draft.py
- app/services/supplier_clarification_draft_service.py
- app/schemas/supplier_offer_intake_validation.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_supplier_clarification_draft_service.py
- tests/unit/test_admin_automation_cockpit.py
- docs/HANDOFF_A3B_CLARIFICATION_DRAFT_HUMANIZATION_FILTER.md
- docs/HANDOFF_A3_MISSING_INFO_CLARIFICATION_DRAFTS.md
- docs/HANDOFF_A2_SUPPLIER_INTAKE_AUTO_VALIDATION.md

If exact file names differ, inspect project structure and report.

---

# Required behavior

## 1. Global detail layout

Default Telegram card detail should use this high-level structure:

```text
📄 Detaliu card

{title}
{Tur/Ofertă/Card #id} · {status}

🚫 Blocaj principal:
{human-readable blocker}

⚠️ Atenționare:
{human-readable warning}

📋 Validare:
{short human validation summary}

✉️ Pentru furnizor:
{supplier_facing_message_ro if exists}

🛠 Sarcini interne:
• {human-readable internal task}
• {human-readable internal task}

🔒 Date comerciale:
{short Romanian fact-lock text if applicable}

🛡 Siguranță:
✅ Doar citire
✅ Fără publicare Telegram
✅ Fără notificare furnizor
✅ Fără modificări rezervări/plăți

Implemented in `format_cockpit_card_detail_text` (`automation_cockpit_telegram.py`) with humanization helpers and catalogue keys in `messages.py`.