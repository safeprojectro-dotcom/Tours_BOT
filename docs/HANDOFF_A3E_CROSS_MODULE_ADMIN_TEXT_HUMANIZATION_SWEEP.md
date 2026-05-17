
---

# HANDOFF

```md
# HANDOFF_A3E_CROSS_MODULE_ADMIN_TEXT_HUMANIZATION_SWEEP

## Project
Tours_BOT

## Block
A3E — Cross-Module Admin Text Humanization Sweep

## Goal
Remove raw English/debug/internal text from admin-facing Telegram UI across cockpit and related admin modules.

## Scope
- Cockpit queue rows
- Cockpit card details
- Tour cards
- Supplier-offer cards
- Related admin moderation/admin Telegram text where raw codes leak

## Main rule
Admin UI must explain the operational meaning, not show internal implementation labels.

## Examples
- `Departure is in the past.` → `Data plecării este în trecut.`
- `Candidate for tour promotion / last-seats style posts (B15B does not send)` → `Candidat pentru promovare / postare „ultimele locuri”.`
- `prepare_chain` → `Pregătește lanțul catalog / rezervări.`
- unknown technical text → `Necesită verificare internă.`

## Must not happen
No sending, no supplier notification, no Telegram publish, no scheduler, no DB, no writes, no AI, no Layer A, no B11.

## Manual UAT
Open several queues and cards. Confirm:
- no raw English/debug text
- no B15B/B7/B10/B11
- internal tasks compact and unique
- supplier draft remains simple
- no dangerous buttons