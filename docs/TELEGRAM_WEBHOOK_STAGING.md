# Telegram webhook on Railway (staging)

## Purpose

Close the mixed staging mode where the **FastAPI API** and **Flet Mini App UI** run on Railway, but the **bot** still depended on **local long-polling** (`python -m app.bot.runner`). After this slice, Telegram delivers updates to the **same backend service** that exposes `/health` and `/mini-app/...`, so the bot can run without a long-lived process on your laptop.

This document does **not** cover Step 8 or product changes to booking, payments, or Mini App UX.

## Why Step 8 is not ready until this is done

Step 8 assumes a **coherent staging environment**. If the bot only works while a local polling process runs, staging is not representative: releases, smoke tests, and operator handoff still depend on a developer machine. Webhook delivery to Railway must work first.

## Architecture (two delivery modes)

| Mode | Process | How Telegram delivers updates |
|------|---------|-------------------------------|
| **Dev (local)** | `python -m app.bot.runner` | Long-polling after `deleteWebhook` (see runner) |
| **Staging/prod (Railway)** | `uvicorn app.main:app` (same API service as today) | HTTPS **POST** to `/telegram/webhook` on the public API URL |

The **Mini App UI** stays a **separate Railway service**; only `TELEGRAM_MINI_APP_URL` points Telegram’s Web App button to that URL. Webhook traffic hits the **API** host only.

## Which service accepts the Telegram webhook

The **backend API** service (the one started with `uvicorn app.main:app` — see root `Procfile`) accepts Telegram updates.

The **Flet Mini App** service does **not** receive Telegram bot webhooks.

## Exact webhook URL for the new bot

Register Telegram `setWebhook` to:

```text
https://<your-api-public-host>/telegram/webhook
```

Example:

```text
https://your-api-service.up.railway.app/telegram/webhook
```

Path is fixed in code (`TELEGRAM_WEBHOOK_HTTP_PATH` in `app/api/routes/telegram_webhook.py`). Do **not** point the webhook at the Mini App UI hostname.

## How `TELEGRAM_WEBHOOK_SECRET` is used

1. **Registration:** When calling `setWebhook`, pass `secret_token` equal to `TELEGRAM_WEBHOOK_SECRET` (see CLI below). Telegram’s API requires allowed characters: `A–Z`, `a–z`, `0–9`, `_`, `-` (length 1–256).

2. **Delivery:** Each incoming webhook request includes header `X-Telegram-Bot-Api-Secret-Token` with that value.

3. **Verification:** The FastAPI handler compares the header to `TELEGRAM_WEBHOOK_SECRET` using a constant-time comparison. If the env var is **set**, requests **without** a matching header get **401**.

4. **Dev convenience:** If `TELEGRAM_WEBHOOK_SECRET` is **empty**, the handler does **not** require the header (insecure — only for local/tunnel experiments). **Staging should always set a non-empty secret.**

## Required environment variables (API / bot runtime on Railway)

| Variable | Required | Notes |
|----------|----------|--------|
| `DATABASE_URL` | Yes | Existing Postgres connection |
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token for the new bot |
| `TELEGRAM_MINI_APP_URL` | Yes for CTA | Public HTTPS URL of the **Mini App UI** service (not the API) |
| `TELEGRAM_WEBHOOK_SECRET` | Strongly recommended | Must match `setWebhook` `secret_token` |
| `TELEGRAM_WEBHOOK_BASE_URL` | For CLI `set` only | Public **origin** of this API, no path, no trailing slash, e.g. `https://your-api.up.railway.app` |

Optional: `TELEGRAM_BOT_USERNAME`, language settings — unchanged from product behavior.

## Local dev: polling (unchanged entry)

From repo root, with `.env` loaded:

```bash
python -m app.bot.runner
```

This **deletes** any existing webhook so `getUpdates` polling works. Do **not** run this on Railway while staging should use webhooks, or you will steal updates from the webhook URL.

## Register webhook manually (explicit)

Prerequisites:

1. API deployed with HTTPS; `GET https://<api>/health` returns 200.
2. Same `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, and `TELEGRAM_WEBHOOK_BASE_URL` in the environment you use for the command (typically local `.env` pointing at staging API URL).

Commands:

```bash
python -m app.cli.telegram_webhook set
python -m app.cli.telegram_webhook info
python -m app.cli.telegram_webhook delete
```

- **`set`** — calls `setWebhook` with `https://<TELEGRAM_WEBHOOK_BASE_URL>/telegram/webhook` and `secret_token` from `TELEGRAM_WEBHOOK_SECRET` (if set).
- **`info`** — prints `getWebhookInfo` (URL, pending updates, last error).
- **`delete`** — removes webhook; required before switching back to local polling.

There is **no** automatic `setWebhook` on application startup.

## Smoke test checklist (staging)

1. **`set`** webhook with CLI; then **`info`** shows the expected HTTPS URL.
2. Stop **local** `app.bot.runner` completely.
3. In Telegram private chat: **`/start`** — bot responds (served via Railway webhook).
4. Exercise existing **commands** and menus as before.
5. Tap **CTA / “Deschide Mini App”** — Mini App opens the **Flet** URL (`TELEGRAM_MINI_APP_URL`); catalog loads against the API.
6. Confirm: with polling stopped, the bot **still** answers (proves webhook path).

## Roll back safely (return to local polling)

1. On your machine (with token in `.env`):

   ```bash
   python -m app.cli.telegram_webhook delete
   ```

2. Verify: `python -m app.cli.telegram_webhook info` shows empty URL.

3. Run locally:

   ```bash
   python -m app.bot.runner
   ```

4. Note: until `set` is run again, Railway will **not** receive Telegram traffic for this bot.

## Production CORS / API origin

Webhook requests come from Telegram’s servers, not browser CORS. If the Mini App browser client calls the API from a different origin, ensure existing API CORS settings allow that origin (separate from this webhook slice).

## Known limitations

- **FSM memory storage** is per process; multiple API replicas may split FSM state. For current MVP, prefer a single worker / replica for the API if you rely on FSM in private chat.

## What stays out of scope

- Step 8 features
- Booking/payment rule changes
- Mini App UI changes
- Automatic webhook registration in `uvicorn` startup
