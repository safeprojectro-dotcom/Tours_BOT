
---

# HANDOFF

```md
# HANDOFF_A3D_GLOBAL_QUEUE_AND_DETAIL_HUMANIZATION

## Project
Tours_BOT

## Block
A3D — Global Queue List + Detail Deduplication & Humanization

## Goal
Make cockpit queue rows and card details readable for non-technical admins across all card types.

## Scope
- Queue list rows
- Card detail screens
- Tour cards
- Supplier offer cards
- Marketing / publishing / catalog / conversion / missing info lanes

## Fixed classes of issues
- Raw English warnings in queue rows
- Tour card raw warnings
- B15B/B7/B10/B11 references in default admin UI
- Repeated internal tasks
- Overlong internal task lists

## Rules
- Humanize all blocker/warning/task text before display.
- Deduplicate internal tasks after humanization.
- Max 5 internal tasks.
- Unknown technical text becomes “Necesită verificare internă.”
- Supplier-facing drafts remain protected by A3B.

## Must not happen
No sending, no supplier notification, no Telegram publish, no scheduler, no DB, no writes, no AI, no Layer A, no B11.

## Manual UAT
Open multiple queues and multiple card types. Confirm:
- no raw English/debug text
- no B15B/raw internal references
- internal tasks are compact and unique
- supplier draft remains simple
- no dangerous buttons