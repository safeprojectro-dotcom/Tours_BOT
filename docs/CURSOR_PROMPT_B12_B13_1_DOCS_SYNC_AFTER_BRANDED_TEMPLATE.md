# CURSOR_PROMPT_B12_B13_1_DOCS_SYNC_AFTER_BRANDED_TEMPLATE

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Это docs-only correction после B12/B13.1 branded Telegram showcase text template.

Не менять app/.
Не менять tests/.
Не менять alembic/.
Не менять mini_app/.
Не менять runtime-код.

## Current implementation already done

B12/B13.1 branded Romanian Telegram showcase template implemented in app/services/supplier_offer_showcase_message.py.

Implemented behavior:
- Telegram channel post is now branded text-first.
- Template uses emoji/section structure:
  - 🚌 title
  - route/destination
  - 📅 period
  - 💰 price
  - transport
  - capacity / group-safe wording
  - include / exclude bullet sections
  - 🔎 availability disclaimer
  - 👉 bot CTA
  - 📲 Mini App CTA
- CTAs remain safe:
  - primary bot deep link supoffer_<id>
  - secondary Mini App supplier-offer landing
- No direct /tours/{code} channel link.
- No photo.
- No sendPhoto/sendMediaGroup.
- No media download/storage/rendering.
- Admin publish flow unchanged.
- Booking/payment/Mini App logic unchanged.

Tests already passed:
- tests/unit/test_supplier_offer_showcase_ro.py
- tests/unit/test_supplier_offer_track3_moderation.py

## Goal

Update docs to reflect B12/B13.1 completion.

Update briefly:

1. docs/CHAT_HANDOFF.md
2. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
3. docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required doc content

Document:

- B12/B13.1 branded Romanian Telegram showcase text template implemented.
- Channel post is now branded text-first, not dry ORM-style listing.
- Emoji section structure is used.
- CTA remains:
  - stable bot deep link supoffer_<id>
  - safe Mini App supplier-offer landing
- No hard “Rezervă” claim.
- No direct /tours/{code} in channel.
- No photo/media publish.
- B7.4/B7.5/B7.6 remain future for storage/render/sendPhoto.
- Admin remains final publisher.
- Mini App remains execution truth.
- No booking/payment changes.

Do not rewrite documents.

## Final report

Report:
1. Files changed
2. Sections updated
3. Confirmation docs-only
4. Any risks/follow-up