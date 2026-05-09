# CURSOR_PROMPT_ADMIN_SUPPLIER_OFFER_COVER_REPLACEMENT_ENDPOINT_C2B7_1

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN / SUPPLIER COVER REPLACEMENT PATH — C2B7.1

Add a narrow central admin HTTP endpoint to replace `SupplierOffer.cover_media_reference`.

---

## Context

Implemented and deployed:

### C2B4
Telegram admin Preview sends local photo + showcase caption to admin private chat.

### C2B5
Review-package/operator_workflow includes deterministic cover media quality warnings.

### C2B6
Telegram admin `Cere poză` / `Request photo` records:

- `packaging_draft_json.media_review.status = replacement_requested`
- reviewed_by = `telegram:{admin_id}`
- no cover mutation
- no publish mutation

Production smoke passed:

- replacement_requested recorded;
- C2B5 warning surfaced;
- `request_cover_photo_replacement.enabled = False`.

### C2B7 design accepted

Current gap:

- system can mark “photo replacement requested”;
- but there is no central admin product path to actually replace `SupplierOffer.cover_media_reference`.

Design decision:

- keep `SupplierOffer.cover_media_reference` as the single operational source of truth for showcase photo;
- do not use `showcase_photo_url` as live showcase source;
- media_review.cover_media_reference remains audit snapshot only;
- next safe product fix is a narrow admin endpoint to replace cover reference.

---

## Strict boundaries

Do not publish to Telegram channel.
Do not add Telegram `Publică`.
Do not add Telegram upload flow.
Do not add OK foto / Respinge foto / Schimbă foto.
Do not mutate booking/payment/order/reservation.
Do not change Mini App.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not call external AI.
Do not download images.
Do not generate images.
Do not implement storage/media pipeline.
Do not add DB migration unless absolutely necessary.
Do not change publish behavior.
Do not block publish.
Do not modify Tour cover endpoint.

This slice only adds a narrow central admin endpoint/service to set `SupplierOffer.cover_media_reference`.

---

## Source files to inspect

Inspect:

- app/api/routes/admin.py
- app/api/admin_auth.py
- app/models/supplier.py
- app/models/enums.py
- app/schemas/supplier_admin.py
- app/services/supplier_offer_service.py
- app/services/supplier_offer_media_review_service.py
- app/services/supplier_offer_cover_media_quality_review.py
- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_review_package_service.py
- app/repositories/supplier_offer.py or equivalent repository if present
- tests/unit/test_supplier_offer_cover_media_quality_review.py
- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_supplier_offer_showcase_ro.py
- tests/unit/test_supplier_offer_track3_moderation.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Use actual project structure if names differ.

---

## Goal

Add an admin-only endpoint, for example:

```text
PUT /admin/supplier-offers/{offer_id}/cover