
---

# HANDOFF

```md
# HANDOFF_A3C_GLOBAL_ADMIN_CARD_READABILITY_CLEANUP

## Project
Tours_BOT

## Block
A3C — Global Admin Card Readability Cleanup

## Goal
Make all Telegram cockpit card detail screens readable for non-technical external admins.

## Scope
Global Telegram cockpit card detail rendering:
- supplier offer cards
- tour cards
- missing info
- risk/conflict
- marketing review
- publishing
- catalog/conversion

## Rules
Default card detail must not show raw debug/platform strings:
- prepare_chain
- cta_safety
- publish_readiness
- gate
- content_quality
- media_review_replacement_requested
- blockers_count
- B7/B10/B11/B15
- snake_case/debug keys

## Required output
- human-readable main blocker
- human-readable warning
- simple supplier draft if available
- separate human-readable internal tasks
- compact useful commercial context
- short Romanian fact-lock
- safety checklist retained

## Must not happen
No sending, no supplier notification, no Telegram publish, no scheduler, no DB, no writes, no AI, no Layer A, no B11.

## Manual UAT
Open several card types and confirm:
- no raw debug text
- no long English fact-lock
- no empty commercial rows
- supplier draft remains simple
- no dangerous buttons