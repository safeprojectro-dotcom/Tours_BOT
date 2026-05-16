# CURSOR_PROMPT_A1V2_COCKPIT_TELEGRAM_UX_POLISH

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- d7bb44c feat: add visible admin automation cockpit buttons
- 1dfc53c feat: add cockpit commercial marketing conversion queues
- 8f9180e feat: add read-only admin automation cockpit
- c95bbb8 docs: add admin automation cockpit design gate
- d916f13 docs: add operational automation roadmap

## Previous block

A1V — Visible Admin Button Surface over Cockpit is complete.

Implemented:

- /admin_cockpit
- 📊 Automation Cockpit button
- cockpit summary screen
- queue screens
- card detail screens
- refresh/back navigation
- fact-lock display
- safety flags
- admin allowlist
- tests

Manual Telegram UAT PASS:

- /admin_cockpit opens cockpit summary
- queue buttons work
- Supplier Intake opens
- Offer Readiness opens
- cards render
- card open buttons appear
- back/home/refresh navigation works
- no dangerous publish/schedule/supplier notification buttons are visible

UX issues found:

- too much technical text in list screens
- raw queue codes are visible
- safety block is too long on summary screen
- card list is too verbose
- mixed English/Romanian labels
- safe_read / active=True / p3 technical fields are visible in list view
- open buttons should be clearer, e.g. Deschide tour #2 / Deschide ofertă #12
- commercial/fact-lock text is useful but too long for summary/list screens

## Current block

# A1V2 — Cockpit Telegram UX Polish / Demo-Ready Labels

## Block mode

Functional-block mode.

This block is allowed to be larger because it is UI/rendering/read-only polish over existing read-only cockpit data.

It may change:

- Telegram rendering helpers
- Telegram labels/messages
- queue labels
- compact text formatting
- keyboards
- tests
- docs/handoff

It must NOT change:

- DB schema
- migrations
- write endpoints
- admin API behavior except harmless text/metadata if absolutely necessary
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

Make the Telegram/admin cockpit demo-ready and admin-readable.

The admin should not see raw technical fields in list screens.

The cockpit should communicate:

- what needs attention
- what is ready
- what is blocked
- what is in marketing review
- what is in publishing
- what is in catalog/conversion
- that the screen is safe/read-only
- that supplier/catalog facts are locked

without looking like a JSON/debug dump.

---

# Required references

Inspect and align with:

- app/bot/automation_cockpit_telegram.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/messages.py
- app/bot/constants.py
- app/services/admin_automation_cockpit_service.py
- app/schemas/admin_automation_cockpit.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_admin_automation_cockpit.py
- docs/HANDOFF_A1V_VISIBLE_ADMIN_BUTTON_SURFACE_OVER_COCKPIT.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

---

# UX requirements

## 1. Queue labels must be business-readable

Do not show raw queue codes as main labels.

Use Romanian admin labels:

- supplier_intake → 📥 Intake furnizor
- missing_info → ⚠️ Lipsă informații
- offer_readiness → ✅ Pregătire ofertă
- risk_conflict → 🚨 Risc / conflict
- marketing_review → 🧩 Revizuire marketing
- publishing_queue → 📣 Publicare
- catalog_conversion → 🔗 Catalog / conversie

Raw queue codes may remain in metadata/detail/debug if useful, but not as the primary visible label.

---

## 2. Summary screen must be compact

Current summary shows too much safety text.

Replace long safety block with one compact line:

`🛡 Mod sigur: fără publicare, fără notificări, fără modificări rezervări/plăți.`

Then add a button:

`🛡 Detalii siguranță`

or if avoiding new screen, put safety details only in a shorter bottom note.

Preferred:

- summary screen: compact safety line
- safety detail screen: full safety flags

If adding a safety detail callback is too much, keep full safety details hidden from summary and show only compact line.

Do NOT remove safety entirely.

---

## 3. Summary counts should be business-readable

Instead of:

`Carduri: 20 · urgență: 15 · necesită atenție: 11 ...`

Use a clearer format:

```text
📊 Cockpit automatizare admin

Total: 20 carduri
🚨 Urgent: 15
⚠️ Necesită atenție: 11
✅ Gata: 5
⛔ Blocate: 4
🚫 Acțiuni viitoare/dezactivate: 0