# HANDOFF_ADMIN_SUPPLIER_OFFER_COVER_REPLACEMENT_ENDPOINT_C2B7_1_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN / SUPPLIER COVER REPLACEMENT PATH — C2B7.1

## Goal

Add a narrow admin HTTP endpoint to replace `SupplierOffer.cover_media_reference`.

## Expected behavior

Endpoint:

- admin-auth only;
- updates only `SupplierOffer.cover_media_reference`;
- accepts `telegram_photo:{file_id}` or http(s) URL;
- does not publish;
- does not approve media automatically;
- does not change lifecycle;
- does not touch Tour/order/payment/Mini App.

After replacement:

- review-package reflects new cover reference;
- showcase preview uses new cover reference;
- previous media_review snapshot may become stale;
- C2B5 warnings should tell admin to re-preview and approve-for-card again.

## Important policy

Replacing cover is not the same as approving cover.

Admin flow:

1. `Cere poză` marks replacement_requested.
2. Admin/supplier obtains new cover reference.
3. Admin endpoint replaces cover_media_reference.
4. Admin Preview again.
5. Admin approve-for-card again.
6. Only later publish workflow.

## Boundaries

No Telegram upload.
No Publică.
No publish gate.
No auto-publish.
No storage/media pipeline.
No AI image validation.
No booking/payment/Mini App changes.

## Future possible slices

- Telegram admin upload flow using this service;
- supplier notification/request workflow;
- publish gate requiring current media approval;
- central admin UI for cover replacement.