# HANDOFF_ADMIN_OPERATOR_WORKFLOW_READMODEL_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — Slice B

## Goal

Add a read-only `operator_workflow` section to:

GET /admin/supplier-offers/{offer_id}/review-package

## Purpose

The operator should not need to remember endpoint order.

The response should say:

- current workflow state
- primary next action
- available actions
- disabled reasons
- dangerous actions
- confirmation requirements
- endpoint hints

## Boundaries

This slice is read-only.

It must not:

- execute actions
- auto-publish
- auto-create Tour
- auto-activate catalog
- auto-create execution link
- call AI
- change booking/payment
- change Mini App UI
- add Telegram buttons
- add web UI
- add batch endpoints

## Expected next after Slice B

Possible next slices:

1. Telegram admin buttons consuming operator_workflow.
2. Minimal admin UI/console consuming operator_workflow.
3. Harder pre-publish content quality gate.
4. AI copy generation workflow with fact lock.

Do not start next slice automatically.