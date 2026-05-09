# HANDOFF_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_CARD_SLICE_C1_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C1

## Goal

Telegram admin review card displays read-only `operator_workflow` guidance from review-package.

## What should be shown

- workflow state
- primary next action
- up to 3 warnings
- up to 3 blockers
- public/dangerous action note

## Boundaries

Slice C1 is display-only.

It must not:

- execute actions
- add publish/bridge/activate/link buttons
- auto-publish
- auto-create Tour
- auto-activate catalog
- auto-create execution link
- change booking/payment
- change Mini App UI
- call AI

## Next possible slice

Slice C2:

Telegram admin action buttons consuming `operator_workflow.actions`, starting only with low-risk actions and explicit confirmation.

Do not start C2 automatically.