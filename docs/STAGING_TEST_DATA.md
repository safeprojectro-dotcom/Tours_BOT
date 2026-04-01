# Staging test data (manual utilities)

## Purpose

Operational scripts under `scripts/` load **one** synthetic tour (`TEST_BELGRADE_001`) into PostgreSQL so you can smoke-test Mini App and API on staging (e.g. Railway) when the catalog is otherwise empty.

They are **not** part of application startup, migrations, or automated deploys. Run them only when you intentionally want test data.

## Scripts

| Script | Action |
|--------|--------|
| `scripts/seed_test_belgrade_tour.py` | Creates or replaces the test tour and **two** boarding points. If the tour already exists, it deletes **only** rows tied to that tour (orders, waitlist, content items, translations, boarding points) and rewrites the tour + boarding data. Does not touch other tours. |
| `scripts/delete_test_belgrade_tour.py` | Deletes **only** `TEST_BELGRADE_001` and related rows (same scope as above). |

Tour code is always `TEST_BELGRADE_001`.

## Prerequisites

- Project dependencies installed (`pip install -r requirements.txt` or your usual env).
- `DATABASE_URL` pointing at the target database (see `.env.example`).
- From repository **root**, so imports resolve and `.env` is found by `app` settings.

## Run locally

PowerShell (example):

```powershell
cd D:\path\to\Tours_BOT
.\.venv\Scripts\python.exe scripts\seed_test_belgrade_tour.py
```

Delete after testing:

```powershell
.\.venv\Scripts\python.exe scripts\delete_test_belgrade_tour.py
```

## Run against Railway (temporary `DATABASE_URL`)

1. Copy the Postgres connection string from Railway (variable often named `DATABASE_URL`).
2. In a **local** shell session only (do not commit secrets):

   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME"
   cd D:\path\to\Tours_BOT
   .\.venv\Scripts\python.exe scripts\seed_test_belgrade_tour.py
   ```

3. Verify Mini App / API (e.g. `GET /mini-app/catalog` shows the test tour).
4. Remove test data when finished:

   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME"
   .\.venv\Scripts\python.exe scripts\delete_test_belgrade_tour.py
   ```

5. Close the shell or `Remove-Item Env:DATABASE_URL` so the URL is not left in the environment.

Use the same driver prefix as your app (`postgresql+psycopg://` is typical for this project).

## Safety notes

- **Do not** add these scripts to `Procfile`, Docker `CMD`, CI, or migration hooks.
- **Do not** rely on them in production; they are for manual staging smoke tests.
- Re-seeding deletes **orders (and cascaded payments / notification outbox rows)** for this tour only, so you get a clean boarding layout for repeated smoke runs.

## What these scripts do not do

- They do not change FastAPI routes, services, or Mini App UI.
- They do not run Alembic or modify schema.
