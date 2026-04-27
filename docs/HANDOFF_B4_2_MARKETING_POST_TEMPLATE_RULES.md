B4.2 — Marketing Post Template Rules is completed.

Current state:
- deterministic Telegram draft uses marketing-aware templates
- full_bus and per_seat have different pricing/CTA semantics
- full_bus clearly says whole bus/private group
- per_seat does not fake live availability
- discounts are shown only when real discount fields exist
- route uses supplier offer route facts, not boarding place
- no raw enums or ISO timestamps in Telegram draft

Still unchanged:
- no AI call
- no publish
- no Tour creation
- no Mini App catalog changes
- no booking/payment changes

Next safe step:
B4.3 — Pricing / Discount / Availability Truth Rules, or B5 Admin Moderation & Review.