
---

# HANDOFF

```md
# HANDOFF_A2_SUPPLIER_INTAKE_AUTO_VALIDATION

## Project
Tours_BOT

## Block
A2 — Supplier Intake Auto-Validation

## Mode
Functional-block mode.

## Goal
Add a read-only supplier-offer validation layer that automatically detects missing/weak supplier facts and exposes them to the Admin Automation Cockpit.

## Scope
Read-only validation of supplier offer facts:
- route/destination
- date/recurrence
- price/currency
- capacity
- sales mode
- program
- included/excluded
- photo
- discount/coupon terms
- packaging/governance status

## Expected outcome
Admin can open the cockpit and see:
- incomplete supplier offers
- missing facts
- blockers
- warnings
- recommended next action
- clarification topics

## Must not happen
- migrations
- write endpoints
- supplier offer mutation
- tour/order/payment/reservation mutation
- Telegram publish/send
- supplier notification send
- scheduler
- QR
- Layer A changes
- B11 changes
- AI execution
- external provider calls

## Manual UAT
1. Open /admin_cockpit.
2. Open 📥 Intake furnizor.
3. Open ⚠️ Lipsă informații.
4. Open supplier-offer card.
5. Confirm missing facts and recommended next step are visible.
6. Confirm no send/publish/action buttons exist.

## Next
A3 — Missing Info Auto-Clarification Drafts, but only after A2 validation is stable.