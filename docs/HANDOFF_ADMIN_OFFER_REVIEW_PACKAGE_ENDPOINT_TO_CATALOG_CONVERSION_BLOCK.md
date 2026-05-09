# HANDOFF_ADMIN_OFFER_REVIEW_PACKAGE_ENDPOINT_TO_CATALOG_CONVERSION_BLOCK

Project: Tours_BOT

## Completed block

ADMIN OFFER REVIEW & APPROVAL GATE — Slice 1

Expected implementation:

GET /admin/supplier-offers/{offer_id}/review-package

Purpose:
Admin gets a single read-only package before deciding the next business action.

## Must remain true

- Review package is read-only.
- It does not call Telegram.
- It does not publish.
- It does not create/link Tour.
- It does not activate catalog.
- It does not create execution link.
- It does not affect booking/payment.
- It does not collapse packaging approval with moderation lifecycle.
- It does not collapse channel publish with Mini App bookability.

## What it should expose

- raw supplier/admin offer snapshot
- packaging status
- moderation lifecycle status
- showcase preview
- bridge readiness
- active bridge / linked Tour
- catalog activation readiness
- execution link status
- validation booleans
- recommended next actions

## Next functional block

SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE

Goal:
After admin review/approval, close the business process:

approved supplier offer
→ create/link Tour
→ activate Tour for Mini App central catalog
→ active execution link
→ supplier offer landing / bot deep link routes to exact Tour
→ Mini App catalog shows Tour
→ booking/payment through existing Layer A

Do not start next block automatically.