Fix Telegram admin execution link tour selection callback_data limit regression.

Problem:
After Y32.9 compatible tour selection UI, clicking "Replace execution link" crashes with:
TelegramBadRequest: BUTTON_DATA_INVALID
Trace points to:
app/bot/handlers/admin_moderation.py
_show_link_tour_candidates(...)
message.answer(... reply_markup ...)

Root cause hypothesis:
Inline keyboard callback_data for tour candidate buttons exceeds Telegram 64-byte limit.

Task:
Make callback_data short and deterministic.

Rules:
- Do not change domain logic.
- Do not change Mini App.
- Do not change Layer A booking/payment.
- Do not change identity bridge.
- No migrations.
- Keep manual fallback.
- Keep compatible filtering and confirmation screen.
- Preserve create/replace behavior.

Implementation guidance:
- Replace verbose callback_data with compact tokens.
- Example pattern:
  - exec_link:list:{offer_id}:{mode}:{page}
  - exec_link:pick:{offer_id}:{mode}:{tour_id}
  - exec_link:manual:{offer_id}:{mode}
- Do not include tour title/code/status in callback_data.
- Keep user-visible text in button label/message only.
- Add/adjust tests to assert all generated callback_data values are <= 64 bytes.
- Cover create and replace candidate buttons, next/prev, manual fallback, confirm/cancel if applicable.

Tests:
- python -m compileall app/bot/handlers/admin_moderation.py app/bot/constants.py app/bot/messages.py tests/unit/test_telegram_admin_moderation_y281.py
- python -m pytest tests/unit/test_telegram_admin_moderation_y281.py
- python -m pytest tests/unit/test_supplier_offer_track3_moderation.py

After coding report:
- files changed
- exact callback_data format
- tests run
- confirm no runtime/domain semantics changed