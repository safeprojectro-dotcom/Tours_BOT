You are continuing Tours_BOT after B7.1.

Goal:
B7.2 — Card Rendering Preview.

Current state:
- B6 creates branded_telegram_preview JSON.
- B7.1 stores media_review in packaging_draft_json.
- cover can be approved_for_card, rejected, replacement_requested, or fallback_card_required.
- No image bytes are generated yet.

Goal:
Add a safe server-side preview metadata/render plan for a future branded card.

Scope:
Preview/render-plan only. Prefer JSON-first. If rendering image bytes is too risky, do not render actual files in this slice.

Allowed:
- create card_render_preview JSON under packaging_draft_json
- admin endpoint to generate card preview plan
- use existing branded_telegram_preview + media_review
- tests

Do NOT:
- call Telegram getFile
- download Telegram photo
- generate public image asset
- upload to S3/storage
- publish to Telegram
- create Tour
- mutate Mini App catalog
- touch booking/payment
- call AI

Suggested endpoint:
POST /admin/supplier-offers/{offer_id}/media/card-preview/generate
GET may reuse /media/review or /packaging/review to expose it.

Data shape:
packaging_draft_json["card_render_preview"] = {
  "version": "b7_2",
  "status": "render_plan_ready | blocked_needs_photo_review | fallback_plan_ready",
  "layout": {
    "aspect_ratio": "4:5",
    "width": 1080,
    "height": 1350,
    "safe_area": {...}
  },
  "source": {
    "mode": "approved_cover | fallback_branded_background",
    "cover_media_reference": "...",
    "source_status": "approved_for_card | fallback_card_required"
  },
  "text_layers": [
    {"role": "title", "text": "..."},
    {"role": "date", "text": "..."},
    {"role": "price", "text": "..."},
    {"role": "route", "text": "..."},
    {"role": "vehicle", "text": "..."}
  ],
  "brand_layers": [
    {"role": "brand", "text": "Tours from Timisoara"}
  ],
  "warnings": [...]
}

Rules:
1. If media_review.status == approved_for_card:
- status = render_plan_ready
- source.mode = approved_cover
- cover_media_reference must be present

2. If media_review.status == fallback_card_required:
- status = fallback_plan_ready
- source.mode = fallback_branded_background

3. If no media_review or status not approved/fallback:
- status = blocked_needs_photo_review
- include warning

4. Text must come from branded_telegram_preview.card_lines/title only.
- do not invent values
- do not use raw enum/ISO
- keep fields short and card-friendly

5. No lifecycle or publish changes.

Tests:
- approved_for_card creates render_plan_ready
- fallback_card_required creates fallback_plan_ready
- no media review creates blocked_needs_photo_review
- text_layers come from branded_telegram_preview
- no lifecycle_status/published_at/showcase fields changed
- no Telegram/getFile/download/render/upload/Tour/Mini App/booking/payment side effects

Before coding:
1. summarize B7.1 state
2. list files expected to change
3. explain why B7.2 is render-plan only and safe
4. state non-goals

After coding:
1. files changed
2. endpoint added
3. card_render_preview shape
4. tests run
5. confirm no Telegram getFile/download/render/upload/publish/Tour/Mini App/booking/payment/AI changes
6. next safe step: B7.3 publish-safe media preparation OR B8/B9 Offer → Tour bridge