Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- `docs/SUPPLIER_ADMIN_MODERATION_AND_STATUS_POLICY_DESIGN.md` accepted
- Y29.2 supplier profile status model implemented
- production migration for Y29.2 already applied
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не смешивать supplier profile moderation with supplier offer moderation.
Не реализовывать supplier offer auto retract/blocking policy в этом шаге.

## Goal
Implement Telegram admin supplier moderation workspace as a narrow operational client for supplier profiles.

## Accepted design truth
Supplier profile moderation is separate from supplier offer moderation.

Supplier profile actions should use supplier-governance terms:
- approve
- reject with reason
- suspend
- reactivate
- revoke

Do NOT use publish/retract vocabulary for supplier profiles.

## Exact scope

### 1. Telegram admin entry points
Implement narrow commands:
- `/admin_suppliers`
- `/admin_supplier_queue`

Use the same fail-closed Telegram admin allowlist model already used by Telegram admin workspaces.

### 2. Supplier queue/read surfaces
Implement narrow Telegram admin views for supplier profiles:
- pending_review queue
- approved view only if needed for suspend/revoke/reactivate operational flow
- suspended/revoked visibility only if narrowly required for current actions

Keep it narrow and operational.
Do not build a broad admin CRM.

### 3. Supplier detail card
Render a supplier detail card with enough moderation context:
- supplier display name
- primary Telegram user id if available
- onboarding/profile status
- legal/compliance identity summary if already available
- current reason fields where relevant

### 4. Supplier admin actions
Wire action buttons to existing supplier governance truth:
- approve
- reject with reason
- suspend
- reactivate
- revoke

Only expose actions valid for the current state.

### 5. Navigation
Implement:
- prev
- next
- back
- home

Reuse existing mobile-first Telegram admin interaction style.

### 6. Reject/suspend/revoke reason capture
Add narrow reason capture flow where needed.
Keep it deterministic and simple.

### 7. Feedback / idempotency UX
Return clear admin feedback:
- approved
- rejected
- suspended
- reactivated
- revoked
- action unavailable in current state

Do not allow silent no-op.

## What this step must NOT do
Do NOT:
- implement supplier-offer cascading retract/blocking
- implement supplier status gating integration across supplier/offer bot surfaces
- redesign onboarding fields
- redesign legal model broadly
- add RBAC/org redesign
- add analytics/finance dashboard
- merge supplier profile workspace with offer workspace

## Likely files
Likely:
- `app/bot/handlers/admin_supplier_moderation.py` (new)
- `app/bot/app.py`
- `app/bot/state.py`
- `app/bot/constants.py`
- `app/bot/messages.py`
- maybe small schema/service touch only if necessary
- focused tests

Avoid unrelated files.

## Before coding
Output briefly:
1. current state
2. why Y29.3 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. allowlisted admin can open supplier queue
2. pending supplier can be approved
3. pending supplier can be rejected with reason
4. approved supplier can be suspended
5. suspended supplier can be reactivated
6. approved or suspended supplier can be revoked if allowed
7. invalid action/state combinations show explicit feedback
8. no offer-moderation semantics are mixed into supplier workspace

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin can now do for supplier profiles in Telegram
6. what remains postponed
7. compatibility notes

## Important note
This is Telegram admin supplier moderation workspace only.
Do not implement supplier offer auto retract/block policy in this step.