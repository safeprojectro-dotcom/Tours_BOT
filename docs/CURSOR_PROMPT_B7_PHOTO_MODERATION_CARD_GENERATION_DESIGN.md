You are continuing Tours_BOT after B6.

Goal:
B7 — Photo Moderation & Card Generation DESIGN ONLY.

Current state:
B6 creates branded_telegram_preview with cover reference and warnings.
Cover can be telegram_photo, but it is not yet public/publishable.
Now we need design rules before image/card implementation.

Scope:
Documentation/design only.
Do not change app code.
Do not create migrations.
Do not call Telegram getFile.
Do not download images.
Do not generate images.
Do not publish.

Create:
docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md

Design must cover:
1. Photo states:
- raw_uploaded
- needs_admin_visual_review
- approved_for_card
- rejected_bad_quality
- rejected_irrelevant
- fallback_card_required
- card_generated
- card_approved

2. Media source rules:
- telegram_photo file_id is internal bot reference, not public URL
- public channel publish needs either Telegram send-by-file-id support or downloaded/hosted media later
- no supplier photo is trusted without admin visual review

3. Quality rules:
- minimum resolution
- relevance to destination/vehicle/tour
- no misleading image
- no copyrighted/watermarked competitor media where obvious
- no unsafe/inappropriate content

4. Card generation model:
- B7 design only
- later implementation may generate a branded 16:9 or 4:5 card
- card uses:
  title
  date
  route
  price
  vehicle/capacity
  supplier cover or fallback background
  brand mark
- card must not invent facts

5. Admin flow:
- review photo
- approve photo for card
- reject photo
- request replacement
- use fallback branded card
- approve generated card

6. Data model options:
- minimal: continue using media_references + packaging_draft_json
- better later: supplier_offer_media table
- explain tradeoffs
- recommend next implementation path

7. Safety:
- no automatic public publish after card generation
- generated card must go back to admin review
- no customer notification
- no Mini App/Tour/booking/payment changes

8. Next implementation slice:
B7.1 — media review metadata + admin visual decision API
B7.2 — card rendering preview
B7.3 — publish-safe media preparation

Update docs/CHAT_HANDOFF.md and docs/OPEN_QUESTIONS_AND_TECH_DEBT.md with B7 design checkpoint and next step B7.1.

Before writing:
- summarize B6 state
- explain why B7 starts as design-only

After writing:
- files changed
- decisions captured
- next safe step