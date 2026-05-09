# CURSOR_PROMPT_ADMIN_SUPPLIER_COVER_REPLACEMENT_PATH_C2B7_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design / safety policy step.

Do not change code.
Do not modify files unless explicitly asked after design approval.

---

## Functional block

ADMIN / SUPPLIER COVER REPLACEMENT PATH — C2B7

Design the safe path for actually replacing `cover_media_reference` after Telegram admin marks the photo as needing replacement.

---

## Context

Implemented and deployed:

### C2B4

Telegram admin `Preview` sends local photo + showcase caption to admin private chat.

### C2B5

Review-package/operator_workflow includes deterministic cover media quality warnings.

### C2B6

Telegram admin card includes one correction action:

- `Cere poză` / `Request photo`

Behavior:

- First tap = confirmation only.
- Confirm calls existing `SupplierOfferMediaReviewService.request_replacement`.
- Records `packaging_draft_json.media_review.status = replacement_requested`.
- Does not mutate `cover_media_reference`.
- Does not publish.
- Does not block publish.
- Does not add OK foto / Respinge foto / Schimbă foto.

Production smoke on offer #8 passed:

- Before action: `request_cover_photo_replacement.enabled = True`.
- After confirm:
  - `media_review.status = replacement_requested`;
  - `reviewed_by = telegram:{admin_id}`;
  - `cover_media_quality_review.has_warnings = True`;
  - `operator_workflow.warnings` includes media warning;
  - `request_cover_photo_replacement.enabled = False`;
  - Telegram button disappeared after refresh.

Problem now:

The system can mark “photo replacement requested”, but there is no clear, safe operator path to actually replace the wrong `cover_media_reference`.

---

## Problem

After `replacement_requested`, what should happen operationally?

Possible paths:

A. Supplier sends a new photo through existing supplier flow.
B. Central admin uses a new admin HTTP endpoint to set/replace `cover_media_reference`.
C. Telegram admin sends a new photo directly to the bot, and bot stores its Telegram `file_id` as `cover_media_reference`.
D. Ops uses manual DB/script for now, documented in runbook.
E. External storage/media pipeline handles it later.

Need decide MVP path.

---

## Hard boundaries

Do not implement code in this Plan step.
Do not publish to Telegram channel.
Do not add Telegram `Publică`.
Do not mutate booking/payment/order/reservation.
Do not change Mini App.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not implement external AI image validation.
Do not implement image generation.
Do not download media.
Do not implement full storage/media pipeline unless only as future design.
Do not add dangerous chained actions.

---

## Existing relevant model/services to inspect

Inspect and summarize:

- app/models/supplier.py
  - cover_media_reference
  - media_references
  - showcase_photo_url
  - packaging_draft_json
- app/services/supplier_offer_media_review_service.py
- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_cover_media_quality_review.py
- app/services/supplier_offer_review_package_service.py
- app/api/routes/admin.py
- app/api/routes/supplier_admin.py
- app/services/supplier_offer_service.py
- app/bot/handlers/supplier_offer_intake.py
- app/bot/handlers/admin_moderation.py
- app/bot/constants.py
- app/bot/messages.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/CHAT_HANDOFF.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- B7.1/B7.3 media docs if present

Use actual project structure if names differ.

---

## Questions to answer

### 1. Current ways to mutate cover media

List current ways, if any, to change `cover_media_reference`:

- supplier API;
- supplier Telegram intake;
- admin API;
- admin Telegram;
- direct DB/script only.

For each, list exact routes/services/handlers and limitations.

### 2. Source of truth

Confirm which field should be source of truth for showcase photo:

- `cover_media_reference`;
- `showcase_photo_url`;
- `media_references`;
- `packaging_draft_json.media_review.cover_media_reference`.

Recommend whether to keep `cover_media_reference` as single source for showcase.

### 3. Replacement path options

Analyze these options:

#### Option A — supplier replacement flow

Admin marks `replacement_requested`.
Supplier is asked to send new photo.
Supplier updates offer.
Admin previews again.
Admin approves media again.

Pros/cons.

#### Option B — central admin HTTP endpoint

Add a narrow endpoint later:

```text
PUT /admin/supplier-offers/{offer_id}/cover