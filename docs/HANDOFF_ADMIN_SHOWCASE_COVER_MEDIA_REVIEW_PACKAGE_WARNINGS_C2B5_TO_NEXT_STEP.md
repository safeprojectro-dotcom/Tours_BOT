# HANDOFF_ADMIN_SHOWCASE_COVER_MEDIA_REVIEW_PACKAGE_WARNINGS_C2B5_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN SHOWCASE MEDIA QUALITY — C2B5

## Goal

Add read-only deterministic cover media quality warnings to review-package/operator_workflow.

## Why

C2B4 local preview shows the actual media. Manual smoke proved this works, but also showed a possible wrong-cover case.

## Allowed

- Add read-only media quality review helper.
- Add review-package field.
- Add concise warnings to operator_workflow.
- Add tests.
- Update docs.

## Not allowed

- No publish gate.
- No Publică button.
- No OK foto / Schimbă foto buttons.
- No media mutation.
- No DB migration.
- No AI image validation.
- No storage/media pipeline.
- No booking/payment/Mini App changes.

## Expected warning examples

- cover_media_missing
- media_review_snapshot_stale
- media_review_not_approved
- media_review_rejected_or_replacement_requested
- showcase_photo_url_ignored_or_inconsistent

## Future

Possible later slices:

- admin media review confirmation UX;
- central admin cover update route;
- publish hard gate requiring media approval;
- AI-assisted image relevance as advisory only.