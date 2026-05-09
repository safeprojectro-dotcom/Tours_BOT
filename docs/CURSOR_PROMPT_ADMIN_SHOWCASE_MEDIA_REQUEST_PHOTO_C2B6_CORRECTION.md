# CURSOR_PROMPT_ADMIN_SHOWCASE_MEDIA_REQUEST_PHOTO_C2B6_CORRECTION

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

## Context

C2B6 is currently implemented but has one important gap before commit.

Current behavior:
- operator_workflow exposes `request_cover_photo_replacement` when `cover_media_reference` is non-empty.
- It does not consider current `packaging_draft_json.media_review.status`.

Problem:
The action must NOT be enabled if media review already says the photo is not usable or replacement was already requested.

## Goal

Tighten C2B6 behavior before commit.

`request_cover_photo_replacement` must be enabled only if:

1. current offer has non-empty usable/current cover media reference, AND
2. media_review.status is NOT one of:
   - replacement_requested
   - rejected_irrelevant
   - rejected_bad_quality
   - fallback_card_required

If status is one of those, action should be disabled / hidden from Telegram keyboard through existing enabled-action filtering.

## Requirements

### 1. Read media_review.status

Use the existing `packaging_draft_json.media_review.status` structure.

Implement cleanly in the review-package/operator workflow path.

Preferred approach:
- In `supplier_offer_review_package_service.py`, extract current media_review status from the offer / existing review data.
- Pass a compact flag or status into `build_operator_workflow`.
- In `supplier_offer_operator_workflow.py`, use it to disable `request_cover_photo_replacement`.

Do not duplicate large parsing logic in Telegram handler.

### 2. Confirm handler safety

Confirm handler must continue to re-read `review_package`.

On confirm, it must execute only if `operator_workflow.actions` still has:

```text
code == request_cover_photo_replacement
enabled == true