# HANDOFF_B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE

## Project
Tours_BOT

## Block
B17 — Channel / Template Editor Design Gate

## Goal

Define the future Channel / Template Editor architecture before any implementation.

## Scope

Design / documentation only.

## Expected result

A design document that defines:

- channel model
- template model
- editor workflow states
- action taxonomy
- confirmation/audit/idempotency requirements
- future data/API sketches
- frontend UX guidance
- future rollout order

## Must not happen in B17

- runtime code changes
- schema changes
- service changes
- API route changes
- tests changes
- migration
- Telegram publish/send/retry
- scheduler
- auto-publish
- public side effects
- frontend implementation

## Relationship to B15

B17 builds on the closed B15 Publishing Console Foundation:

- publish_readiness
- console_preview
- template_library
- preview_payload
- ui_card
- supplier-offer detail read view
- guarded prepare_conversion_chain actions

B17 must not replace or bypass B15 safety boundaries.

## Recommended next after B17

Conservative next:

- B17A — read-only editor detail view
- or B17B — channel/template selection metadata only

Do not jump directly to Telegram publish implementation without explicit go/no-go.