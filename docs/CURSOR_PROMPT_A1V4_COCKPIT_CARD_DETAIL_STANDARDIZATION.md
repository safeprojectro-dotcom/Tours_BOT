# CURSOR_PROMPT_A1V4_COCKPIT_CARD_DETAIL_STANDARDIZATION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 80a3a87 feat: standardize cockpit queue list UX
- 512c2d feat: polish admin cockpit telegram ux
- d7bb44c feat: add visible admin automation cockpit buttons
- 1dfc53c feat: add cockpit commercial marketing conversion queues
- 8f9180e feat: add read-only admin automation cockpit

## Previous blocks

A1V created visible Telegram/admin cockpit buttons.

A1V2 polished the summary screen:
- compact summary
- business queue labels
- compact safety line
- safety detail screen
- clearer buttons

A1V3 standardized queue list screens:
- compact list card format across all queues
- no raw safe_read / active=True / p3 in list screens
- readable source labels
- one primary issue per card
- commercial fact-lock shown once per queue

Manual UAT after A1V3 shows:

PASS:
- /admin_cockpit opens
- summary looks good
- queue buttons work
- queue list screens are improved
- open buttons work
- no dangerous action buttons

Remaining issue:
- card detail screens still look technical/debug-like
- detail shows raw source paths:
  - admin_action_path
  - admin_tour_path
- detail shows raw safety flags:
  - read_only=True
  - no_layer_a_mutation=True
- detail still shows English backend text:
  - Open tour in admin
  - Candidate for tour promotion...
  - Tour promotion rows are not evaluated...
- this likely affects all card detail screens, not one card only

## Current block

# A1V4 — Cockpit Card Detail Standardization

## Block mode

Functional-block mode.

This block is allowed to be larger because it is Telegram rendering / UI polish only over existing read-only cockpit data.

It may change:

- Telegram detail renderer
- Telegram display helper functions
- Telegram message strings
- tests
- docs/handoff

It must NOT change:

- DB schema
- migrations
- write endpoints
- admin API behavior
- service classification rules
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

Standardize ALL Telegram cockpit card detail screens so they are business-readable and demo-ready.

Do NOT fix only one card.

The card detail screen should be useful for an admin/operator, not a raw debug dump.

---

# Required references

Inspect and align with:

- app/bot/automation_cockpit_telegram.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/messages.py
- app/bot/constants.py
- app/schemas/admin_automation_cockpit.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_admin_automation_cockpit.py
- docs/HANDOFF_A1V3_COCKPIT_QUEUE_LIST_STANDARDIZATION.md
- docs/HANDOFF_A1V2_COCKPIT_TELEGRAM_UX_POLISH.md
- docs/HANDOFF_A1V_VISIBLE_ADMIN_BUTTON_SURFACE_OVER_COCKPIT.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

---

# UX standard for card detail

## 1. Detail screen should use one business-readable format

Target format:

```text
📄 Detaliu card

Smoke per-seat catalog / booking
Tur #2 · ✅ Gata

Pas sugerat:
Deschide turul în admin

Atenționare:
⚠️ Candidat pentru promovare / postări tip „ultimele locuri”.

Surse:
• Tur admin: disponibil
• Acțiune admin: disponibilă

🛡 Siguranță:
✅ Doar citire
✅ Fără publicare Telegram
✅ Fără planificator
✅ Fără notificare furnizor
✅ Fără modificări rezervări/plăți
✅ Fără schimbări B11