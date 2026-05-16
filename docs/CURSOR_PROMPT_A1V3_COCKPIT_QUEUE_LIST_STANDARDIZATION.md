# CURSOR_PROMPT_A1V3_COCKPIT_QUEUE_LIST_STANDARDIZATION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 512c2d feat: polish admin cockpit telegram ux
- d7bb44c feat: add visible admin automation cockpit buttons
- 1dfc53c feat: add cockpit commercial marketing conversion queues
- 8f9180e feat: add read-only admin automation cockpit
- c95bbb8 docs: add admin automation cockpit design gate

## Previous blocks

A1V implemented the visible Telegram/admin surface over the cockpit.

A1V2 polished the summary screen:
- compact cockpit summary
- business queue labels
- compact safety line
- safety detail screen
- clearer open buttons
- fact-lock retained

Manual UAT after A1V2 shows:

PASS:
- /admin_cockpit works
- summary is much cleaner
- queue buttons work
- safety details button exists
- open buttons are clearer

Remaining issue:
- queue list screens are still too verbose and inconsistent across queues
- Revizuire marketing still shows long backend text
- other queues likely have the same issue
- list screens still show too much blocker/warning/status text
- English backend messages appear in Romanian admin UI
- queue card format must be standardized across all queues, not fixed one by one

## Current block

# A1V3 — Cockpit Queue List Standardization

## Block mode

Functional-block mode.

This block is allowed to be larger because it is UI/rendering/read-only standardization over existing cockpit data.

It may change:

- Telegram rendering helpers
- Telegram display-label helpers
- Telegram message strings
- queue card formatting
- tests
- docs/handoff

It must NOT change:

- DB schema
- migrations
- write endpoints
- admin API behavior
- service classification rules unless absolutely required for display only
- Telegram channel publish/send
- scheduler
- supplier notification send
- QR
- Layer A booking/payment/order/reservation
- B11 routing
- AI execution
- external provider calls

---

# Goal

Standardize ALL Telegram cockpit queue list screens so every queue uses the same compact, business-readable card format.

Queues covered:

- supplier_intake
- missing_info
- offer_readiness
- risk_conflict
- marketing_review
- publishing_queue
- catalog_conversion

Do NOT only fix marketing_review.

The result should be suitable for a non-technical admin/operator demo.

---

# Required references

Inspect and align with:

- app/bot/automation_cockpit_telegram.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/messages.py
- app/bot/constants.py
- app/schemas/admin_automation_cockpit.py
- app/services/admin_automation_cockpit_service.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_admin_automation_cockpit.py
- docs/HANDOFF_A1V_VISIBLE_ADMIN_BUTTON_SURFACE_OVER_COCKPIT.md
- docs/HANDOFF_A1V2_COCKPIT_TELEGRAM_UX_POLISH.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

---

# UX standard

## 1. All queue list screens must use one compact card format

For every queue, list cards like:

```text
1) Excursie Timișoara Oradea
Ofertă #12 · ⚠️ Necesită atenție
Următorul pas: Verifică datele marketing lipsă
⛔ Pachetul trebuie aprobat pentru publicare.