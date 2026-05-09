# CURSOR_PROMPT_B12_B13_4A_SHOWCASE_PREVIEW_READINESS_FIELDS

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Это маленький correction step внутри B12/B13.4.

Не менять:
- actual publish behavior
- Telegram send behavior
- booking/payment/order/reservation
- Mini App UI
- B11/B10.6 routing
- media/photo pipeline
- SupplierOffer lifecycle transitions

## Current state

B12/B13.4 added:

GET /admin/supplier-offers/{offer_id}/showcase-preview

Current response includes:
- supplier_offer_id
- caption_html
- publication_mode
- showcase_photo_url
- disable_web_page_preview
- cta_detalii_href
- cta_rezerva_href
- preview_notice

Preview is read-only and does not call Telegram.

## Missing required contract fields

Add publish readiness fields to the preview response.

Required additions:

1. lifecycle_status
   - string value of current SupplierOffer lifecycle_status

2. can_publish_now
   - true only when the offer is in the lifecycle state that POST /publish can accept today
   - usually approved
   - false for published, draft, ready_for_moderation, rejected, etc.
   - do not mutate state

3. warnings
   - list[str]
   - include clear admin-facing warning strings when:
     - offer is not approved / cannot be published now
     - offer is already published
     - telegram_bot_username is missing, so Detalii link cannot be built
     - telegram_mini_app_url is missing, so Rezervă link cannot be built
     - showcase channel id or bot token missing, if settings expose this and it affects real publish
   - do not expose secrets
   - keep warnings stable enough for tests, but not over-engineered

## Expected response shape

Example:

```json
{
  "supplier_offer_id": 123,
  "lifecycle_status": "approved",
  "caption_html": "...",
  "publication_mode": "text_only",
  "showcase_photo_url": null,
  "disable_web_page_preview": true,
  "cta_detalii_href": "https://t.me/...",
  "cta_rezerva_href": "https://.../supplier-offers/123",
  "can_publish_now": true,
  "warnings": [],
  "preview_notice": "..."
}