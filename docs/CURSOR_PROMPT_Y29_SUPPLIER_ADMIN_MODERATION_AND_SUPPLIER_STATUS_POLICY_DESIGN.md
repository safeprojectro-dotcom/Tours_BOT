Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- supplier Telegram onboarding already implemented
- supplier legal/compliance hardening already implemented
- supplier offer intake/workspace/moderation/publication already implemented
- Telegram admin offer moderation workspace already implemented
- current `docs/CHAT_HANDOFF.md`
- current `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Это design-only step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать hidden implementation.

## Goal
Design the next safe supplier-governance layer consisting of:
1. supplier onboarding Telegram navigation polish needs
2. Telegram admin supplier moderation workspace (for supplier profiles, not offers)
3. supplier suspension/revoke policy and its effect on supplier offers/public visibility

## Critical architecture rule
Do NOT mix:
- supplier profile lifecycle
with
- supplier offer lifecycle

These are separate domains and must remain separate.

Supplier profile moderation is about whether the supplier entity is allowed to operate on the platform.
Supplier offer moderation/publication is about whether a specific supplier offer is allowed to appear in public/admin surfaces.

## Product questions to resolve in design

### 1. Supplier onboarding Telegram navigation
Current supplier onboarding in `/supplier` lacks safe step navigation for correction.
Design whether `/supplier` should gain:
- `Înapoi`
- `Acasă`

Define:
- safe step-back semantics
- safe cancel/home semantics
- how FSM should behave
- whether already-entered draft onboarding data is preserved while stepping back
- whether home clears current onboarding FSM state fully

Keep this narrow and aligned with the already accepted `/supplier_offer` navigation pattern.

### 2. Supplier profile moderation in Telegram
Design a narrow Telegram admin workspace for moderating supplier profiles, separate from offer moderation.

Define recommended v1 entry points, e.g.:
- `/admin_suppliers`
- `/admin_supplier_queue`

Define workspace model:
- supplier moderation queue
- supplier detail card
- navigation
- actions

Initial moderation states should cover at minimum:
- pending_review suppliers
- approved suppliers
- rejected suppliers where useful for audit/read-side visibility

### 3. Supplier admin actions
Define which actions admin should have for supplier profile moderation.

Recommended action families to evaluate:
- approve
- reject with reason
- suspend
- reactivate / reinstate
- revoke (only if semantically distinct from suspend)

Important:
Do NOT use offer-oriented terms like publish/retract for supplier profiles.
Those belong to supplier offers, not supplier entities.

### 4. Supplier status policy and operational effects
Design what operational consequences should happen when a supplier is:
- approved
- rejected
- suspended
- reactivated
- revoked (if kept as distinct concept)

Must define policy for:
- supplier onboarding access
- `/supplier`
- `/supplier_offer`
- `/supplier_offers`
- already existing draft offers
- ready_for_moderation offers
- approved/unpublished offers
- published offers
- bot/public visibility
- Telegram channel visibility

### 5. Important rule for supplier exclusion
The user explicitly wants:
if a supplier is excluded/revoked, supplier offers should be removed from active bot/channel visibility.

Design the safest model for this without breaking architecture.

Strong preference:
- no physical delete
- no loss of audit/history
- use policy-driven deactivation/suspension/revocation
- published offers should be operationally retracted
- approved but unpublished offers should become blocked from publication
- drafts/history should remain retained unless there is a very strong reason otherwise

### 6. Relationship between supplier moderation and offer moderation
Design how supplier profile status should gate offer behavior.

Examples to resolve:
- can a suspended supplier create new offers?
- can a suspended supplier edit existing drafts?
- can admin publish an approved offer belonging to a suspended supplier?
- should retract of published offers happen automatically on suspend/revoke?
- should reactivation restore prior offers automatically, or remain manual?

### 7. Backward compatibility and current-state migration stance
Current approved suppliers may predate stricter legal/compliance or later status-policy additions.

Design must explicitly discuss:
- backward compatibility
- safest additive approach
- how not to break current working supplier domain

## Constraints
Do NOT:
- implement code
- redesign Layer A booking/payment flows
- redesign RFQ/bridge/payment-entry/reconciliation semantics
- merge supplier moderation with offer moderation
- silently introduce destructive delete behavior
- silently redefine existing approved supplier semantics without explicit migration/policy reasoning

## Required design output
Produce a narrow design recommendation covering:
1. supplier onboarding navigation polish recommendation
2. supplier Telegram admin moderation workspace recommendation
3. supplier profile lifecycle recommendation
4. operational consequences of each supplier status
5. effect on supplier offers and public visibility
6. safest implementation sequence
7. postponed items / non-goals

## Preferred files
Prefer creating:
- `docs/SUPPLIER_ADMIN_MODERATION_AND_STATUS_POLICY_DESIGN.md`

Update continuity docs only if narrowly justified.

## Before coding
Output briefly:
1. current state
2. why this design gate is needed before implementation
3. artifacts to inspect
4. main risks if implementation starts without this design step

## After coding
Report exactly:
1. files changed
2. code changes none
3. migrations none
4. design recommendation summary
5. safest implementation sequence
6. postponed items
7. compatibility notes

## Important note
This is design-only.
Do not implement supplier navigation buttons, supplier moderation Telegram workspace, or supplier suspend/revoke policy in this step.