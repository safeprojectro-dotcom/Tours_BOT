# Deployment

## Project
Tours_BOT

## Purpose
Document local development setup, staging deployment, production deployment assumptions, and environment strategy for Tours_BOT.

This document covers:
- local environment
- GitHub readiness
- Railway staging deployment
- Railway production deployment
- environment variables
- health checks
- migrations
- process model
- deployment validation

---

## 1. Deployment Model

The project uses three environments:
- local
- staging
- production

The deployment path is:
1. local development
2. commit to GitHub
3. deploy to Railway staging
4. validate staging
5. deploy to Railway production

---

## 2. Process Model

The system should be deployable with separate logical processes:

- backend
  - FastAPI API
  - health endpoints
  - webhook/public endpoints
  - Mini App backend endpoints

- bot
  - Telegram delivery logic
  - private/group message processing

- workers
  - reservation expiry
  - reminders
  - waitlist release
  - publication jobs
  - scheduled automation

The exact Railway process mapping may vary, but responsibilities must remain separate.

---

## 3. Database Strategy

PostgreSQL is the primary target database.

Rules:
- local development should be Postgres-first
- staging uses Railway Postgres
- production uses Railway Postgres or equivalent production Postgres
- SQLite must not be used to validate booking/payment-critical logic

Critical flows that must be verified against PostgreSQL:
- reservation creation
- seat counting
- reservation expiry
- payment state updates
- waitlist release
- migration behavior
- concurrency-sensitive booking logic

---

## 4. Local Development

## Local requirements
Recommended local setup:
- Python
- PostgreSQL
- Redis if used in workers/background logic
- environment variables from local `.env`
- Alembic migrations
- local run commands for backend/bot/workers

## Local PostgreSQL bootstrap
Local development must be PostgreSQL-first.

Minimum local assumptions:
- PostgreSQL is installed and running
- a local database named `tours_bot` exists
- the configured local user can connect and run migrations
- `.env` points `DATABASE_URL` at the local Postgres instance

Recommended local baseline:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/tours_bot
DATABASE_CONNECT_TIMEOUT=5
```

SQLite may be used temporarily only for non-critical convenience work, but it must not be treated as the validation target for booking, payment, waitlist, or concurrency-sensitive behavior.

## Local run expectations
Local environment must support:
- backend startup
- DB connection
- migrations
- health endpoints
- test execution
- bot logic development assumptions
- Mini App backend support

## Local verification checklist
- backend starts
- DB connection works
- migrations apply successfully
- `/health` works
- `/healthz` works
- tests run
- settings validation behaves correctly

## Local bootstrap workflow
Recommended local bootstrap order:
1. create and activate a virtual environment
2. install dependencies with `python -m pip install -e .`
3. copy `.env.example` to `.env`
4. verify local PostgreSQL is reachable
5. verify Alembic configuration loads
6. run migrations when schema revisions exist
7. start the backend locally
8. check `/health` and `/healthz`

---

## 5. GitHub Readiness

Repository must include:
- `.gitignore`
- `.env.example`
- docs
- migrations
- tests
- stable module structure

Recommended Git discipline:
- commit small safe increments
- do not mix architecture changes with many unrelated features
- keep deployment-related config versioned
- document new env vars when added

---

## 6. Environment Variables

## Required categories
Environment variables should include at least:

### App
- APP_ENV
- APP_DEBUG if used
- BASE_URL if needed

### Database
- DATABASE_URL

### Redis / queue
- REDIS_URL if used

### Telegram
- TELEGRAM_BOT_TOKEN
- TELEGRAM_WEBHOOK_SECRET if used
- TELEGRAM_WEBHOOK_BASE_URL or equivalent

### Payments
- PAYMENT_PROVIDER
- PAYMENT_SECRET / API KEY
- PAYMENT_WEBHOOK_SECRET if applicable

### Content/publication
- publication credentials as needed

### Admin/security
- admin-related secrets if needed

All values must be loaded through application settings/config, not ad hoc environment reads scattered across modules.

---

## 7. Health Endpoints

Minimum endpoints:
- `/health`
- `/healthz`

Expected usage:
- local smoke check
- Railway staging validation
- production readiness verification

These endpoints should remain lightweight and reliable.

---

## 8. Migrations

Alembic is the migration authority.

Rules:
- model changes must be reflected through migrations
- migrations must be tested locally first
- migrations must be verified in Railway staging before production
- migration rollback/recovery approach should be known before critical production rollout

## Local migration workflow
Expected local workflow:
1. update or add SQLAlchemy models/metadata in the application
2. generate a migration with Alembic
3. review the generated migration before applying it
4. apply the migration locally on PostgreSQL
5. verify schema consistency and app startup

Reference commands:

```powershell
python -m alembic revision --autogenerate -m "describe change"
python -m alembic upgrade head
```

For this current Phase 1 foundation step:
- Alembic is initialized
- application metadata is wired into `alembic/env.py`
- no business-table migration is expected yet because business models are intentionally not implemented

Migration checks:
- fresh DB migration
- upgrade path
- schema consistency
- no destructive assumption without review

---

## 9. Railway Staging Deployment

## Purpose
Railway staging is the first hosted environment where real deployment assumptions are validated.

## Staging goals
Validate:
- backend startup
- environment variable configuration
- Railway Postgres connection
- migrations
- health endpoints
- Telegram webhook routing
- payment sandbox
- worker execution
- Mini App entry assumptions
- admin access assumptions

## Staging checklist
- app deploys successfully
- backend process starts
- worker process assumptions are valid
- DB connects successfully
- migrations apply
- `/health` works
- `/healthz` works
- webhook reachable
- payment sandbox works
- reminder/expiry flow can be tested

---

## 10. Production Deployment

Production deployment must happen only after:
- staging validation is complete
- webhook setup is confirmed
- payment sandbox/testing is satisfactory
- migrations are verified
- release checklist is approved
- rollback plan exists

Production validation should include:
- backend startup
- correct env vars
- correct bot token
- correct webhook URL
- correct database connection
- correct process startup
- health endpoints
- smoke tests of critical flows

---

## 11. Release And Rollback

Release readiness must be tracked through:
- `docs/RELEASE_CHECKLIST.md`

Rollback planning should include:
- deploy rollback trigger conditions
- DB migration risk awareness
- webhook rollback awareness
- previous working release identification
- smoke check after rollback if needed

---

## 12. Deployment Test Layers

## Local terminal tests
- unit tests
- integration tests
- migrations
- health endpoints
- config validation

## Local manual tests
- Telegram private flow
- Telegram group behavior
- Mini App open/browse/reserve
- admin screens/flows if present

## Staging tests
- webhook
- Postgres
- workers
- health endpoints
- payment sandbox
- Mini App launch

## Release checks
- production webhook validation
- payment safety
- multilingual smoke tests
- waitlist
- handoff
- rollback readiness

---

## 13. Immediate Deployment Priorities

Before advanced features, deployment foundation must support:
- repo readiness
- env strategy
- Postgres-first setup
- Alembic
- health endpoints
- Railway-compatible startup
- documented process model

---

## 14. Operational Notes

Update this document when:
- new env vars are introduced
- process model changes
- deployment flow changes
- Railway setup changes
- DB strategy changes
- production rollout strategy changes
