# CURSOR_PROMPT_B12_B13_3_DISABLE_CHANNEL_LINK_PREVIEW

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a small B12/B13.3 Telegram showcase polish step.

Do not change booking/payment/order/reservation logic.
Do not change Mini App UI.
Do not change B11 routing.
Do not change B10.6 bot behavior.
Do not change media/photo publishing.
Do not add sendPhoto/sendMediaGroup.
Do not add object storage/download/rendering.
Do not change SupplierOffer lifecycle.

---

## Current checkpoint

B12/B13.2 completed and deployed.

Current channel post is now much better:

- branded Romanian text template
- FULL_BUS price as `{price} {currency} / grup`
- no individual seats for FULL_BUS
- program section when `program_text` exists
- CTA line:
  `ℹ️ Detalii | ✅ Rezervă`
- `Detalii` -> bot deep link `supoffer_<id>`
- `Rezervă` -> Mini App supplier-offer landing
- no direct `/tours/{code}`
- no photo/sendPhoto

Manual channel check after deploy showed a visual problem:

Telegram automatically renders a web preview card for the Mini App URL:

- `miniappui-production.up.railway.app`
- `Flet`
- `Flet application.`

This makes the showcase post look technical and ugly.

---

## Goal

Disable Telegram web page preview for supplier offer showcase posts.

Expected result:

- Channel post still contains clickable `Detalii | Rezervă` links.
- Telegram must not show the automatic web preview card.
- Text layout remains clean.
- No change to CTA destinations.
- No change to publish lifecycle.

---

## Files to inspect/change

Inspect:

- app/services/telegram_showcase_client.py
- app/services/supplier_offer_moderation_service.py
- app/services/supplier_offer_showcase_message.py
- tests/unit/test_supplier_offer_track3_moderation.py
- tests/unit/test_supplier_offer_showcase_ro.py
- any tests/mocks around Telegram sendMessage/sendPhoto

Likely change:

- app/services/telegram_showcase_client.py
- tests around sendMessage payload / mocked Telegram request

---

## Required behavior

When sending text-only showcase publication to Telegram:

- use Telegram API option to disable link previews.

Depending on current implementation / aiogram/httpx style, use the appropriate supported parameter:

- `disable_web_page_preview=True`, or
- `link_preview_options={"is_disabled": True}`

Use the style already compatible with the project.

Do not remove the links from the message.
Do not replace HTML links with plain text.
Do not remove Mini App URL.
Do not change CTA order.

---

## Tests

Add/update tests so this does not regress.

Required assertions:

1. `send_showcase_publication(...)` sends text message with link preview disabled.
2. The caption/text still contains links.
3. `photo_url=None` still uses sendMessage path.
4. No sendPhoto behavior is introduced.
5. Existing showcase tests remain green.

Run:

```bash
python -m pytest tests/unit/test_supplier_offer_showcase_ro.py -v
python -m pytest tests/unit/test_supplier_offer_track3_moderation.py -v
python -m compileall app alembic -q