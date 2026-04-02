# Phase 5 Step 8 — smoke check (private chat + Mini App)

## Purpose

Validate a **cohesive staging journey** after Railway webhook + Mini App UI deployment: the bot acts as a **guide/launcher**, the Mini App as the **primary booking surface**, and **bookings/status** stay easy to find from both places.

This checklist does **not** replace automated tests or Step 9+ scope.

## Expected user journey

1. User opens the bot in **private chat** and sends `/start` (or uses a deep link).
2. User reads a short **welcome** that states the Mini App is the main place for catalog, bookings, and payment; chat offers **optional quick filters**.
3. User taps **Open Mini App** (primary) or **My bookings (Mini App)** when they need status.
4. User works in the **Mini App** (catalog → detail → preparation → payment flow as already implemented).
5. User can return to **Telegram** (close Mini App or switch chat) and use `/help`, `/bookings`, or the same URL buttons without confusion.

## Bot entry points

| Entry | Expected behavior |
|-------|-------------------|
| `/start` | Welcome + home keyboard: **Mini App** and **My bookings** first, then chat filters and language |
| `/tours` | Same catalog overview pattern as today (welcome + list) |
| `/language` | Language picker (unchanged) |
| `/help` | Short guide + **Open Mini App** / **My bookings** buttons |
| `/bookings` | Explains status is in Mini App + same two URL buttons |
| `/contact` | Support expectation + same two URL buttons |

**Mini App URLs:** All `url` buttons use `TELEGRAM_MINI_APP_URL` from the API/bot environment. **My bookings** uses `{TELEGRAM_MINI_APP_URL}/bookings` (same origin, path `/bookings`).

## Mini App entry point

- Telegram **Web App** / menu button should point to the **root** of the Mini App service (`TELEGRAM_MINI_APP_URL`), as already configured.
- Catalog screen states that **My bookings** holds reservation/payment status and mentions alignment with bot shortcuts.

## Bookings / status checkpoints

| Where | What to verify |
|-------|----------------|
| Bot | **My bookings (Mini App)** opens the Mini App at `/bookings` |
| Mini App | **My bookings** on catalog navigates to the bookings list |
| Mini App | Booking detail and payment status views still work as before |

## Exact smoke-test order (staging)

0. **Optional but recommended:** If `TEST_BELGRADE_001` was used recently, run `python scripts/reset_test_belgrade_tour_state.py` and confirm stdout ends with **`SMOKE_READY=YES`** (see `docs/PHASE_5_STEP_8C_NOTES.md`). Do **not** treat prepare/catalog issues as UI bugs when seats are exhausted or dates are stale — reset first.

1. **Bot:** `/start` — confirm welcome copy and that **Open Mini App** appears **above** date/destination/budget/catalog rows.
2. **Bot:** Tap **Open Mini App** — catalog opens (HTTPS Mini App service).
3. **Mini App (phone):** On each main screen, the **whole body** must scroll (one shared layout: `scrollable_page` — filters + cards on catalog; detail/prepare/success/payment/bookings/booking detail/help/settings the same). **View details** on a card must be reachable without trapped content.
4. **Bot:** `/bookings`, `/help`, `/contact` — each returns the expected text + Mini App URL buttons, even if profile language is not set yet (copy uses default language). `/language` still opens the picker.
5. **Mini App:** From catalog, open **My bookings** — list loads for **only** the Mini App dev Telegram user (`MINI_APP_DEV_TELEGRAM_USER_ID`). Other users’ orders in the DB will not appear (see `docs/PHASE_5_STEP_8B_NOTES.md`).
6. **Mini App:** Open **Help** — static line about returning to the bot + API-driven help content below.
7. **Regression:** Complete or spot-check catalog → detail → preparation → payment screen (no business-rule changes expected).
8. **Webhook:** With local polling **off**, send `/start` again — bot still responds via Railway.

## If `TEST_BELGRADE_001` is sold out on staging

`TEST_BELGRADE_001` is a **staging-only** test tour. Repeated manual tests can consume seats (`seats_available` → 0), leave orders that block preparation, or let **calendar fields go stale** (departure/sales in the past), which breaks prepare/confirm even when the UI is fine.

**Light reset (keep tour + boarding points + translations):** from project root with `DATABASE_URL` set (PowerShell):

```powershell
python scripts/reset_test_belgrade_tour_state.py
```

Shared logic lives in `scripts/staging_belgrade_helpers.py`. The reset removes **payments**, **notification_outbox**, **orders**, and **waitlist** for that tour; sets `seats_available = seats_total` and `status = open_for_sale`; **rolls `departure_datetime`, `return_datetime`, and `sales_deadline` forward** so reservation expiry logic stays valid. It does **not** delete `content_items`. Stdout includes a **`SMOKE_READY=YES/NO`** block — aim for **YES** before a long smoke.

**Full re-seed** (replace boarding + translations path, fresh rolling dates): `python scripts/seed_test_belgrade_tour.py` (see script docstring).

**Nuclear option:** `python scripts/delete_test_belgrade_tour.py` removes the tour entirely; run `seed_test_belgrade_tour.py` after to recreate it.

More detail: `docs/PHASE_5_STEP_8C_NOTES.md`.

## Step 8B — UI language vs content

After changing **Language & settings**, shell labels (nav, titles, buttons, filters) should follow the selected language where keys exist; tour paragraphs may still show fallback language from the API. See `docs/PHASE_5_STEP_8B_NOTES.md`.

## Out of scope for this step

- New booking/payment rules, API contracts, DB changes, waitlist, handoff automation, admin, webhook transport, Mini App deploy model.
- Full i18n polish for every language (some new bot strings fall back to English where not translated).
- BotFather command list updates (document manually if needed).
