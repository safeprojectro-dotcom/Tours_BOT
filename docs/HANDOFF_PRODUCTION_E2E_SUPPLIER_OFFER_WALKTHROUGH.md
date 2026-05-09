# HANDOFF_PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH

Project: Tours_BOT

## Purpose

This handoff follows:

- Core catalog conversion closure
- BUSINESS-plan-v2 audit after core conversion

The next step is a production/staging smoke walkthrough using a real or safe test Supplier Offer.

## Goal

Verify the complete operator path:

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
→ Layer A remains unchanged

## Safety

- Do not run mutating production calls without explicit safe OFFER_ID and confirmation.
- Prefer test/sandbox offer/channel.
- Do not create real payment.
- Do not alter booking/payment code.
- Do not add functionality in this step.

## Checklist artifact

**Done:** [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md) — Mode **A** (dry-run / commands) and Mode **B** (live staging/prod), canonical gate order, **`conversion_closure`** pass criteria, **`NOT RUN`** rule.

**Still open:** An operator must **run** the checklist against a safe **`OFFER_ID`** (staging preferred) and fill the run log. The repo cannot substitute for infra credentials or Telegram verification.

## Next decision

After an **executed** walkthrough (checklist + logged results):

- PASS → choose admin UX or AI public copy block.
- FAIL → next block is the concrete blocker.