# CURSOR_PROMPT_ADMIN_SHOWCASE_COVER_MEDIA_REVIEW_PACKAGE_WARNINGS_C2B5

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN SHOWCASE MEDIA QUALITY — C2B5

Read-only cover media warnings in review-package / operator_workflow.

---

## Context

Implemented:

- C2B4: Telegram admin Preview now sends local photo + showcase caption to admin private chat.
- Preview uses the same showcase builder/media source as future channel publish.
- Manual smoke showed C2B4 works.
- Product issue discovered: offer #8 showed a breakfast/coffee image for a tour, which means media parity works but cover quality/mismatch can be operationally wrong.

Accepted C2B5 design direction:

- Do not add Telegram media mutation buttons now.
- Do not add OK foto / Schimbă foto now.
- Do not add publish hard gate now.
- Do not add DB migration now.
- Start with read-only deterministic warnings surfaced in review-package/operator_workflow.
- Use existing B7.1 media_review JSON when present.
- Human preview remains source of semantic truth.

---

## Strict boundaries

Do not publish to Telegram channel.
Do not add Telegram `Publică`.
Do not add OK foto / Schimbă foto buttons.
Do not mutate supplier offer media.
Do not add admin PATCH cover endpoint.
Do not add migration.
Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not call external AI.
Do not download images.
Do not implement storage/media pipeline.
Do not block publish behavior in this slice.

This slice is read-only warnings only.

---

## Source files to inspect

Inspect:

- app/models/supplier.py
- app/models/enums.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_operator_workflow.py
- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_media_review_service.py
- app/services/supplier_offer_publish_safe_stub.py
- app/services/supplier_offer_moderation_service.py
- app/schemas/supplier_admin.py
- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_operator_workflow_telegram_format.py
- tests/unit/test_operator_workflow_c2b3_keyboard.py
- tests/unit/test_supplier_offer_showcase_ro.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Use actual project structure if names differ.

---

## Goal

Add deterministic read-only media quality warnings to the admin review-package and operator workflow.

Warnings should help admin notice:

1. There is no usable cover media for showcase preview/publish.
2. There is media review data, but it refers to a different cover than the current `cover_media_reference`.
3. There is a rejected/request-replacement/fallback media review state.
4. There is a possible source-of-truth inconsistency around `showcase_photo_url` vs `cover_media_reference` if relevant.
5. There is technically usable media, but no explicit admin media review approval yet.

Do not attempt AI semantic matching.

---

## Implementation requirements

### 1. Add a small deterministic media quality review helper

Create or extend a service, for example:

```text
app/services/supplier_offer_cover_media_quality_review.py