# CURSOR_PROMPT_A6E_MOBILE_ADMIN_COMPACT_SUMMARY_AND_ACTION_CLARITY

## Project

Tours_BOT

## Context

A6A, A6B, A6C, A6D are complete and committed.

Recent commits:
- 6a87691 feat: add catalog conversion readiness snapshot
- 924426 feat: add guided catalog conversion actions
- 2befca9 fix: clean up operator workflow catalog conversion text
- 968fea3 fix: polish catalog conversion admin UX

A6D improved admin text and buttons, but Telegram UAT still shows that real mobile admin UX is too verbose.

Observed Telegram UAT issues:
- Catalog / conversie queue entries are too long.
- Detail cards still become large text walls.
- Generic “Necesită verificare internă” repeats too often.
- Raw ISO datetime strings are hard to read.
- Admin does not always know the single next action.
- Test or dirty supplier text can appear as confusing route/title.
- Supplier-facing clarification draft and internal tasks are visible together, but the admin needs clearer separation.

This step is a compact mobile UX pass only.

## Goal

Make admin Telegram cards readable for a non-technical admin, including an older person or a driver/supplier-side person who does not understand internal systems.

The admin should understand within 5 seconds:

1. What is this item?
2. Is it blocked / needs attention / ready?
3. What is the one next safe action?
4. What can be sent or asked from supplier?
5. What is internal only?

## Scope

Read-only Telegram formatting and i18n cleanup only.

Allowed files likely include:
- app/bot/automation_cockpit_telegram.py
- app/bot/supplier_offer_operator_workflow_telegram.py
- app/bot/supplier_offer_conversion_status_panel_telegram.py
- app/bot/handlers/admin_moderation.py
- app/bot/messages.py
- tests/unit/test_automation_cockpit_telegram.py
- tests/unit/test_operator_workflow_telegram_format.py
- tests/unit/test_supplier_offer_conversion_status_panel.py
- tests/unit/test_operator_workflow_c2b3_keyboard.py

Do not add DB migrations.

## Hard safety boundaries

Do NOT:
- publish to Telegram channel
- notify suppliers
- create/link tours directly
- activate catalog directly
- create execution links directly
- change booking/payment/orders
- change Layer A
- change B11 routing
- bypass any propose/confirm gates
- add new external calls
- add AI calls
- change service-layer business rules

This is UX/readability only.

## Required UX improvements

### 1. Queue list compact format

For /admin_cockpit category lists such as Catalog / conversie, each item should be compact.

Current style is too long:
- title
- Tur/Ofertă
- status
- next step
- blocker
- catalog conversion status

Target style example:

For tour:
1) Test Belgrade Tour
Tur #1 · ⛔ Blocat
Motiv: Data plecării este în trecut
Pas: Revizuiește turul

For offer:
2) Test 1
Ofertă #10 · ⚠️ Necesită atenție
Motiv: Conversia nu este gata
Pas: Deschide oferta

Rules:
- Maximum 4 logical lines per entry.
- Do not repeat generic “Necesită verificare internă” if a clearer reason exists.
- If only generic reason exists, show:
  “Motiv: Verificare internă necesară”
- Keep up to 5 entries, as today.
- Keep existing action buttons.

### 2. Detail card top summary

Every card detail should start with a compact summary before long blocks.

Target:

📄 Detaliu card

Test 1
Ofertă #10 · ⚠️ Necesită atenție

Pe scurt:
⛔ Conversia nu este gata
➡️ Pas: Rezolvă pasul de conversie
🔒 Intern: nu se trimite nimic automat

Then optional sections:
- Pentru furnizor
- Sarcini interne
- Date comerciale
- Catalog / conversie
- Siguranță

### 3. “Necesită verificare internă” dedupe everywhere

Across:
- operator workflow block
- conversion panel
- automation cockpit detail
- queue list

If the same generic line appears multiple times, show it once.

If it appears together with a specific line, prefer the specific line.

Example:
- “Lipsește legătura ofertă–tur”
- “Necesită verificare internă”

Show:
- “Lipsește legătura ofertă–tur”

### 4. Human readable dates

Where Telegram renders datetime fields in admin cards, convert ISO strings such as:
2026-04-28 18:00+00:00

To compact display:
28.04.2026, 18:00

If date formatting helper already exists, reuse it.
If not, add a small local helper in Telegram formatting only.
Do not change API schemas.

### 5. Supplier draft separation

Supplier-facing text must remain clean and copyable.

Keep:

📩 Pentru furnizor:
Bună ziua! Pentru ofertă avem nevoie de câteva clarificări:

1. ...
2. ...

Mulțumim!

Then:

🛠 Sarcini interne:
...

Never mix internal tasks into supplier-facing block.

### 6. Commercial data compact

If commercial data are mostly empty or repetitive, do not show a large block.

Show only meaningful fields:
- Status publicare
- Status previzualizare
- Deja publicat
- Link rezervări activ

No empty “—” rows.

### 7. Conversion panel compact

The “— Conversie catalog —” block should be short:

— Conversie catalog —
Showcase: Publicat
Legătură ofertă–tur: Lipsește
Catalog: Nu este listat
Link rezervări: Lipsește
Client: Nu e rezervare online directă

Do not add generic verification bullets after every row.
At most one final line:
“Necesită verificare internă.”

### 8. Button text

Keep buttons short and Romanian:
- Flux ofertă
- Previzualizare
- OK poză
- Cere poză
- Pregătește
- Șablon
- Retrage
- Link rezervări
- Comenzi
- Cereri
- Cockpit
- Anterior
- Următor
- Înapoi
- Acasă

Do not use English button labels unless there is no Romanian translation.

## Tests

Update/add tests to assert:
- queue entries do not contain repeated “Necesită verificare internă”
- queue entries remain compact
- detail card begins with “Pe scurt”
- supplier block does not contain internal task wording
- conversion panel has at most one generic internal verification line
- no raw tokens leak:
  full_bus_private_group
  lifecycle
  review-package
  Admin API
  JSON
  C2B11
  admin_a6
  prepare_chain
  cta_safety
  execution_link
- button labels use Romanian keys where language_code is ro
- ISO date formatting is compact if dates are rendered

Run:
python -m compileall app tests
python -m pytest tests/unit/test_automation_cockpit_telegram.py tests/unit/test_operator_workflow_telegram_format.py tests/unit/test_supplier_offer_conversion_status_panel.py tests/unit/test_operator_workflow_c2b3_keyboard.py -q

## Deliverable

Report:
1. Files changed
2. Exact UX improvements
3. Safety confirmation
4. Test results
5. Any remaining known rough edges

Do not commit.
Do not push.