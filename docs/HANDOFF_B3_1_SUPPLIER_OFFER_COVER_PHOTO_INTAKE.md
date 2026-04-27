B3.1 — Supplier Offer Cover Photo Intake is completed.

Current state:
- supplier offer intake accepts one Telegram cover photo
- largest Telegram photo file_id is stored as cover_media_reference with telegram_photo: prefix
- optional media metadata may be stored in media_references JSON
- URL cover option still works if implemented
- “no photo yet” still works

Important:
This is raw media intake only.

Still not implemented:
- gallery/multiple photos
- file download/storage
- crop/resize
- branded card generation
- AI image analysis
- Telegram channel photo publishing changes
- Tour creation
- Mini App catalog visibility
- booking/order/payment changes

Next safe step:
B4 — AI Packaging Layer.