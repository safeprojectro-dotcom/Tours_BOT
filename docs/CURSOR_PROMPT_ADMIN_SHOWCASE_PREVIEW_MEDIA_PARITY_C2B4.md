# CURSOR_PROMPT_ADMIN_SHOWCASE_PREVIEW_MEDIA_PARITY_C2B4

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN SHOWCASE PREVIEW — C2B4

Telegram admin `Preview` button should show media parity with the future channel post:

- same/similar photo when available;
- same showcase caption;
- sent only to the admin private chat;
- never published to the Telegram channel.

---

## Context

Implemented:

- Telegram admin operator workflow read model.
- Compact operator card.
- Read-only buttons:
  - Actualizează
  - Preview
- Safe mutation buttons with confirmation:
  - Pregătește
  - Aprobă text
- C2B3 label/order polish deployed.

Current issue:

Admin presses `Preview`, but sees only text preview. Admin does not see the image/photo that may appear in the final Telegram channel post.

Product concern:

Before any future `Publică` button, admin must see the post as close as possible to the real channel output, especially image + caption.

---

## Strict boundaries

Do not publish to Telegram channel.
Do not call publish endpoint.
Do not set published_at.
Do not set showcase_chat_id.
Do not set showcase_message_id.
Do not mutate supplier_offer lifecycle.
Do not create Tour.
Do not activate catalog.
Do not create execution link.
Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not add migrations.
Do not call external AI.
Do not add public/dangerous buttons.

This slice only improves the existing admin `Preview` read-only action.

---

## Goal

When admin taps the existing Telegram admin `Preview` button:

1. Load the same showcase preview data/service already used today.
2. If the preview/post has a usable Telegram photo reference/file_id, send a photo message to admin chat with caption.
3. If no usable photo exists, fall back to current text preview.
4. Always include a clear local-preview notice:
   - not sent to channel;
   - no publish happened.
5. Preserve current safety:
   - no lifecycle mutation;
   - no channel send;
   - no publish metadata write.

---

## Source files to inspect

Inspect:

- app/bot/handlers/admin_moderation.py
- app/bot/messages.py
- app/bot/constants.py
- app/services/supplier_offer_moderation_service.py
- app/services/supplier_offer_showcase_message.py
- app/services/supplier_offer_review_package_service.py
- app/models/supplier.py
- app/schemas/supplier_admin.py
- tests/unit/test_operator_workflow_c2a_specs.py
- tests/unit/test_operator_workflow_c2b3_keyboard.py
- tests/unit/test_supplier_offer_showcase_ro.py
- tests/unit/test_telegram_admin_moderation_y281.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md if present

Use actual project structure if names differ.

---

## Implementation requirements

### 1. Reuse existing showcase builder/service

Do not create a separate “admin preview caption” truth.

Use the same service / builder that powers:

- GET showcase-preview;
- future publish caption;
- current Preview text.

The admin preview must not diverge from the channel post builder.

### 2. Media source

Determine the safest media source from existing preview/publication object and/or offer fields.

Likely sources may include:

- showcase_preview.showcase_photo_url
- offer.cover_media_reference
- offer.media_references
- Telegram photo file_id embedded in `cover_media_reference`
- Telegram photo refs in media_references

Preferred behavior:

- If there is a Telegram `file_id`, use bot.send_photo(chat_id=admin_chat_id, photo=file_id, caption=caption_html, parse_mode HTML if project uses it).
- If media is URL and Telegram can send photo URL safely, use URL only if existing code already supports that safely.
- If unsupported/uncertain, fall back to text preview with a warning.

Do not download media.
Do not implement storage/media pipeline.
Do not generate images.
Do not transform images.

### 3. Caption

Use the exact caption HTML/plain output intended for showcase where possible.

Respect Telegram caption limit if the project has helper logic.

If caption is too long for photo caption, safe fallback:

- send photo with short “Local preview” caption;
- then send full caption as separate text message.

Do not silently truncate commercial/factual content.

### 4. Local preview notice

Add a short header or footer in the admin preview message, e.g.:

RO:

```text
Previzualizare locală — nu s-a trimis nimic în canal.