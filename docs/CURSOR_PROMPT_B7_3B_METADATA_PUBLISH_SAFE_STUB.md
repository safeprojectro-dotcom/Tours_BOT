# CURSOR_PROMPT_B7_3B_METADATA_PUBLISH_SAFE_STUB

You are continuing the Tours_BOT project.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a small metadata-only implementation step.

Do not implement Telegram download.
Do not implement object storage / S3.
Do not implement local file storage.
Do not implement real card rendering.
Do not implement sendPhoto/sendMediaGroup.
Do not implement automatic publish.
Do not change Mini App UI.
Do not change booking/payment/order/reservation logic.

---

## Current checkpoint

B7.3A media pipeline policy acceptance is completed.

Latest commit:

- ed3b20f — docs: accept B7.3 media pipeline policy

Accepted B7.3A policy:

- raw supplier media is not publish-safe.
- Telegram file_id / telegram_photo:{file_id} is not a stable public URL.
- approved_for_card is not the same as publish_safe.
- publish_safe is not the same as published.
- publication remains a separate explicit admin action.
- Railway local filesystem must not be used as canonical durable storage.
- Durable publish-safe media should use future object storage/S3-compatible storage if/when download/storage is explicitly scoped.
- AI/card prompt/render preview JSON is metadata, not binary media.
- Fallback branded card may remain a placeholder/planned derived asset until renderer/storage exists.
- Mini App execution truth remains independent of marketing media.

B7 status:

- B7.1 media review metadata completed.
- B7.2 card render preview plan completed.
- B7.3A media policy accepted and documented.
- B7.3B is now the next small optional implementation slice.

B8 recurring supplier offers line is closed and must not be reopened.

---

## Source documents to read first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TESTING_STRATEGY.md

Also inspect current code:

- app/services/supplier_offer_media_review_service.py
- app/services/supplier_offer_card_render_preview.py
- app/models/supplier.py
- app/models/enums.py
- existing tests for supplier offer media review / card render preview if present

If some docs/tests do not exist, do not invent broad structures. Continue with available files.

---

## Goal

Add a metadata-only `publish_safe` stub to the existing Supplier Offer packaging/media metadata flow.

The goal is to make the accepted B7.3A policy explicit in data metadata, without implementing storage/download/render/publish.

This stub should answer:

- Is there a durable publish-safe media artifact now?
- If not, why not?
- What is the current source/reference?
- What future storage/download state is expected?

---

## Required behavior

### 1. Add metadata only

Extend `packaging_draft_json` media-related metadata with a small `publish_safe` object.

Recommended shape:

```json
{
  "publish_safe": {
    "status": "deferred",
    "reason": "no_durable_media_storage",
    "source_media_reference": "telegram_photo:<file_id>",
    "storage_kind": "none",
    "object_key": null,
    "public_url": null,
    "marked_at": "<iso timestamp>",
    "marked_by": "<admin/system identifier if available>"
  }
}