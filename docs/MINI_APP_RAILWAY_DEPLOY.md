# Mini App UI on Railway (Flet)

## Purpose

The FastAPI service (`app.main:app`) exposes **JSON API** under `/mini-app/...`. It does **not** serve the Flet Flutter web UI. Telegram Mini App must open a **separate URL** that runs the Flet web process so users see the catalog and flows, not 404 or raw JSON.

This document describes a **second Railway service** (or any host) that runs only `mini_app/` as a public web UI, while the existing API service stays unchanged.

## Architecture (two processes)

| Service | Role | Typical start command |
|--------|------|------------------------|
| **Backend API** | REST + DB, `/mini-app/catalog`, etc. | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (see root `Procfile`) |
| **Mini App UI** | Flet web server + Flutter client; calls API via `MINI_APP_API_BASE_URL` | `python -m mini_app.main` |

Do not point Telegram at the API origin for the Mini App button unless you have intentionally mounted the Flet UI there (this repo does not merge them).

## Public URL shape

- Railway assigns something like `https://your-mini-app-service.up.railway.app`.
- Flet mounts the app at path **`/`** when the default page name is used (empty `name` in `ft.run`).
- **Use this as `TELEGRAM_MINI_APP_URL`:** the **HTTPS root** of the Mini App service, e.g.  
  `https://your-mini-app-service.up.railway.app/`  
  (trailing slash optional; Telegram accepts the Web App URL without requiring `/mini-app` on the API host.)

The in-app routes (`/`, `/tours/...`, `/bookings`, etc.) are **client-side** Flet routes after the Flutter bundle loads, not separate FastAPI routes on the API server.

## Required environment variables (Mini App service)

Set these on the **Mini App UI** Railway service (not necessarily on the API service):

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | Yes (Railway injects) | Listen port. `mini_app/main.py` reads `PORT` or `FLET_SERVER_PORT`. |
| `MINI_APP_API_BASE_URL` | Yes | Public **HTTPS** base URL of the **API** service, no trailing slash, e.g. `https://your-api.up.railway.app`. All `httpx` calls use this. |
| `MINI_APP_DEV_TELEGRAM_USER_ID` | Yes for full flows | Telegram user id used until init-data auth exists; must match a user your API accepts. |
| `MINI_APP_DEFAULT_LANGUAGE` | Optional | Default `en`. |
| `MINI_APP_TITLE` | Optional | Window/title string. |
| `FLET_HOST` | Optional | Bind address; defaults to `0.0.0.0` when `PORT` is set (already suitable for Railway). |

**Database:** the Mini App UI process does **not** need `DATABASE_URL` unless you add server-side DB access later.

## Recommended Railway settings (Mini App service)

1. **Root directory:** repository root (same as API), or the directory that contains `mini_app/` and `pyproject.toml`.
2. **Build:** install dependencies (`pip install -r requirements.txt` or Nixpacks equivalent).
3. **Start command:**

   ```bash
   python -m mini_app.main
   ```

   Equivalent:

   ```bash
   python -m mini_app
   ```

4. **Networking:** generate a public domain (HTTPS). Copy that URL into Telegram Bot settings / `.env` as `TELEGRAM_MINI_APP_URL` on the **bot** runtime (the process that runs `app.bot.runner`, not necessarily the Mini App container).

## Local smoke (before Railway)

From project root, with API running on port 8000:

```powershell
$env:MINI_APP_API_BASE_URL = "http://127.0.0.1:8000"
python -m mini_app.main
```

Open the printed local URL (or `http://127.0.0.1:<port>/`). You should see the **Tours catalog** UI.

Simulate container binding:

```powershell
$env:PORT = "8080"
$env:FLET_HOST = "0.0.0.0"
$env:MINI_APP_API_BASE_URL = "http://127.0.0.1:8000"
python -m mini_app.main
```

## Smoke checks (staging)

1. **Opens UI:** browser or Telegram opens the Mini App URL without 404; Flutter/Flet shell loads.
2. **Catalog loads:** catalog lists tours (requires API + DB seeded, e.g. `TEST_BELGRADE_001`).
3. **Detail opens:** navigate to a tour detail from the catalog.
4. **Preparation opens:** continue to preparation from detail.
5. **Telegram path:** users can return to the private bot chat; support/help copy in the Mini App still points to the bot for human help (no change from deployment).

## What this does not do

- Does not add Step 8 features.
- Does not merge API and Flet into one process (recommended: keep two Railway services).
- Does not change booking/payment rules or API semantics.

## Troubleshooting

| Symptom | Check |
|--------|--------|
| Blank white screen | `no_cdn=True` is already set in `mini_app/main.py`; ensure outbound CDN is not blocked, or try another network. |
| Catalog empty | API `/mini-app/catalog` and `MINI_APP_API_BASE_URL` pointing to the same API the browser can reach; CORS on API for local dev (already when `APP_DEBUG` / `APP_ENV=local`). |
| CORS on staging | API must allow the Mini App **origin** (HTTPS Mini App hostname). Configure `CORSMiddleware` / allowed origins for production separately if needed. |
| Wrong user in API | `MINI_APP_DEV_TELEGRAM_USER_ID` matches a user known to the API. |
