# HANDOFF_ADMIN_OPERATOR_WORKFLOW_PACKAGING_APPROVE_BUTTON_C2B1_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — C2B1

## Goal

Add one Telegram workflow mutation button:

approve_packaging_for_publish

## Rules

The button appears only when operator_workflow.actions has approve_packaging_for_publish enabled.

First tap only opens confirmation.

Confirm:

- re-reads review-package;
- verifies action is still enabled;
- executes only packaging approval;
- refreshes card.

Cancel:

- no mutation.

## Hard boundaries

C2B1 must not add:

- approve_offer_moderation workflow button
- create_tour_bridge button
- activate_tour_for_catalog button
- publish_showcase_channel button
- create_execution_link button
- batch workflow action

Legacy Aprobă / Respinge remain unchanged.

## Next possible slices

1. generate_packaging_draft button with confirmation.
2. legacy moderation consolidation.
3. create_tour_bridge only in a later conversion-action slice.
4. public/dangerous publish only in a later double-confirmation slice.

Do not start next slice automatically.