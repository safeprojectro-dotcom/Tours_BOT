# CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_READINESS_GATE_C2B8A

You continue Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN SHOWCASE PUBLISH — C2B8A

Implement publish readiness gating in operator_workflow/read-package before adding Telegram `Publică`.

---

## Problem

C2B8 design inspection found that `publish_showcase_channel` already exists in `build_operator_workflow`.

Current behavior:

- action code: `publish_showcase_channel`
- danger_level: `public_dangerous`
- requires_confirmation: true
- enabled if:
  - lifecycle == APPROVED
  - showcase_preview.can_publish_now

But `showcase_preview.can_publish_now` is technical readiness only and does not block on C2B5 media warnings.

This is unsafe before Telegram public publishing.

Example risk:

- media_review.status = replacement_requested
- media_review.cover_media_reference == offer.cover_media_reference
- cover_media_quality_review.has_warnings = True

In this case, `Publică` must not be enabled.

---

## Goal

Make `publish_showcase_channel` action respect hard publish readiness blockers in the read-model/operator_workflow.

This slice does NOT add Telegram button.

It only fixes the workflow/readiness gate so future Telegram button cannot expose unsafe publish.

---

## Boundaries

Do not add Telegram `Publică` button.

Do not add callbacks.

Do not change Telegram handlers.

Do not publish anything.

Do not call `SupplierOfferModerationService.publish`.

Do not change POST `/admin/supplier-offers/{offer_id}/publish` behavior unless absolutely required and explicitly justified.

Do not touch Mini App.

Do not touch booking/payment/orders.

Do not create Tour.

Do not activate catalog.

Do not create execution links.

Do not add storage pipeline.

Do not add AI validation.

No migrations.

---

## Required publish readiness policy

For `publish_showcase_channel` in operator_workflow:

### Must remain disabled if:

1. lifecycle is not APPROVED.
2. showcase_preview.can_publish_now is false.
3. offer is already published, if current code exposes this state.
4. packaging is not approved for publish.
5. current publish mode would use a photo and cover media is not approved/aligned.
6. cover_media_quality_review has hard media warnings.

Hard media blockers include at least:

- media_review_replacement_requested
- media_review_rejected_bad_quality
- media_review_rejected_irrelevant
- media_review_fallback_card_required
- media_review_cover_snapshot_mismatch
- cover_media_not_explicitly_approved_for_card
- cover_media_not_sendable_for_showcase
- showcase_photo_url / cover_media_reference conflict if it can affect publish trust

Use exact existing warning codes from `supplier_offer_cover_media_quality_review.py`.

### Allowed / advisory warnings for now:

Do not block publish only because of general content quality warnings like:

- orphan_promo_code
- discount_deadline_without_value
- description_thin

Unless existing product policy already treats them as blockers.

### Text-only rule

If there is no `cover_media_reference` and publication mode is text-only:

- keep it allowed if current product policy allows text-only publishing;
- surface warnings, but do not block only because there is no photo.

If current code treats missing photo differently, report actual behavior and preserve it unless safety requires blocking.

---

## Implementation guidance

Likely files:

- app/services/supplier_offer_operator_workflow.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_cover_media_quality_review.py
- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_supplier_offer_cover_media_quality_review.py
- docs/CHAT_HANDOFF.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Prefer passing existing `cover_media_quality_review` into the publish action gating, rather than reparsing JSON in many places.

If a helper is needed, create a small deterministic helper such as:

```text
cover_media_publish_blocking_reasons(...)