You are continuing the existing Tours_BOT project as strict continuation.

Task:
Implement a narrow fix for Mini App Telegram identity resolution.

Confirmed from previous debug:
- Catalog works.
- User-scoped pages fail:
  - /bookings
  - /my-requests
  - /settings
- Identity is not resolved in MiniAppShell at startup or route-change.
- API client then sends user-scoped requests without identity.
- Backend receives missing telegram_user_id.
- Confirmed technical issue:
  page.query.to_dict exists but is not callable and page.query is not mapping, so current Flet query extraction returns empty.
- Do NOT restore unsafe fallback.
- Fail-closed behavior must remain.

==================================================
SOURCE OF TRUTH
==================================================

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- mini_app/app.py
- mini_app/api_client.py
- mini_app/config.py
- app/api/routes/mini_app.py

Do not work on supplier marketplace or booking/payment core.

==================================================
BEFORE CODING
==================================================

Report briefly:
- Current state
- Why this is the next safe step
- Likely files changed
- Risks
- What remains postponed

==================================================
IMPLEMENTATION GOAL
==================================================

Fix runtime identity extraction from Flet surfaces only.

Implement a robust helper that safely extracts query-like data from:

- page.route
- page.url
- page.query
- page.query_string if present
- page.client_storage/session only if already used safely in the project

The helper must handle:
- string query
- object with non-callable to_dict
- object with attributes
- iterable key/value pairs if supported
- URL fragment with query
- URL-encoded tgWebAppData/initData payload if already present in route/url

==================================================
SECURITY RULES
==================================================

Do NOT:
- add shared dev fallback
- trust arbitrary telegram_user_id from public browser outside current existing dev behavior
- load bookings/requests/settings without identity
- log raw initData
- change backend business semantics
- change booking/payment/RFQ logic

Keep:
- fail-closed if identity cannot be extracted
- safe trace behind MINI_APP_DEBUG_TRACE only
- no noisy debug probes

==================================================
EXPECTED BEHAVIOR
==================================================

When Mini App is opened from Telegram:
- identity should be extracted from the available Flet runtime surface
- same identity should persist across route changes:
  - /
  - /bookings
  - /my-requests
  - /settings
- API client should include telegram_user_id for user-scoped calls
- backend should no longer receive empty telegram_user_id for those screens

If identity still cannot be extracted:
- user-scoped screens remain blocked
- safe trace should show failure reason/source under MINI_APP_DEBUG_TRACE only

==================================================
FILES LIKELY TO CHANGE
==================================================

Expected:
- mini_app/app.py

Possible only if needed:
- mini_app/api_client.py
- mini_app/config.py
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Do NOT change:
- booking services
- payment services
- RFQ/custom request domain services
- supplier offer services

==================================================
TESTS / CHECKS
==================================================

Run:
- python -m compileall app mini_app

If tests exist for Mini App identity helpers, run them.
If no tests exist, add a small focused unit test for query extraction helper if practical.

Do not add broad test suite changes.

==================================================
AFTER CODING REPORT
==================================================

Report:
- Files changed
- Migrations: none expected
- Tests run
- Result
- Exact extraction path now supported
- Why fail-closed remains safe
- Compatibility notes
- What remains postponed