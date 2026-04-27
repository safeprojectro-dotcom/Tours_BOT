You are continuing Tours_BOT after B7 design.

Goal:
B7.1 — Media Review Metadata + Admin Visual Decision API.

Read:
- docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Scope:
Implement metadata-only visual review decisions for supplier offer cover media.

Allowed:
- additive enum/state fields if needed
- use existing supplier_offers.cover_media_reference and media_references
- store review metadata in packaging_draft_json or a small additive column if cleaner
- admin API endpoints for visual decision
- tests

Do NOT:
- call Telegram getFile
- download images
- generate image/card files
- publish to Telegram
- create Tour
- mutate Mini App catalog
- touch booking/payment
- call AI

Implement decisions:
1. approve cover for card
2. reject cover with reason
3. request replacement with reason
4. require fallback branded card

Suggested API:
- GET /admin/supplier-offers/{offer_id}/media/review
- POST /admin/supplier-offers/{offer_id}/media/approve-for-card
- POST /admin/supplier-offers/{offer_id}/media/reject
- POST /admin/supplier-offers/{offer_id}/media/request-replacement
- POST /admin/supplier-offers/{offer_id}/media/use-fallback-card

Data shape:
Store something like:

packaging_draft_json["media_review"] = {
  "version": "b7_1",
  "cover_media_reference": "...",
  "status": "approved_for_card | rejected_bad_quality | rejected_irrelevant | replacement_requested | fallback_card_required",
  "reason": "...",
  "reviewed_at": "...",
  "reviewed_by": "..."
}

Rules:
- approve allowed only if cover_media_reference exists
- reject/request-replacement require non-empty reason
- fallback allowed even if no cover exists
- no lifecycle_status changes
- no packaging_status publish side effects
- branded_telegram_preview may surface media_review status if already easy, but not required

Tests:
- get review returns current cover + media review metadata
- approve cover stores approved_for_card
- approve without cover fails
- reject requires reason
- request replacement requires reason
- fallback works with no cover
- no publish fields changed
- no lifecycle_status changed
- no Telegram/Tour/Mini App/booking/payment side effects

Before coding:
1. summarize B7 design state
2. list files expected to change
3. explain why B7.1 is metadata-only and safe
4. state non-goals

After coding:
1. files changed
2. API endpoints added
3. media_review JSON shape
4. tests run
5. confirm no Telegram getFile/download/publish/Tour/Mini App/booking/payment/AI changes
6. next safe step: B7.2 card rendering preview