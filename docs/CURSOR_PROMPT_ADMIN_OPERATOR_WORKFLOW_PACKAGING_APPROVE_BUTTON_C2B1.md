# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_PACKAGING_APPROVE_BUTTON_C2B1

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN OPERATOR WORKFLOW — C2B1

Telegram workflow mutation button:

approve_packaging_for_publish

with mandatory confirmation.

---

## Context

Already implemented and deployed:

- Slice B: GET /admin/supplier-offers/{offer_id}/review-package includes operator_workflow.
- Slice C1/C1.1: Telegram admin card displays compact operator_workflow.
- Slice C2A: Telegram admin card has read-only workflow buttons:
  - review_package_refresh
  - get_showcase_preview
- C2B design accepted:
  - next mutating Telegram workflow slice is packaging-only;
  - no duplicate moderation approve button;
  - legacy Aprobă / Respinge remain unchanged;
  - no bridge/catalog/publish/execution-link buttons yet.

## Strict boundaries

Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not change publish behavior.
Do not change Tour bridge/catalog activation behavior.
Do not add migrations.
Do not call external AI.
Do not add web UI.
Do not add batch/macro endpoints.
Do not auto-publish.
Do not auto-create Tour.
Do not auto-activate catalog.
Do not auto-create execution link.

Do not add Telegram buttons for:

- approve_offer_moderation
- create_tour_bridge
- activate_tour_for_catalog
- publish_showcase_channel
- create_execution_link

Do not duplicate legacy Aprobă / Respinge.

C2B1 scope is only:

```text
approve_packaging_for_publish