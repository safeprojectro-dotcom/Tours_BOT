# CURSOR_PROMPT_ADMIN_SHOWCASE_COVER_MEDIA_QUALITY_GUARD_DESIGN

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design / safety policy step.

Do not change code.
Do not modify files unless explicitly asked after design approval.

---

## Functional block

ADMIN SHOWCASE MEDIA QUALITY — Cover mismatch guard

---

## Context

Implemented and deployed:

- C2B4: Telegram admin Preview now shows local media parity:
  - sends photo to admin private chat when a usable Telegram file_id / media reference exists;
  - sends the showcase caption;
  - does not publish to channel;
  - does not mutate lifecycle / published_at / showcase ids.

Manual smoke showed the mechanism works.

But the smoke exposed a product/ops issue:

- Offer #8 preview displayed a breakfast/coffee image while the offer is a tour “Дорога в дюны”.
- Technically preview is correct because it shows the current `cover_media_reference`.
- Product-wise this is dangerous: admin may publish an offer with a wrong/mismatched cover image.

Therefore before any future `Publică` Telegram button, we need a cover media quality / mismatch policy.

---

## Problem

Admin now sees the final-like visual, but the system has no explicit media quality state such as:

- cover image missing
- cover image present but probably irrelevant
- cover image accepted by admin
- cover image rejected / needs replacement
- preview seen/confirmed

Current fields may include:

- cover_media_reference
- media_references
- showcase_photo_url / send arg
- packaging_status
- lifecycle_status
- publish_safe metadata stub if present from B7.3

Need determine what is already available and what minimal next slice should be.

---

## Hard boundaries

Do not design auto-publish.
Do not design channel publishing button.
Do not mutate booking/payment/order/reservation.
Do not change Mini App execution truth.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not implement external AI image analysis in this step.
Do not implement storage/media pipeline in this step.
Do not implement image generation.
Do not download images.

This is a design step only.

---

## Questions to answer

### 1. Current media model

Inspect and summarize the current model/service fields related to supplier offer media:

- SupplierOffer.cover_media_reference
- SupplierOffer.media_references
- showcase_photo_url / send arg
- any publish_safe/media_review/card_render_preview fields
- B7.3 docs / media pipeline docs if present
- current admin endpoints for cover update if any

List exact files/classes/functions.

### 2. Current preview/publish behavior

Explain current behavior:

- what Preview uses now after C2B4;
- what future publish would use;
- whether Preview and publish share the same media source;
- where mismatch can occur;
- whether there is any current admin confirmation that image is correct.

### 3. Risk classification

Classify image problems:

- missing cover image
- wrong image / irrelevant image
- low quality image
- supplier-provided but misleading image
- image exists but not publish-safe
- image too generic
- image outdated after offer details changed
- image is technically invalid / Telegram cannot send it

For each, recommend: blocking / warning / advisory.

### 4. Minimal state model

Recommend whether we need new DB state now, or can start with read-only warnings.

Options:

A. No DB changes:
- review-package detects cover_media_reference present/missing;
- operator_workflow warnings say “review cover image manually”;
- Preview displays media;
- publish still human-controlled.

B. Add admin media review state:
- media_review_status: none / needs_review / approved / rejected
- media_reviewed_at / media_reviewed_by / rejection_reason
- optional media_review_snapshot_hash tied to cover_media_reference

C. Use existing packaging_status / packaging_draft_json subtree:
- store media_review under packaging_draft_json or publish_safe metadata
- no migration but less clean

Choose the safest MVP option and explain why.

### 5. Admin workflow

Design the operator flow:

- admin opens review-package
- admin presses Preview
- admin sees photo + caption
- if image wrong:
  - what can admin do today?
  - what should future UX provide?
- if image correct:
  - should admin explicitly mark image as approved?
- should `Publică` later require image approval?

### 6. Button UX

Do we need Telegram buttons now?

Possible future buttons:

- `OK foto`
- `Schimbă foto`
- `Fără foto`
- `Respinge foto`

Analyze if these should be added now or postponed.

Given our current safe workflow, recommend smallest next implementation slice.

### 7. Publish safety rule

Define a future rule for publish:

- publish can proceed if no photo and text_only mode?
- publish can proceed with photo only if preview was generated?
- publish can proceed with photo only if media approved?
- public_dangerous Telegram publish button later must require what?

Tie this back to `ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`.

### 8. AI / semantic image matching

Should AI image validation be used later?

Analyze:

- optional future AI image relevance check;
- risks of relying on AI;
- deterministic checks that can be done first;
- why admin human preview remains source of approval.

No implementation now.

### 9. Recommended next implementation slice

Pick one:

A. Docs-only media quality runbook.
B. Read-only cover media warning in review-package/operator_workflow.
C. Add explicit media_review_status DB state.
D. Telegram buttons for OK foto / Schimbă foto.
E. Publish hard gate requiring media approval.

Choose the smallest safe next step.

### 10. Tests needed later

List tests for the chosen implementation.

---

## Required output

Return exactly:

1. Current media model
2. Current preview/publish behavior
3. Risk classification
4. Recommended state model
5. Admin workflow proposal
6. Telegram button recommendation
7. Future publish safety rule
8. AI/media validation stance
9. Recommended next implementation slice
10. Tests needed
11. Files likely affected later
12. Risks/open questions
13. Recommended next prompt name

Do not change files.