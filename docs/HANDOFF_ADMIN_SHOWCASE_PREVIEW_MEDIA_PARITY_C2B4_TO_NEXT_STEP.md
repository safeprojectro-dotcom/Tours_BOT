# HANDOFF_ADMIN_SHOWCASE_PREVIEW_MEDIA_PARITY_C2B4_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

ADMIN SHOWCASE PREVIEW — C2B4

## Goal

Improve Telegram admin `Preview` so admin sees media parity with future channel post:

- photo when available;
- same showcase caption;
- local admin preview only;
- no channel publish.

## Rules

Preview button remains read-only.

Allowed:

- send photo to admin private chat if there is a usable Telegram file_id / safe media reference;
- send same showcase caption;
- fall back to text preview if image missing/fails;
- show local preview notice.

Forbidden:

- publish to channel
- set published_at
- set showcase_chat_id/message_id
- mutate lifecycle
- create Tour
- activate catalog
- create execution link
- booking/payment/order changes
- Mini App changes
- external AI
- media pipeline/storage implementation

## Safety note

This is a prerequisite before any future `Publică` Telegram button.

## Next possible slices

1. Manual Telegram smoke on offer with image.
2. Preview-before-publish hard gate design.
3. Legacy moderation confirmation/consolidation.
4. Return to business-plan open items.

Do not start next slice automatically.