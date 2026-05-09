# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_READMODEL_SLICE_B

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN OPERATOR WORKFLOW — Slice B

Add a read-only `operator_workflow` section to:

GET /admin/supplier-offers/{offer_id}/review-package

---

## Context

Slice A created:

docs/ADMIN_OPERATOR_WORKFLOW.md

It defines the canonical admin/operator sequence:

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

Now Slice B should expose this sequence as a read-only admin workflow read model.

---

## Strict boundaries

Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not change publish behavior.
Do not change Tour bridge/catalog activation behavior.
Do not add migrations.
Do not call external AI.
Do not add Telegram buttons.
Do not add web UI.
Do not add batch/macro endpoints.
Do not execute any action from review-package.
Do not auto-publish.
Do not auto-create Tour.
Do not auto-activate catalog.
Do not auto-create execution link.

`operator_workflow` is read-only guidance only.

---

## Existing review-package sections

Reuse existing read-only sections:

- offer
- packaging_status
- lifecycle_status
- content_quality_review
- ai_public_copy_review
- showcase_preview
- bridge_readiness
- active_tour_bridge
- linked_tour_catalog
- execution_links_review
- mini_app_conversion_preview
- conversion_closure
- warnings
- recommended_next_actions

Do not duplicate business logic if existing fields already provide truth.

---

## Goal

Add a new response section:

```json
"operator_workflow": {
  "state": "ready_to_activate_catalog",
  "primary_next_action": "activate_tour_for_catalog",
  "actions": [
    {
      "code": "activate_tour_for_catalog",
      "label": "Activate Tour for Mini App catalog",
      "enabled": true,
      "danger_level": "conversion_enabling",
      "requires_confirmation": true,
      "method": "POST",
      "endpoint": "/admin/tours/{tour_id}/activate-for-catalog",
      "disabled_reason": null
    }
  ],
  "blocking_reasons": [],
  "warnings": []
}