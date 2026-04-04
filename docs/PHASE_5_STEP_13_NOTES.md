# Phase 5 / Step 13 — Support / handoff entry hardening

## Analysis

- **DB:** `handoffs` table and `HandoffRepository.create` existed, but there was **no** API or bot path wired to create rows before this step.
- **This step adds** a minimal, honest persistence path: `HandoffEntryService` + `POST /mini-app/support-request`, plus `/contact` and `/human` in private chat.
- **Not implemented:** operator notifications, assignment UI, full lifecycle — copy explicitly avoids promising live chat or instant assignment.

## Private chat

- **`/help`:** Stronger copy: `/contact`, `/human`, Mini App Help, and “Log support request” — no DB write.
- **`/contact`:** Sends guidance, then creates a handoff with reason `private_chat_contact`, then a second message with reference id (or failure text).
- **`/human`:** Same pattern with reason `private_chat_human_request`.
- **Locales:** `app/bot/messages.py` — `en` + `ro` for `help_command_reply`, `contact_command_reply`, `human_command_reply`, `handoff_request_recorded`, `handoff_request_failed`.

## API

- **`POST /mini-app/support-request`** — body: `telegram_user_id`, optional `order_id` (must belong to user), optional `screen_hint` (e.g. `payment`, `booking_detail`, `my_bookings`). Persists reason `mini_app_support|<hint>`.
- **`GET /mini-app/help?language_code=`** — returns English or Romanian static help text from `MiniAppHelpSettingsService.get_help_read`.

## Mini App (Flet)

- **Payment screen:** Note + “Log support request” → API with `order_id` + `screen_hint=payment`.
- **Booking detail:** Note + same button → `booking_detail`.
- **My bookings:** Banner when there is at least one booking → `my_bookings`, `order_id` null.
- **Help screen:** Loads localized help via `language_code`.
- **Snackbar:** Confirms internal reference id or failure; never implies operator assigned.

## Files

- `app/services/handoff_entry.py` — new
- `app/services/mini_app_help_settings.py` — bilingual help, copy updates
- `app/api/routes/mini_app.py` — help query param, support-request route
- `app/schemas/mini_app.py` — `MiniAppSupportRequest`, `MiniAppSupportRequestResponse`
- `app/bot/messages.py`, `app/bot/handlers/private_entry.py`
- `mini_app/api_client.py`, `mini_app/app.py`, `mini_app/ui_strings.py`

## Manual smoke

1. `/help`, `/contact`, `/human` in Telegram private chat.
2. Mini App: Help (en/ro), Payment → log support, Booking detail → log, My bookings → log.
3. Confirm snackbar/second message shows reference id, not “operator replied”.

## Verification

- `python -m compileall` on touched modules
- `python -m unittest tests.unit.test_handoff_entry tests.unit.test_support_message_keys -v`
