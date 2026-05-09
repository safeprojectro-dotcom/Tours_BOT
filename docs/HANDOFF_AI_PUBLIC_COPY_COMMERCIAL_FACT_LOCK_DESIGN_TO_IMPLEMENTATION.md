# HANDOFF_AI_PUBLIC_COPY_COMMERCIAL_FACT_LOCK_DESIGN_TO_IMPLEMENTATION

Project: Tours_BOT

## Functional block

AI PUBLIC COPY WITH COMMERCIAL FACT LOCK

## Problem

Supplier offers will eventually be processed by AI to produce better public copy.

Risk:
AI may change commercial facts:

- price
- currency
- dates/times
- route
- sales mode
- full_bus/per_seat meaning
- included/excluded services
- discounts/coupons
- capacity/seats
- payment/cancellation terms

If this reaches channel/Mini App, we can mislead customers and create operational/legal/reputation risk.

## Principle

AI is a copywriter and validator, not commercial source of truth.

AI may improve wording.
AI must not mutate facts.
Admin approves.
Facts stay from SupplierOffer/Tour/Layer A.

## Target safe model

Supplier raw facts
→ source_facts snapshot
→ AI public copy draft + fact_claims
→ fact_lock validator compares AI claims to source facts
→ blockers/warnings
→ admin review
→ approved public copy can be used only if fact_lock passed
→ final showcase/Mini App preview still uses source facts for factual lines

## Expected first implementation after design

Likely first slice:

- source_facts snapshot helper
- fact_lock validator
- ai_public_copy_review block in review-package
- tests for AI fact mismatch blockers
- no external AI call yet
- no publish source change yet

## Boundaries

Do not start implementation automatically.
Do not change booking/payment.
Do not change Tour bridge/catalog activation.
Do not make AI final publisher.
Do not use unapproved AI copy in public publish.