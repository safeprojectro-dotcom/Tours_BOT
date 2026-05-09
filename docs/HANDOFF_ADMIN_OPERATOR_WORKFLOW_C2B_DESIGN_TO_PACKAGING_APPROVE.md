# HANDOFF_ADMIN_OPERATOR_WORKFLOW_C2B_DESIGN_TO_PACKAGING_APPROVE

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — C2B Design → C2B1

## Decision

Next implementation slice is packaging-only:

- approve_packaging_for_publish from operator_workflow.actions
- only when enabled
- mandatory confirmation
- re-read review-package before execution
- execute exactly one action
- no chained actions

## Do not implement yet

- approve_offer_moderation workflow button
- create_tour_bridge
- activate_tour_for_catalog
- create_execution_link
- publish_showcase_channel
- batch workflow

## Legacy moderation

Existing Aprobă / Respinge remain unchanged for now.

Do not add a duplicate approve_offer_moderation button until a separate legacy-consolidation slice.

## Next code slice

CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_PACKAGING_APPROVE_BUTTON_C2B1.md