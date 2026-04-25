Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- supplier Telegram onboarding/intake/workspace already implemented
- supplier moderation/publication lifecycle already implemented
- supplier execution linkage persistence already implemented
- current `docs/CHAT_HANDOFF.md`

Это design-only block.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать hidden implementation.

## Goal
Define a coherent Telegram admin moderation/publication workspace v1 as a narrow operational layer on top of the existing admin/service truth.

This is a single design block intended to accelerate later implementation safely.

## Product rule already accepted
The admin must NOT edit supplier-authored content.

Accepted moderation model:
- supplier creates/submits content
- admin reviews it
- admin may approve/publish
- admin may reject / return for rework with reason
- supplier corrects and resubmits
- admin reviews again

Admin is moderator/publisher, not content editor.

## Why this block exists
Supplier-side Telegram flows are already operational.
Admin moderation/publication backend capabilities already exist.
The next natural surface is a Telegram admin ops workspace for mobile-first moderation work.

## Design scope for this block
Define Telegram admin workspace v1 including:

### 1. Admin identity / access model
Decide the safest v1 access model for Telegram admin workspace.
Prefer narrow explicit access such as:
- allowlisted Telegram user IDs
- or another very narrow bound admin identity model

Must be explicit and fail-closed.

### 2. Entry points
Define the recommended admin Telegram commands / entry points, for example:
- `/admin_ops`
- `/admin_offers`

Keep command set narrow.

### 3. Workspace structure
Define the admin workspace interaction model:
- moderation queue/list
- offer detail card/view
- navigation (next/back/home)
- action buttons

Prefer a narrow live workspace model similar in spirit to supplier read-side, but admin-specific.

### 4. Offer moderation actions
Define exactly which actions admin may perform in Telegram v1:
- approve
- reject / return for rework with reason
- publish
- retract

Clarify whether approve and publish remain separate in Telegram as they already are in backend truth.

### 5. Supplier rework loop
Define how "return for rework" should work operationally:
- what supplier sees
- what reason/note is captured
- how supplier resubmits
- how admin re-reviews

Be explicit whether current lifecycle should reuse `rejected + reason` or whether a future `changes_requested` state is only a possible later refinement.

Do not silently redesign lifecycle in this step.

### 6. Read-side data admin sees
Define what admin can see in Telegram moderation workspace:
- supplier identity summary
- offer title/content summary
- lifecycle status
- publication status
- timestamps
- maybe narrow operational linkage summary if already relevant

Do not over-expand into full admin portal replacement.

### 7. What admin must NOT do in Telegram v1
Explicitly prohibit:
- editing supplier content
- editing supplier legal data
- editing commercial truth directly
- payment/order control expansion
- analytics dashboard expansion
- customer data expansion beyond what is already explicitly allowed elsewhere

### 8. Publication behavior
Reinforce:
- approve != publish remains preserved
- publish remains explicit
- retract remains explicit
- publication must still go through existing publication truth/service path
- Telegram workspace is only an operational client layer

### 9. Future-but-postponed items
Explicitly postpone:
- scheduled publish
- content editing
- mass moderation actions
- RFQ admin workspace
- order/payment admin controls
- analytics/finance dashboard
- richer portal replacement

## Required design output
Produce a narrow design recommendation that includes:
1. access model
2. command model
3. queue/detail/navigation model
4. moderation action model
5. supplier rework loop
6. read-side boundaries
7. postponed items
8. recommended narrow implementation sequence

## Constraints
Do NOT:
- implement code
- redesign supplier lifecycle broadly
- change Layer A booking/payment semantics
- change RFQ/bridge semantics
- propose a broad new admin platform
- propose admin content editing
- merge unrelated admin concerns into this block

## Preferred files
Create/update only narrow docs, for example:
- `docs/TELEGRAM_ADMIN_MODERATION_WORKSPACE_DESIGN.md`
- minimal `docs/CHAT_HANDOFF.md` mention only if truly needed

## Before coding
Output briefly:
1. current state
2. why doing this as one design block is safe/useful
3. artifacts to inspect
4. risks if implementation starts without this design gate

## After coding
Report exactly:
1. files changed
2. code changes none
3. migrations none
4. design recommendation summary
5. safest implementation sequence
6. postponed items

## Important note
This is a design-only block.
Do not implement the workspace in this step.