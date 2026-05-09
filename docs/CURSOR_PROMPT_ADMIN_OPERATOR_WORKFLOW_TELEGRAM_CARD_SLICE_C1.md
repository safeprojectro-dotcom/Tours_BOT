# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_CARD_SLICE_C1

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C1

Telegram admin review card shows operator_workflow.

---

## Context

Slice B is implemented and deployed.

`GET /admin/supplier-offers/{offer_id}/review-package` now includes read-only `operator_workflow`:

- state
- primary_next_action
- actions[]
- danger_level
- requires_confirmation
- endpoint hints
- blocking_reasons
- warnings

Production check on offer #11 showed:

```text
state = ready_to_publish_showcase
primary_next_action = publish_showcase_channel
warnings include:
- orphan_promo_code
- discount_deadline_without_value
- description_thin