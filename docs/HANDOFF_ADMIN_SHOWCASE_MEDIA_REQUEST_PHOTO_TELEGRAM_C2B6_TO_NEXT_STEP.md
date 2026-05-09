# HANDOFF_ADMIN_SHOWCASE_MEDIA_REQUEST_PHOTO_TELEGRAM_C2B6_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN SHOWCASE MEDIA REVIEW — C2B6

## Goal

Add one Telegram admin correction action after visual Preview:

- `Cere poză` / `Request photo`

## Behavior

First tap:

- confirmation only;
- no mutation.

Confirm:

- re-read current state;
- verify usable photo still exists;
- verify media is not already replacement/rejected/fallback;
- call existing SupplierOfferMediaReviewService.request_replacement;
- reviewed_by = telegram:{admin_id};
- fixed non-empty reason;
- commit;
- refresh card if practical.

Cancel:

- no mutation.

## Important

This does not change the photo.
This does not publish.
This does not block publish.
This does not mutate cover_media_reference.
This does not add OK foto / Respinge foto / Schimbă foto.

After success, C2B5 warnings should surface replacement_requested.

## Boundaries

No publish button.
No bridge/catalog/execution-link.
No Mini App changes.
No booking/payment changes.
No AI image validation.
No storage/media pipeline.
No migration.

## Future possible slices

- central admin cover replacement route;
- supplier notification/request flow;
- media approval gate before Telegram Publică;
- optional AI relevance advisory.