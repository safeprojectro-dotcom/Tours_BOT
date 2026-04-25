Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Telegram admin moderation workspace v1 already implemented
- current `docs/TELEGRAM_ADMIN_MODERATION_WORKSPACE_DESIGN.md`
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не добавлять admin content editing.
Не делать broad admin portal rewrite.

## Goal
Expand Telegram admin visibility so admin can access not only `ready_for_moderation` queue, but also:
- approved / unpublished supplier offers
- published supplier offers

## Current problem to solve
Current `/admin_ops`, `/admin_offers`, `/admin_queue` behave as moderation queue only.
After approve or retract, offers disappear from Telegram admin visibility because they are no longer in `ready_for_moderation`.

This is a narrow operational visibility gap, not a lifecycle redesign.

## Exact scope

### 1. Preserve existing moderation queue
Keep current moderation queue behavior for:
- `ready_for_moderation`

Do not break existing `/admin_queue`.

### 2. Add approved/unpublished visibility
Add a narrow admin Telegram surface for offers that are:
- approved
- not currently published

Recommended command:
- `/admin_approved`

### 3. Add published visibility
Add a narrow admin Telegram surface for offers that are:
- published

Recommended command:
- `/admin_published`

### 4. Workspace behavior
For both new surfaces, keep the same narrow workspace model:
- queue/list
- detail card
- prev / next / back / home
- state-valid action buttons only

### 5. Valid action availability
Keep action availability state-driven:
- approved/unpublished: publish allowed
- published: retract allowed
- ready_for_moderation: approve / reject allowed

Do not redesign lifecycle.
Preserve approve != publish.

### 6. UX consistency
Reuse the same admin Telegram UX style:
- same navigation model
- same detail rendering style
- explicit feedback
- explicit empty-state messages

## What this step must NOT do
Do NOT:
- edit supplier content
- add scheduled publish
- add mass moderation
- add supplier profile moderation here
- add payment/order admin controls
- add analytics/finance surfaces
- redesign moderation lifecycle

## Likely files
Likely:
- `app/bot/handlers/admin_moderation.py`
- `app/bot/app.py`
- `app/bot/constants.py`
- `app/bot/messages.py`
- focused admin moderation tests

Avoid unrelated files.

## Before coding
Output briefly:
1. current state
2. why Y28.2 is needed
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. `/admin_queue` still shows ready_for_moderation only
2. `/admin_approved` shows approved/unpublished offers
3. `/admin_published` shows published offers
4. publish action is available only in approved/unpublished view
5. retract action is available only in published view
6. approve/reject remain unchanged in moderation queue
7. no lifecycle redesign introduced

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin can now see/do
6. what remains postponed
7. compatibility notes

## Important note
This is a narrow Telegram admin visibility expansion only.
Do not silently expand into editing, scheduling, supplier profile moderation, or broader admin portal replacement.