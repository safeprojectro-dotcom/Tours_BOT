
---

# HANDOFF

```md
# HANDOFF_A3E_CAP_INTERNAL_TASKS_TO_5_CORRECTION

## Goal
Correct A3E Telegram detail rendering so internal tasks are capped at 5 visible items.

## Reason
A3E report showed cap 8, but product requirement is max 5 to avoid long admin cards.

## Rules
- max 5 internal tasks
- overflow note after 5
- dedupe after humanization
- no raw debug text
- supplier-facing draft unchanged

## No-go
No DB, no writes, no sends, no AI, no Layer A, no B11.