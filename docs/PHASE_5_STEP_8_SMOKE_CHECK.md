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

1. **Bot:** `/start` — confirm welcome copy and that **Open Mini App** appears **above** date/destination/budget/catalog rows.
2. **Bot:** Tap **Open Mini App** — catalog opens (HTTPS Mini App service).
3. **Mini App (phone):** Scroll the catalog — filters and tour cards must scroll; **View details** on a card must be reachable (single scroll surface; page-level scroll is off).
4. **Bot:** `/bookings`, `/help`, `/contact` — each returns the expected text + Mini App URL buttons, even if profile language is not set yet (copy uses default language). `/language` still opens the picker.
5. **Mini App:** From catalog, open **My bookings** — list loads (same user as `MINI_APP_DEV_TELEGRAM_USER_ID` / your test user).
6. **Mini App:** Open **Help** — static line about returning to the bot + API-driven help content below.
7. **Regression:** Complete or spot-check catalog → detail → preparation → payment screen (no business-rule changes expected).
8. **Webhook:** With local polling **off**, send `/start` again — bot still responds via Railway.

## If `TEST_BELGRADE_001` is sold out on staging

Repeated manual tests can consume seats (`seats_available` → 0) or leave orders that block preparation.

**Light reset (keep tour + boarding points):** from project root with `DATABASE_URL` set:

```bash
python scripts/reset_test_belgrade_tour_state.py
```

This deletes **orders** (and cascading payments / notification rows) and waitlist/content rows scoped to that tour, then sets `seats_available = seats_total`.

**Full re-seed** (recreate tour + boarding + translations): use `python scripts/seed_test_belgrade_tour.py` instead (see script docstring).

**Nuclear option:** `python scripts/delete_test_belgrade_tour.py` removes the tour entirely; run `seed_test_belgrade_tour.py` after to recreate it.

## Out of scope for this step

- New booking/payment rules, API contracts, DB changes, waitlist, handoff automation, admin, webhook transport, Mini App deploy model.
- Full i18n polish for every language (some new bot strings fall back to English where not translated).
- BotFather command list updates (document manually if needed).
