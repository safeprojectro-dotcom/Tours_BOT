# HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN

Project: Tours_BOT

## Functional block

ADMIN / SUPPLIER COVER REPLACEMENT PATH — C2B7.2

## Why this exists

C2B6 lets admin mark a bad preview photo as needing replacement.

C2B7.1 lets admin replace `SupplierOffer.cover_media_reference` through:

PUT /admin/supplier-offers/{offer_id}/cover

But replacement is not approval.

After changing cover, the old `media_review` snapshot remains stale/replacement_requested until admin approves the new cover.

## Decision (resolved)

**Telegram + HTTP:** operators can complete step **6** either via **`POST /admin/supplier-offers/{offer_id}/media/approve-for-card`** (Admin API) or via Telegram **`OK poză` / `OK photo`** (same service: **`SupplierOfferMediaReviewService.approve_for_card`**).

## Current expected operational flow

1. Preview shows wrong photo.
2. `Cere poză`.
3. `media_review.status = replacement_requested`.
4. `PUT /admin/supplier-offers/{offer_id}/cover` with new reference.
5. Preview again.
6. Approve-for-card again: **HTTP** `POST …/media/approve-for-card` **or** Telegram **`OK poză` / `OK photo`** (confirm → re-read `review-package` → `approve_for_card`, `reviewed_by = telegram:{admin_id}`).
7. Warnings clear if snapshot matches current cover.

## Boundaries

No publish.
No Publică.
No auto-approve on PUT /cover.
No booking/payment/Mini App.
No bridge/catalog/execution-link.
No AI/image validation.
No storage pipeline.

## Implemented behavior (C2B7.2)

Telegram **`OK poză` / `OK photo`** when **`operator_workflow`** exposes **`approve_cover_for_card`** **`enabled`**:

- non-empty **`cover_media_reference`** that is Telegram-sendable for showcase (**`telegram_photo:{file_id}`** or **`https`** — same gate as C2B5-style preview);
- **not** already **`approved_for_card`** with **`media_review.cover_media_reference`** equal to current row cover;
- **C2B7.2a:** **`disabled`** when **`media_review.status`** ∈ **`replacement_requested`**, **`rejected_irrelevant`**, **`rejected_bad_quality`**, **`fallback_card_required`** **and** snapshot **`media_review.cover_media_reference`** equals current **`cover_media_reference`** (same bad hero — admin must **`PUT …/cover`** first)**;** **`enabled`** when snapshot **≠** current cover so operator can approve the new hero after replacement;
- propose → confirm → **re-read `review-package`** → execute only if action still **`enabled`**;
- **`approve_for_card`** only — no **`cover`** mutation, no lifecycle/publish/channel changes.

See **`app/bot/handlers/admin_moderation.py`** (handler **`admin_ops_operator_workflow_c2b7_2_ok_photo`**), **`app/services/supplier_offer_operator_workflow.py`** (**`approve_cover_for_card`**), **`approve_cover_for_card_operator_action_disabled_reasons`** in **`app/services/supplier_offer_cover_media_quality_review.py`**.