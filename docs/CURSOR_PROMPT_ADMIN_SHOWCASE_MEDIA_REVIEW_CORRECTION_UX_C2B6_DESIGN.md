# CURSOR_PROMPT_ADMIN_SHOWCASE_MEDIA_REVIEW_CORRECTION_UX_C2B6_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design / safety policy step.

Do not change code.
Do not modify files unless explicitly asked after design approval.

---

## Functional block

ADMIN SHOWCASE MEDIA REVIEW — C2B6

Correction UX after visual preview.

---

## Context

Implemented and deployed:

- C2B4: Telegram admin `Preview` sends local photo + showcase caption to admin private chat.
- C2B5: review-package/operator_workflow now includes deterministic cover media quality warnings.
- Production check on offer #8:
  - `cover_media_reference` exists and is sendable.
  - `media_review.status = approved_for_card`.
  - `media_review.cover_media_reference` matches current `cover_media_reference`.
  - Therefore `cover_media_quality_review.has_warnings = false`.

But manual visual preview showed the cover image is semantically wrong:

- offer is a tour “Дорога в дюны”;
- cover image is breakfast/coffee;
- deterministic guard cannot know this is irrelevant;
- previous media approval was technically valid but operationally wrong.

Therefore we need an admin correction UX after visual preview.

---

## Problem

The system can detect technical media problems, stale review snapshots, rejected statuses, and missing media.

But it cannot deterministically detect semantic mismatch:

- image is valid;
- image sends correctly;
- media review is approved;
- snapshot matches;
- yet the image is wrong for the tour.

Admin needs a safe way to mark:

- photo is not suitable;
- replacement is needed;
- current approval should no longer be trusted.

---

## Hard boundaries

Do not implement code in this Plan step.
Do not add publish button.
Do not publish to Telegram channel.
Do not mutate booking/payment/order/reservation.
Do not change Mini App.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not add migrations in this design step.
Do not implement AI image relevance scoring.
Do not implement storage/media pipeline.
Do not download images.
Do not generate images.

---

## Existing relevant model/services to inspect

Inspect and summarize:

- app/services/supplier_offer_media_review_service.py
- SupplierOfferMediaReviewStatus enum in app/models/enums.py
- packaging_draft_json.media_review structure
- admin media review routes in app/api/routes/admin.py
- Telegram admin moderation handlers in app/bot/handlers/admin_moderation.py
- review-package/operator_workflow integrations from C2B5
- docs related to B7.1 / B7.3 / media review / publish-safe
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/ADMIN_OPERATOR_WORKFLOW.md

---

## Questions to answer

### 1. Current correction options

What can an admin/operator do today if the preview photo is wrong?

Analyze existing endpoints/actions:

- media reject
- request replacement
- fallback card
- approve for card
- supplier update flows
- direct correction paths, if any

List exact route/service names and whether they are available from Telegram, Admin API, or supplier API.

### 2. Which media status should represent “photo is wrong”?

Choose the best existing status for this scenario:

- rejected_irrelevant
- replacement_requested
- fallback_card_required
- rejected_bad_quality

Explain the difference.

Example:
- If photo is irrelevant but supplier should send a better one → replacement_requested?
- If photo is clearly bad and should not be used → rejected_irrelevant?
- If no replacement needed and text/card fallback acceptable → fallback_card_required?

Recommend product semantics.

### 3. Telegram UX options

Evaluate possible Telegram buttons after Preview:

Option A:
- no Telegram buttons; Admin API only.

Option B:
- one safe button: `Cere poză` / `Request photo`
- marks media_review as replacement_requested.

Option C:
- one safe button: `Respinge foto` / `Reject photo`
- marks rejected_irrelevant.

Option D:
- two buttons:
  - `OK foto`
  - `Cere poză`
  
Option E:
- three buttons:
  - `OK foto`
  - `Respinge foto`
  - `Cere poză`

Analyze risk, clutter, and operator clarity.

### 4. Confirmation policy

If a Telegram correction button is added later:

- should it require confirmation?
- should it re-read review-package?
- should it check current cover_media_reference?
- should it include current media_review.status?
- should it allow typed reason?
- should it use default reason if no text?

Recommend minimum safe UX.

### 5. Effect of marking photo wrong

Define what happens after correction:

- media_review.status becomes what?
- reason is stored where?
- reviewed_by uses telegram:{admin_id}?
- reviewed_at updated?
- cover_media_reference snapshot stored?
- review-package shows C2B5 warning?
- operator_workflow warnings show warning?
- preview still shows current photo or text-only?
- publish remains unchanged in this slice?

### 6. Should publish be blocked?

For now, should `POST publish` be blocked if media_review is rejected/replacement_requested?

Choices:

A. No, keep publish unchanged; warnings only.
B. Block only photo_with_caption, allow text_only.
C. Hard block all publish until media fixed.
D. Defer hard gate until Telegram `Publică`.

Recommend MVP rule.

### 7. Should there be `OK foto` now?

Since existing `approved_for_card` already exists, do we need Telegram `OK foto`?

Analyze:

- value of explicit OK after Preview;
- risk of extra button clutter;
- whether existing Admin API approve_for_card is sufficient;
- whether future Publică requires fresh approval.

Recommend whether to defer `OK foto`.

### 8. Reason capture

If admin marks photo wrong, should we require a reason?

Options:

- fixed default reason: “Marked from Telegram preview as not suitable”
- inline confirm with no reason
- ask for text reason in FSM
- choose reason buttons: irrelevant / bad quality / replacement needed

Recommend MVP.

### 9. Recommended next implementation slice

Pick smallest safe slice:

Option 1:
- Docs-only runbook: if photo wrong, use existing Admin API media rejection/replacement endpoint.

Option 2:
- Telegram one-button correction:
  - `Cere poză`
  - confirmation
  - calls existing media review service/request replacement
  - no publish gate.

Option 3:
- Telegram two-button correction:
  - `Respinge foto`
  - `Cere poză`

Option 4:
- Add central admin HTTP route first if missing.

Option 5:
- Hard publish gate.

Choose one.

### 10. Tests needed

List tests for the chosen future implementation.

---

## Required output

Return exactly:

1. Current correction options
2. Status semantics recommendation
3. Telegram UX option analysis
4. Confirmation policy
5. Effect after correction
6. Publish blocking recommendation
7. OK foto recommendation
8. Reason capture recommendation
9. Recommended next implementation slice
10. Tests needed
11. Files likely affected later
12. Risks/open questions
13. Recommended next prompt name

Do not change files.