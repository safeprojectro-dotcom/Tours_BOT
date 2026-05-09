# HANDOFF_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_CARD_POLISH_C1_1_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C1.1

## Goal

Make the Telegram admin operator workflow block compact and readable.

## What changes

The Telegram admin card still shows read-only operator_workflow, but in compact form:

- state
- next action
- risk/danger level
- confirmation flag
- warning count + warning codes
- blockers if any
- short read-only footer

## Boundaries

This slice remains display-only.

It must not:

- execute actions
- add publish/bridge/activate/link buttons
- call POST endpoints
- auto-publish
- auto-create Tour
- auto-activate catalog
- auto-create execution link
- change booking/payment
- change Mini App UI
- call AI

## Next possible slice

Slice C2:

Telegram action buttons consuming operator_workflow.actions.

Start only with low-risk actions and explicit confirmation.

Do not start C2 automatically.