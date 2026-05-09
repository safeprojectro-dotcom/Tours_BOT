# HANDOFF_ADMIN_OPERATOR_WORKFLOW_MUTATION_BUTTONS_CONFIRMATION_DESIGN_C2B

Project: Tours_BOT

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C2B Design

## Purpose

Telegram admin now shows operator workflow and has read-only workflow buttons.

Before adding mutation buttons, we must define confirmation and safety policy.

## Current state

Implemented:

- review-package operator_workflow read model
- Telegram compact operator workflow card
- read-only Telegram workflow buttons:
  - refresh review package
  - showcase preview

Existing legacy buttons:

- Aprobă
- Respinge

These are mutating and must be analyzed before new workflow mutation buttons are added.

## Design goals

Define:

- which safe_mutation actions are eligible for Telegram
- which actions are postponed
- confirmation UX
- stale-state protection
- no duplicate approve buttons
- tests for future implementation

## Hard boundaries

No C2B implementation should add:

- publish button
- activate catalog button
- execution link button
- batch workflow button
- auto actions
- booking/payment changes
- Mini App UI changes
- AI calls

## Expected next after design

One small implementation slice only, likely:

- confirmation wrapper for existing Aprobă / Respinge, or
- confirmation framework without new mutation buttons, or
- one low-risk workflow mutation action with confirmation.

Do not start implementation automatically.