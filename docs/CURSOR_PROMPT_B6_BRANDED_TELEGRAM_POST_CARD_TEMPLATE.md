You are continuing Tours_BOT after B5.

Goal:
B6 — Branded Telegram Post / Card Template.

Current state:
B1–B4.3 created supplier offer intake, packaging, marketing template and truth rules.
B5 added admin review:
- review detail
- approve / reject / request clarification
- draft edit
- approved_for_publish does NOT publish

Now we need a branded Telegram/channel preview layer.

Important:
B6 must NOT publish to Telegram.
B6 must NOT create Tour.
B6 must NOT mutate Mini App catalog.
B6 must NOT touch booking/payment.

Goal:
Create a deterministic branded post/card preview structure that admin can review before later publishing.

Scope:
- Use existing packaging_draft_json and media fields.
- Add a structured branded preview payload.
- Keep it review-only.
- Do not download Telegram photos.
- Do not generate image files yet unless already safe and local-only.
- Do not call AI.

Expected output:
A new preview JSON inside packaging_draft_json, for example:
packaging_draft_json["branded_telegram_preview"] = {
  "template_version": "b6_v1",
  "channel": "telegram",
  "title": "...",
  "cover": {
    "source": "telegram_photo",
    "ref": "telegram_photo:...",
    "status": "needs_admin_visual_review"
  },
  "card_lines": [...],
  "caption": "...",
  "cta": [...],
  "warnings": [...]
}

Branded preview rules:
1. Title:
- use offer title
- keep original supplier language
- do not invent destination

2. Cover:
- if cover_media_reference exists:
  mark cover as available but needs admin visual review
- if no cover:
  mark fallback_branded_card_needed = true
- no download / no image transformation in B6

3. Card lines:
For full_bus:
- date
- route
- price: "{price} {currency} — tot autobuzul"
- vehicle/capacity
For per_seat:
- date
- route
- price: "{price} {currency} / persoana"
- availability fallback: "Locurile se confirma la rezervare"

4. Caption:
- reuse cleaned telegram_post_draft from B4.3
- do not introduce raw enum / ISO / fake scarcity

5. Warnings:
- surface existing quality_warnings_json
- add visual warning if cover is missing
- add warning if cover source is telegram_photo because it is not yet publicly publishable as URL/card

6. Admin review:
- B6 should make preview visible from:
  GET /admin/supplier-offers/{offer_id}/packaging/review
- Optionally add:
  POST /admin/supplier-offers/{offer_id}/packaging/branded-preview/generate
  if separation is cleaner
- The preview generation must not approve/reject/publish.

Tests:
- branded preview generated for offer with telegram_photo cover
- missing cover produces fallback warning
- full_bus card line says tot autobuzul
- per_seat card line says / persoana and no fake availability
- review endpoint returns branded_telegram_preview when present
- no lifecycle_status change
- no published_at / showcase_message_id change
- no Telegram send / no Tour / no Mini App / no booking/payment side effects

Before coding:
1. summarize B5 state
2. list files expected to change
3. explain why B6 is preview-only and safe
4. state exact non-goals

After coding:
1. files changed
2. preview JSON shape
3. tests run
4. confirm no publish/Tour/Mini App/booking/payment/AI changes
5. next safe step: B7 Photo Moderation & Card Generation or B9/B10 Offer → Tour Bridge