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

## Hold expiry (Step 9)

Expired unpaid holds are released in the database when you **open catalog, prepare, bookings, or related Mini App actions** (lazy expiry), so seats can return without relying only on manual reset. See `docs/PHASE_5_STEP_9_NOTES.md`.

## Mock payment success (Step 10)

With **`ENABLE_MOCK_PAYMENT_COMPLETION=true`** on the API, complete a hold through **payment entry**, then tap **Pay now** in the Mini App: the client calls **`POST /mini-app/orders/{id}/mock-payment-complete`** and should show **payment confirmed** + **Back to bookings**. **My bookings** / booking detail should show **confirmed** (not an active hold). Production should leave the flag **off** (endpoint returns **403**). Details: `docs/PHASE_5_STEP_10_NOTES.md`.

## My bookings sections (Step 11)

On **My bookings**, the Mini App shows **Confirmed bookings** first, then **Active holds**, then **History** (released/expired unpaid), using the same API data as before — only presentation changes. See `docs/PHASE_5_STEP_11_NOTES.md`.

## Payment edge UX (Step 12)

**Booking detail** adds a short explanation per hold state; **payment** screen uses clearer copy for an active hold, and friendly messages when payment-entry fails (e.g. hold gone) or mock completion is disabled (403). See `docs/PHASE_5_STEP_12_NOTES.md`.

## Support / handoff entry (Step 13)

- **Private chat:** `/help` (guidance only), `/contact` and `/human` record a **`handoffs`** row and reply with an internal reference id (no promise of live operator).
- **API:** `POST /mini-app/support-request` with `telegram_user_id`, optional `order_id`, optional `screen_hint`; `GET /mini-app/help?language_code=` for EN/RO help text.
- **Mini App:** “Log support request” on **Payment**, **Booking detail**, and **My bookings** (when list non-empty); snackbar shows ref or failure. See `docs/PHASE_5_STEP_13_NOTES.md`.

## Step 8B — UI language vs content

After changing **Language & settings**, shell labels (nav, titles, buttons, filters) should follow the selected language where keys exist; tour paragraphs may still show fallback language from the API. See `docs/PHASE_5_STEP_8B_NOTES.md`.

## Ops queue visibility (Step 15)

Staging/production ops can poll **read-only** JSON queues (shared secret `OPS_QUEUE_TOKEN`): `GET /internal/ops/handoffs/open` and `GET /internal/ops/waitlist/active`. This does not change user-facing bot or Mini App flows. See `docs/PHASE_5_STEP_15_NOTES.md`.

## Handoff claim / close (Step 16)

With the same `OPS_QUEUE_TOKEN`, ops can **`PATCH /internal/ops/handoffs/{id}/claim`** (open → `in_review`) and **`PATCH /internal/ops/handoffs/{id}/close`** (→ `closed`). Waitlist endpoints remain read-only. See `docs/PHASE_5_STEP_16_NOTES.md`.

## Out of scope for this step

- New booking/payment rules, API contracts, DB changes, waitlist, handoff automation, admin, webhook transport, Mini App deploy model.
- Full i18n polish for every language (some new bot strings fall back to English where not translated).
- BotFather command list updates (document manually if needed).
