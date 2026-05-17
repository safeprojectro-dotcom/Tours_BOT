
---

# HANDOFF

```md
# HANDOFF_A3B_CLARIFICATION_DRAFT_HUMANIZATION_FILTER

## Project
Tours_BOT

## Block
A3B — Clarification Draft Humanization & Hard Technical Filter

## Goal
Make supplier-facing clarification drafts safe and understandable for drivers, elderly people, and non-technical suppliers.

## Rule
Only whitelisted simple Romanian questions may appear in supplier-facing drafts.

## Forbidden supplier-facing terms
execution link, conversion chain, CTA, Mini App, blockers_count, prepare_chain, publish_readiness, content_quality, orphan_promo_code, description_thin, media_review_replacement_requested, B7/B10/B11/B15, snake_case/debug keys.

## Supplier draft style
- polite
- Romanian
- max 5 numbered questions
- no technical terms
- no English debug copy
- no sending

## Internal tasks
Technical platform problems are mapped to human-readable internal tasks and shown separately.

## Must not happen
No sending, no supplier notification, no Telegram publish, no scheduler, no DB, no writes, no AI, no Layer A, no B11.

## Manual UAT
Open supplier-offer card and confirm:
- supplier draft is simple
- internal tasks are separate
- no technical terms in supplier draft
- no Send button