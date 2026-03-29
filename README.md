# Tours_BOT

Initial Phase 1 backend skeleton for the Tours_BOT MVP.

## Included in this step

- FastAPI backend application entrypoint
- environment-based settings
- PostgreSQL SQLAlchemy setup
- Alembic initialization
- `/health` and `/healthz` endpoints
- modular backend folder layout

## Not included yet

- Telegram bot handlers
- Mini App UI
- booking logic
- payment logic
- admin business features
- content publication features

## Local run

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -e .
```

### 3. Prepare local environment variables

Copy `.env.example` to `.env` and adjust values if needed.

Required local baseline:
- `APP_ENV=local`
- `DATABASE_URL` points to a local PostgreSQL database
- `DATABASE_CONNECT_TIMEOUT` stays low enough for fast readiness failures

### 4. Prepare local PostgreSQL

This project is Postgres-first even in local development.

Expected local database target:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/tours_bot
```

Manual setup expectations:
- PostgreSQL is installed and running locally
- the `tours_bot` database exists
- the configured user has permission to connect and run migrations

### 5. Verify Alembic foundation

Check that Alembic is wired and can read the project configuration:

```powershell
python -c "from alembic.config import Config; Config('alembic.ini')"
```

When business models are introduced in later steps, the normal local migration workflow should be:

```powershell
python -m alembic revision --autogenerate -m "describe change"
python -m alembic upgrade head
```

At this stage, Alembic is initialized but no business-table migration is created yet by design.

### 6. Run the backend API

```powershell
python -m uvicorn app.main:app --reload
```

### 7. Verify health endpoints

- `GET /health` should return process liveness
- `GET /healthz` should return readiness and fail with `503` if PostgreSQL is unavailable
