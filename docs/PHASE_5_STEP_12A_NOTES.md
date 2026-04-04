# Phase 5 / Step 12A — Telegram private chat message hygiene

## Scope

**Allowed:** bot handlers, keyboards/messages/services as needed, small in-memory helper, docs, narrow unit tests.

**Out of scope:** booking/payment business logic, webhooks, Mini App API, schema/migrations, admin/operator flows, waitlist.

## Policy

- **Transient / service** bot messages are tracked in memory (per process). When a new message of the same **category** is sent, the bot **best-effort deletes** the previous one (`delete_message` in try/except).
- **No database** — store resets on worker restart.
- **Not deleted:** user messages, payment confirmations, temporary reservation confirmations, help/contact/bookings content, reservation prep summaries, tour detail bodies, `language_saved`, and similar “anchor” outcomes.

## Categories (safe slice)

| Category | Role |
|----------|------|
| `LANGUAGE_PROMPT` | Language picker (single active message per chat). |
| `FILTER_STEP` | One slot for date / destination / budget step prompts (each new step replaces the previous). |
| `CATALOG_WELCOME` + `CATALOG_LIST` | Home/browse pair: welcome + tour list; `register_catalog_bundle` also clears stale language picker and filter prompts when a new catalog is shown. |

## Files

- `app/bot/transient_messages.py` — store, `register_transient`, `register_catalog_bundle`, `answer_and_register_*` helpers.
- `app/bot/handlers/private_entry.py` — wired paths for `/start`, `/language`, `/tours`, browse/filter callbacks, catalog sends.

## Manual smoke (Step 12A)

1. `/start` twice — no duplicate stacked language/home rows beyond one active picker + one catalog pair pattern.
2. `/language` several times — old picker removed when possible.
3. Filter by date / destination / budget — intermediate prompts do not pile up (single `FILTER_STEP` slot).
4. Complete or view a reservation/payment/help flow — important final messages remain.

## Verification

- `python -m compileall app/bot/transient_messages.py app/bot/handlers/private_entry.py`
- `python -m unittest tests.unit.test_transient_messages -v` (optional narrow suite)
