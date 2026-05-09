# HANDOFF_ADMIN_OPERATOR_WORKFLOW_PLAYBOOK_TO_OPERATOR_WORKFLOW_READMODEL

Project: Tours_BOT

## Functional block

ADMIN UX / OPERATOR WORKFLOW

## Slice A result

Canonical docs-only playbook:

docs/ADMIN_OPERATOR_WORKFLOW.md

## Purpose

The operator workflow is currently fragmented across many endpoints.

The playbook defines the canonical path:

review-package
→ content quality / AI fact lock review
→ packaging
→ moderation
→ tour bridge
→ catalog activation
→ catalog verification
→ showcase preview
→ publish
→ execution link
→ landing/bot verification

## Critical principles

- Always start with review-package.
- review-package is read-only.
- No auto-publish.
- No auto-bridge.
- No auto-catalog activation.
- No auto-execution-link.
- No AI final publisher.
- No booking/payment mutation from review flow.

## Next code slice

ADMIN OPERATOR WORKFLOW Slice B:

Add read-only `operator_workflow` section to:

GET /admin/supplier-offers/{offer_id}/review-package

Expected fields:

- state
- primary_next_action
- actions[]
- danger / requires_confirmation flags
- endpoint hints
- disabled reasons
- no action execution

No Telegram buttons yet.
No web UI yet.
No batch actions.