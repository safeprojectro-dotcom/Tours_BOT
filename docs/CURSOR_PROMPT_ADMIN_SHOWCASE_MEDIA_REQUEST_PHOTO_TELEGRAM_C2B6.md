# CURSOR_PROMPT_ADMIN_SHOWCASE_MEDIA_REQUEST_PHOTO_TELEGRAM_C2B6

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN SHOWCASE MEDIA REVIEW — C2B6

Telegram single-button media correction:

`Cere poză` / `Request photo`

This marks current cover media as needing replacement after admin visually checks Preview.

---

## Context

Implemented and deployed:

- C2B4: Telegram admin Preview sends local photo + showcase caption to admin private chat.
- C2B5: review-package/operator_workflow includes deterministic cover media quality warnings.
- Production check on offer #8:
  - cover_media_reference exists;
  - media_review.status = approved_for_card;
  - media_review snapshot matches current cover;
  - cover_media_quality_review.has_warnings = false.
- Human visual check showed photo can still be semantically wrong.
- C2B6 design accepted:
  - do not add OK foto now;
  - do not add Respinge foto now;
  - add only one safe correction action: `Cere poză`;
  - it should call existing request_replacement media review service;
  - no publish gate;
  - no media mutation;
  - no DB migration.

---

## Strict boundaries

Do not publish to Telegram channel.
Do not add Telegram `Publică`.
Do not add OK foto.
Do not add Respinge foto.
Do not add Schimbă foto.
Do not mutate cover_media_reference.
Do not add admin PATCH cover endpoint.
Do not add DB migration.
Do not change booking/payment/order/reservation.
Do not change Mini App.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not call external AI.
Do not download images.
Do not generate images.
Do not implement storage/media pipeline.
Do not change publish behavior.
Do not block publish in this slice.

This slice only adds a Telegram admin correction action that records media replacement request.

---

## Source files to inspect

Inspect:

- app/bot/constants.py
- app/bot/handlers/admin_moderation.py
- app/bot/messages.py
- app/services/supplier_offer_media_review_service.py
- app/services/supplier_offer_cover_media_quality_review.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_operator_workflow.py
- app/models/enums.py
- app/schemas/supplier_admin.py
- app/api/routes/admin.py
- tests/unit/test_supplier_offer_cover_media_quality_review.py
- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_operator_workflow_c2a_specs.py
- tests/unit/test_operator_workflow_c2b3_keyboard.py
- tests/unit/test_telegram_admin_moderation_y281.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Use actual project structure if names differ.

---

## Goal

Add one Telegram admin button:

RO:

```text
Cere poză