Перед кодом
Фаза: Phase 5 / Mini App MVP — deployment enablement for real Telegram Mini App launch.
Следующий безопасный шаг: publish the existing Flet Mini App as a real public UI entry without changing booking/payment business logic.
Этот срез: make the current `mini_app/` runnable as a standalone web service for Railway, define the correct public entry route, and keep backend/API and bot logic unchanged.

Контекст, который уже подтверждён:
- Railway backend API is live and healthy
- Railway Postgres is connected and seeded with TEST_BELGRADE_001
- Telegram private bot flow is working with the new bot
- CTA/button to open Mini App exists in chat
- BUT current public URLs `/`, `/app`, `/mini-app` on the backend return `Not Found`
- therefore Telegram Mini App cannot yet open a real UI
- we need a public Flet UI service URL, not JSON endpoints

Жёсткие границы scope
Не менять:
- service-layer booking rules
- reservation/payment business logic
- existing backend route semantics
- existing bot dialog logic except minimal URL wiring if needed
- migrations
- data model
- waitlist/handoff behavior
- admin scope

Нужно реализовать ТОЛЬКО deployment/public-entry slice для existing Flet Mini App.

Goal
Deliver a safe, documented way to run the current Flet Mini App as a real public web UI so Telegram can open it as Mini App instead of hitting backend JSON/404 routes.

Required work
1. Inspect current `mini_app/` structure and determine the minimal correct web entrypoint for Flet web hosting.
2. Make the Mini App runnable as a standalone web process suitable for Railway.
3. Add only the minimal files/config needed so a separate Railway service can run the Mini App UI.
4. Clearly define the public UI route/path that should open the catalog screen in browser/Telegram.
5. Keep backend API base URL configurable and continue pointing Mini App UI to the existing backend.
6. Do not merge backend and Mini App runtime into one ambiguous process unless absolutely necessary. Prefer a separate service/process if the current structure supports it.
7. Document the exact Railway deploy/start assumptions for the Mini App service.

Expected output
A user should be able to open a public URL in a browser and see the actual Flet Mini App UI (catalog screen), not JSON and not 404.

Implementation constraints
- reuse the already implemented Flet Mini App under `mini_app/`
- keep mobile-first UI unchanged unless a tiny adjustment is required for web entry
- no new product features
- no new business rules
- no fake HTML wrapper if Flet already provides the right runtime model
- no broad refactor
- no hidden magic
- environment-driven configuration only

Likely files in scope
- `mini_app/main.py`
- `mini_app/app.py`
- `mini_app/config.py`
- `pyproject.toml` or deployment-related config only if required
- optional dedicated Procfile / Railway note if necessary
- docs file for deployment instructions

Also add/update docs
Create:
- `docs/MINI_APP_RAILWAY_DEPLOY.md`

Include:
- purpose
- which process/service runs backend API
- which process/service runs Flet Mini App UI
- required env vars
- exact start command for Mini App service
- what URL should be used in Telegram as `TELEGRAM_MINI_APP_URL`
- smoke checks:
  - opens UI
  - catalog loads
  - detail opens
  - preparation opens
  - return to Telegram support path remains clear

Important
Do not implement Step 8.
This is still pre-Step-8 deployment work needed so the Mini App launch criterion is actually true.

Before coding
Briefly state:
1. current phase
2. why the current Telegram CTA is not enough
3. what exact deployment slice you will implement

After coding
Report:
1. files changed
2. exact run commands locally
3. exact Railway service/start command recommendation
4. exact public URL shape expected
5. what remains postponed