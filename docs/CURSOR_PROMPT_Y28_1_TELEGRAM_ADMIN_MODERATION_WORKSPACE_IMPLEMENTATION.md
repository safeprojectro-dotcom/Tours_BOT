Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- `docs/TELEGRAM_ADMIN_MODERATION_WORKSPACE_DESIGN.md` accepted
- current `docs/CHAT_HANDOFF.md`
- supplier moderation/publication lifecycle already implemented
- supplier Telegram flows already implemented
- supplier execution linkage persistence already implemented

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не делать broad admin portal rewrite.
Не добавлять admin content editing.

## Goal
Implement Telegram admin moderation workspace v1 as a narrow operational layer over the existing admin/service truth.

## Accepted product/ops rule
Admin does NOT edit supplier-authored content.
Admin only:
- reviews
- approves
- rejects / returns for rework with reason
- publishes
- retracts

Supplier remains content author and must resubmit after rework.

## Exact scope

### 1. Admin Telegram access gate
Implement a fail-closed Telegram admin allowlist gate.
Only allowlisted Telegram user IDs may access admin Telegram workspace commands.

Use the narrowest safe config-backed approach for v1.

### 2. Entry commands
Implement narrow commands:
- `/admin_ops`
- `/admin_offers`

Optional alias only if trivial and safe:
- `/admin_queue`

Keep command surface narrow.

### 3. Queue read-side
Implement Telegram admin queue/list for supplier offers using existing backend/service truth.
Prefer the narrowest useful queue, for example:
- ready_for_moderation
- optionally approved / published views only if already safe and simple

Do not build a broad admin dashboard.

### 4. Offer detail view
Implement one-offer detail card/view with:
- supplier identity summary
- offer title / summary
- lifecycle status
- publication status
- reject reason where relevant
- enough moderation context for admin action

### 5. Admin actions
Wire action buttons to existing backend/service truth only:
- approve
- reject with reason
- publish
- retract

Preserve:
- approve != publish
- no direct content editing
- no lifecycle redesign

### 6. Reject reason capture
Implement narrow reject / rework reason capture in Telegram flow.
Keep it simple and deterministic.

### 7. Navigation
Implement:
- next
- prev
- back
- home

Keep mobile-first and workspace-oriented.

### 8. Feedback / idempotency UX
Return clear admin-facing confirmations:
- approved
- rejected
- published
- retracted
- action unavailable in current state

Do not create duplicate/confusing action loops.

## What this step must NOT do
Do NOT:
- edit supplier content
- add scheduled publish
- add mass moderation
- add RFQ admin Telegram workspace
- add order/payment admin controls
- add analytics/finance surfaces
- redesign supplier lifecycle
- replace existing admin API/service truth

## Likely files
Likely:
- `app/bot/handlers/admin_moderation.py` (new)
- `app/bot/app.py`
- `app/bot/state.py`
- `app/bot/messages.py`
- maybe a small admin Telegram access helper/service
- focused tests

Avoid touching unrelated subsystems.

## Before coding
Output briefly:
1. current state
2. why Y28.1 is the next safe step
3. exact files likely to change
4. risks
5. what remains postponed

## Required tests
Add focused tests for:
1. non-allowlisted Telegram user is denied
2. allowlisted admin can open queue
3. admin can approve from allowed state
4. admin can reject with reason
5. admin can publish only from valid state
6. admin can retract only from valid state
7. approve/publish remain separate
8. no admin content editing path exists

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin can now do in Telegram
6. what remains postponed
7. compatibility notes

## Important note
This is a narrow Telegram admin moderation workspace v1.
Do not silently expand into editing, scheduling, RFQ admin workspace, or broader portal replacement.