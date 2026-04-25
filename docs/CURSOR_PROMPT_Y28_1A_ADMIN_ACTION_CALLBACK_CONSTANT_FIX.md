Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после Y28.1.

Нужен узкий bugfix без redesign.

## Observed live issue
Telegram admin workspace opens correctly.
Queue/detail render correctly.
Inline buttons render correctly.
Pressing `Aprobă` produces webhook hits and handled updates, but visually nothing changes and no moderation action is applied.

## Likely root cause
In `app/bot/handlers/admin_moderation.py`, action buttons are created using action constants:
- `ADMIN_OFFERS_ACTION_APPROVE`
- `ADMIN_OFFERS_ACTION_REJECT`
- `ADMIN_OFFERS_ACTION_PUBLISH`
- `ADMIN_OFFERS_ACTION_RETRACT`

But action dispatch in callback handler compares against hard-coded string literals like:
- `"approve"`
- `"reject"`
- `"publish"`
- `"retract"`

This likely causes silent no-op fallback when constant values do not exactly match those literals.

## Goal
Fix callback action dispatch to use the same constants that are used when building callback_data.

## Scope
Only narrow bugfix in admin moderation callback path.
Do not redesign workspace.
Do not change architecture.
Do not change lifecycle semantics.

## Required changes
1. In `app/bot/handlers/admin_moderation.py`, replace hard-coded action-name comparisons with the matching constants.
2. Make dispatch chain consistent (`if/elif/...`).
3. Ensure unknown action path gives explicit admin-visible feedback instead of silent no-op.
4. Keep approve != publish preserved.
5. Keep reject-reason flow unchanged except for correct dispatch.

## Required tests
Add/update focused tests proving:
1. approve callback using actual action constants executes approve path
2. publish callback using actual action constants executes publish path
3. retract callback using actual action constants executes retract path
4. reject callback using actual action constants enters reject-reason flow
5. unknown action gives explicit feedback instead of silent no-op

## After coding
Report exactly:
1. root cause confirmed
2. files changed
3. migrations none
4. tests run
5. results
6. what was fixed
7. compatibility notes