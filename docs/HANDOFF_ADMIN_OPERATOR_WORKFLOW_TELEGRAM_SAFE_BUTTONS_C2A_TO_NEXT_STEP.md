# HANDOFF_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_SAFE_BUTTONS_C2A_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C2A

## Goal

Telegram admin card starts consuming operator_workflow.actions for safe/read-only buttons only.

## Allowed in C2A

- refresh workflow/review-package
- show workflow details
- show showcase preview read-only if safe

## Explicitly not allowed in C2A

No Telegram buttons for:

- publish_showcase_channel
- activate_tour_for_catalog
- create_execution_link
- create_tour_bridge
- approve packaging/moderation unless already existing legacy buttons handle them

## Boundaries

C2A must not:

- execute public/dangerous actions
- execute conversion-enabling actions
- auto-publish
- auto-create Tour
- auto-activate catalog
- auto-create execution link
- change booking/payment
- change Mini App UI
- call AI

## Next possible slices

C2B:
low-risk mutation buttons with explicit confirmation.

C2C:
public/dangerous actions with separate double-confirmation policy.

Do not start C2B/C2C automatically.