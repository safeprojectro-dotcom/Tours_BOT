# CURSOR_PROMPT_B15C3_POST_B15C_COPY_POLISH

## Context

Project: Tours_BOT.

We are continuing after:
- B15C exact Tour CTA gate before supplier offer publish.
- B15C1 direct channel `Rezervă` through Telegram Mini App startapp.
- B15C2 admin Telegram navigation keeps operator on the same supplier offer after bridge/catalog/link actions.
- B15C4 cover replacement/text-only guard.
- B15C5 production smoke PASS for direct Mini App short-name CTA.

Current accepted publication/conversion order for supplier offers is:

1. Supplier offer approved/packaged.
2. Create/link Tour bridge.
3. Activate linked Tour for Mini App catalog.
4. Create active execution link.
5. Publish showcase/channel post.
6. Channel `Rezervă` opens exact Mini App tour via:
   `https://t.me/<bot>/<mini_app_short_name>?startapp=tour_<tour_code>`

Important: execution links are now created before showcase publish, not after publish.

## Problem

Some user/admin-facing copy still says or implies:

- “execution links are created after showcase publish”
- “Booking link is created after publish”
- similar wording that conflicts with B15C.

This is now misleading.

## Goal

Implement B15C3 copy polish:

Find and update user/admin-facing copy so it matches the current B15C order:

- execution link / booking link must exist before channel publish;
- publish is blocked until exact tour conversion chain is ready;
- channel publish is the final public step, not the step that enables execution link creation.

## Scope

Search at least:
- `app/`
- `docs/`
- `tests/`

For phrases around:
- `execution links are created after showcase publish`
- `created after showcase publish`
- `after publish`
- `booking link`
- `execution link`
- `publish before`
- `showcase publish`

## Required code behavior

1. Update copy/messages only.
2. Do not change business logic.
3. Do not change gates.
4. Do not change service decisions.
5. Do not change API response structure unless the response text itself is the only changed field.
6. Keep bilingual EN/RO wording aligned where applicable.

## Suggested replacement meaning

Use wording like:

EN:
- `Booking link: missing — create an active execution link before channel publish.`
- `Create an active execution link after the tour is listed for sale and before publishing to the channel.`
- `Channel publish requires an active booking link to the exact Mini App tour.`

RO:
- `Link rezervări: lipsește — creează un link activ de rezervare înainte de publicarea pe canal.`
- `Creează linkul de rezervare după listarea turului în catalog și înainte de publicarea pe canal.`
- `Publicarea pe canal necesită un link activ către turul exact din Mini App.`

Use existing project translation/message style. Do not introduce a new translation system.

## Tests

Update tests that assert the old text.

Run focused tests covering:
- supplier offer review package / conversion status panel;
- operator workflow/publish gate if relevant;
- admin moderation tests if text assertions exist.

Suggested commands may include:

```powershell
python -m pytest `
  tests/unit/test_supplier_offer_review_package.py `
  tests/unit/test_supplier_offer_track3_moderation.py `
  tests/unit/test_supplier_offer_catalog_conversion_closure.py `
  tests/unit/test_telegram_admin_moderation_y281.py `
  -k "execution_link or booking_link or publish or conversion_status or c2b10" `
  -q