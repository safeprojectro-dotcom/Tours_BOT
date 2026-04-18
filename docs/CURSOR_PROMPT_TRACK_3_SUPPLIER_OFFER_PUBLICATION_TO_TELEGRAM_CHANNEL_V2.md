Implement **Track 3 — Supplier Offer Publication To Telegram Channel** on top of the accepted supplier marketplace foundation.

## Preconditions already completed
- Track 0 completed: frozen core documented in `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- Track 1 completed: design package aligned and accepted
- Track 2 completed and accepted: Supplier Admin Foundation now exists
- current Layer A customer flows must remain stable

## Critical rule
This track must remain an additive publication/moderation layer.

It must not:
- replace the current customer catalog
- bypass platform moderation
- allow suppliers to post directly into the client-facing Telegram surface
- break current Mini App/private bot flows
- broaden into request marketplace logic

## Mandatory documents to respect
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`
- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`

## Goal
Implement the first moderated publication pipeline that allows supplier-created offers to move from supplier-admin into platform-reviewed publication and then into the Telegram offer showcase.

## Required scope

### A. Publication lifecycle
Support a narrow supplier-offer publication lifecycle such as:
- draft
- ready_for_moderation
- approved
- rejected
- published

If Track 2 already introduced part of this lifecycle, extend it minimally rather than redesigning it.

### B. Platform moderation/approval
Allow central admin/platform admin to:
- review supplier offers
- approve for publication
- reject / send back for correction
- list publication-ready / approved / rejected supplier offers

### C. Telegram publication integration
Support publication to the client-facing Telegram showcase.

Preferred assumptions:
- Telegram channel is the primary showcase
- linked discussion group remains conceptually separate
- this track should publish into the showcase layer only

### D. CTA continuity
Published offers must include a controlled path into:
- private bot
- Mini App
- existing deep-link or route assumptions where already safe

Do not invent unsupported booking behaviors.

### E. Minimal publication payload shaping
Add only the minimum needed formatting/payload shaping to publish supplier offers consistently.

Do not build a large AI content-generation system here.
Do not rebuild the broader content assistant in this track.

## Strong constraints
Do not implement:
- request marketplace / RFQ
- supplier bidding/response flows
- direct whole-bus self-service booking
- new payment execution logic
- unrestricted supplier direct posting
- broad redesign of content assistant
- broad redesign of group bot logic
- broad redesign of publication architecture beyond the minimum needed for supplier-offer publication

## Must-not-break rules
You must explicitly preserve:
- current per-seat booking semantics
- current payment semantics
- current reservation timer semantics
- current Mini App routes and stable expectations
- current private bot routes and CTA behavior
- current assisted full-bus path
- current sales_mode semantics for core tours
- current admin auth boundary
- migrate → deploy → smoke discipline

## Migration rule
Migrations are allowed only if actually necessary for publication state or publication records.
If you add a migration:
- keep it minimal
- explain why it is necessary
- preserve backward compatibility
- avoid schema churn

## Testing scope
Add focused tests for:
- publication state transitions
- moderation approval/rejection
- publication payload generation
- CTA/deep-link continuity
- no regression in current Mini App/private bot/customer-facing flows
- no unauthorized supplier bypass of platform moderation

## Before coding
First summarize:
1. how Track 3 builds on Track 2
2. exact files/modules you plan to touch
3. whether migrations are needed
4. what remains explicitly postponed after Track 3

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. publication behavior now supported
6. compatibility notes against Track 0 and Track 2
7. postponed items