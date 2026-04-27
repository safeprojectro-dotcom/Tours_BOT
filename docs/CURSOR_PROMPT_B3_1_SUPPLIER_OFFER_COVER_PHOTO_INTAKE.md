You are continuing Tours_BOT after B3.

Goal:
B3.1 — Supplier Offer Cover Photo Intake.

Implement a small UX fix in the supplier Telegram intake flow:
supplier should be able to upload ONE cover photo directly in Telegram instead of being forced to paste a public URL.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md

Scope:
Update supplier offer intake FSM only.

Allowed:
- accept Telegram photo message in cover media step
- store largest photo file_id as cover_media_reference
- use a safe prefix like telegram_photo:<file_id>
- optionally store minimal metadata in media_references JSON if easy:
  - source=telegram_photo
  - file_id
  - file_unique_id
  - width
  - height
  - file_size if available
  - role=cover
- keep existing URL option if already implemented
- keep “no photo yet” option
- update review summary copy to show “photo uploaded” instead of raw file_id
- add tests

Validation:
- accept only message.photo
- reject documents/files/videos in this step
- choose largest available photo size
- if width/height available and too small, reject with friendly message
- suggested minimum: 800x500
- do not download the file
- do not resize/crop
- do not create branded card
- do not support gallery/multiple photos yet

Must NOT:
- implement media table
- implement multiple photos/gallery
- download files
- upload to storage
- generate card image
- publish photo
- change Telegram channel publish behavior
- create Tour
- touch Mini App catalog
- change booking/order/payment
- implement AI image analysis

Before coding:
1. summarize B3 state and why URL-only is a UX blocker
2. list expected files to change
3. explain why accepting file_id only is safe

After coding:
1. files changed
2. behavior added
3. tests run
4. confirm no publish/Tour/Mini App/booking/payment/AI changes
5. next safe step: B4 AI Packaging Layer