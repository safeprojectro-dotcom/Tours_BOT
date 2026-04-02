# Phase 5 Step 8B — stabilization notes (Mini App + staging)

## Mobile scroll pattern

Full-screen Mini App bodies use `mini_app/ui_layout.scrollable_page()`: **SafeArea(expand=True) → Container(expand=True) → Column(expand=True, scroll=AUTO)**. This avoids competing with `page.scroll` and fixes touch scrolling in Telegram WebView.

**Screens expected to use this pattern:** catalog, tour detail, reservation preparation, reservation success, payment entry, my bookings, booking detail, help, settings.

## UI-shell localization vs tour content

- **Translated via `mini_app/ui_strings.shell()` (where keys exist):** navigation labels, screen titles, primary buttons, filter labels, badges (sold out / seats available), loading strings, common helper copy, payment/hold status labels used in the shell.
- **From API (may fallback per backend rules):** tour title, descriptions, program, boarding text, and booking status phrases produced by `resolve_mini_app_booking_facade` / server copy. If the API returns English-only strings for a chosen UI language, that is expected until content is fully translated.

Romanian (`ro`) has partial keys; unknown keys fall back to English.

## `TEST_BELGRADE_001` reset script

`scripts/reset_test_belgrade_tour_state.py`:

- Scoped **only** to tour code `TEST_BELGRADE_001`.
- Deletes **payments** and **notification_outbox** rows for orders of that tour, then **orders**, then **waitlist** entries for that tour.
- Sets `seats_available = seats_total` and `status = open_for_sale`.
- Does **not** delete `content_items`, translations, or boarding points (unlike a full re-seed).

**Full re-seed** (rebuilds boarding + clears more children): `python scripts/seed_test_belgrade_tour.py`.

## My bookings vs raw `orders` in the database

The Mini App calls `MiniAppBookingsService.list_bookings`, which:

1. **Resolves the Telegram user** from `telegram_user_id` (staging: `MINI_APP_DEV_TELEGRAM_USER_ID`) to an internal `users.id`.
2. Lists **only orders where `order.user_id` equals that internal user**. Orders created for other Telegram users or manual DB rows tied to other users **never appear**.

So seeing “many orders in `orders`” but one row in My bookings is **expected** if the extra rows belong to other users or were inserted without the dev Telegram user.

Additionally, `OrderSummaryService.list_user_order_summaries` **skips** an order if `LanguageAwareTourReadService.get_localized_tour_detail` returns `None` for that tour (e.g. missing tour data). In normal staging data this should not hide rows; if it does, fix tour/translation data rather than changing product rules.
