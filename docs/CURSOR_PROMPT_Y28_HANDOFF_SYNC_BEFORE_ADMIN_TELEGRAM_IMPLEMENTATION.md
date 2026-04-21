Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- supplier Telegram onboarding/intake/workspace already implemented
- supplier moderation/publication lifecycle already implemented
- supplier execution linkage persistence already implemented
- `docs/TELEGRAM_ADMIN_MODERATION_WORKSPACE_DESIGN.md` completed and accepted
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать hidden implementation.

## Goal
Synchronize continuity/handoff docs before Y28.1 Telegram admin moderation workspace implementation.

## What must be reflected

### 1. Current supplier/admin scope
Document that the current accepted supplier/admin surface now includes:
- supplier onboarding
- legal/compliance hardening for pending supplier approval
- supplier offer intake
- moderation/publication lifecycle
- retract path
- supplier workspace
- narrow operational visibility
- narrow operational alerts
- authoritative execution linkage persistence for supplier offers
- admin link/unlink offer -> execution tour
- supplier booking-derived aggregate metrics only when active authoritative link exists

### 2. Current accepted Telegram admin design truth
Document that Telegram admin moderation workspace design has now been accepted.

Accepted rule:
- admin does NOT edit supplier-authored content
- supplier remains content author
- admin acts only as moderator/publisher

Accepted Telegram admin workspace v1 scope:
- fail-closed allowlisted Telegram admin IDs
- narrow entry commands:
  - `/admin_ops`
  - `/admin_offers`
  - optional alias `/admin_queue` only if trivial
- workspace model:
  - queue -> detail -> actions
- navigation:
  - prev / next / back / home
- actions v1:
  - approve
  - reject with reason
  - publish
  - retract
- approve != publish remains preserved
- supplier rework loop uses current `rejected + reason` model in v1
- no lifecycle redesign

### 3. Current Telegram admin boundaries
Document clearly that Telegram admin workspace v1 must NOT include:
- content editing
- legal/commercial truth editing
- scheduled publish
- mass moderation
- RFQ admin workspace
- payment/order admin controls
- analytics/finance dashboard
- broad portal replacement
- broad RBAC redesign

### 4. Architecture boundaries preserved
Reinforce:
- no Layer A booking/payment redesign
- no RFQ/bridge redesign
- no payment-entry/reconciliation redesign
- no supplier content editing by admin
- Telegram admin workspace is only an operational client over existing backend/service truth

### 5. Exact next safe step
Set next safe step to:
- `Y28.1 — Telegram admin moderation workspace implementation`

Implementation scope should be described narrowly as:
- allowlist gate
- `/admin_ops`
- `/admin_offers`
- queue read-side
- detail card/view
- approve / reject with reason / publish / retract
- prev / next / back / home
- clear admin feedback
- no editing path

### 6. Postponed items
Explicitly keep postponed:
- scheduled publish
- admin content editing
- mass moderation
- RFQ admin Telegram workspace
- order/payment admin controls
- analytics/finance dashboard
- broad portal replacement / RBAC redesign

## Files to update
Prefer only:
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if narrowly justified

Do not mass-edit historical prompts.

## Before coding
Output briefly:
1. current continuity state
2. why sync is needed now
3. files to update
4. what remains postponed

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests not run (docs-only)
4. what was synchronized
5. next safe step
6. postponed items

## Important note
This is docs sync only.
Do not implement Y28.1 in this step.