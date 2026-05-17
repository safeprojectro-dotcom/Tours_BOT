
---

# HANDOFF

```md
# HANDOFF_A3_MISSING_INFO_CLARIFICATION_DRAFTS

## Project
Tours_BOT

## Block
A3 — Missing Info Clarification Drafts + Supplier/Internal Task Split

## Mode
Functional-block mode.

## Goal
Generate read-only supplier clarification drafts from A2 validation while separating supplier-facing questions from internal platform/admin tasks.

## Key rule
Supplier-facing messages must be simple enough for drivers, elderly people, and non-technical supplier staff.

## Supplier-facing style
- short
- polite
- numbered
- one question per line
- max 5 questions
- no technical platform terms

## Internal-only terms
Never send these to supplier:
- execution link
- conversion chain
- exact-tour CTA
- blockers_count
- Mini App exact tour
- B7/B10/B11/B15
- internal gate codes
- prepare_conversion_chain

## Must not happen
- no sending
- no supplier notification
- no Telegram publish
- no scheduler
- no AI
- no migrations
- no writes
- no Layer A
- no B11

## Manual UAT
Open supplier-offer card in cockpit and confirm:
- Draft întrebare furnizor is simple
- Sarcini interne are separate
- no technical terms in supplier draft
- no Send button

## Next
A3B or A4 only after A3 draft quality is accepted.