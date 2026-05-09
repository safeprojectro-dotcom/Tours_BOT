# CURSOR_PROMPT_PRODUCTION_E2E_WALKTHROUGH_POINTERS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync.

Не менять app/.
Не менять tests/.
Не менять alembic/.
Не менять mini_app/.
Не менять runtime code.

## Context

Created:

docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md

It documents dry-run/live smoke modes for the full operator path:

Supplier Offer
→ review-package
→ packaging approval
→ moderation approval
→ tour bridge
→ catalog activation
→ Mini App catalog
→ showcase preview/publish
→ execution link
→ supplier offer landing
→ bot deep link exact Tour

Mode B was not executed because no safe staging/prod credentials and OFFER_ID were provided.

## Goal

Add short pointers to the walkthrough doc in the existing control docs.

Update only:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required notes

Add concise notes:

1. `PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md` created.
2. It is a smoke procedure, not new functionality.
3. It supports dry-run and live execution modes.
4. Live mutating calls require explicit safe OFFER_ID / staging or test channel confirmation.
5. Mode B was not executed yet.
6. Next decision depends on real smoke result.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Pointers added
3. Confirmation docs-only