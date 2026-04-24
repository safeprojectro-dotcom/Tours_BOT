Continue existing Tours_BOT project as strict continuation.

We fixed a separate deployment/env issue:
Mini_App_UI had wrong production env:
MINI_APP_API_BASE_URL=http://127.0.0.1:8000

After removing/fixing it:
- Catalog works again.
- Language/settings basic UI works again.

Original issue remains:
User-scoped pages still fail identity:
- /bookings
- /my-requests
- /settings

Current task:
Collect and analyze safe identity trace with correct production API URL.

Do NOT change code yet.

==================================================
RULES
==================================================

- Do not restore unsafe fallback.
- Do not change booking/payment/RFQ/supplier logic.
- Do not change API contracts.
- Do not add debug probes.
- Use existing safe trace only.
- Fail-closed must remain.

==================================================
ENV ASSUMPTION
==================================================

Mini_App_UI must run with:

MINI_APP_DEBUG_TRACE=True

And backend URL must NOT be localhost:
MINI_APP_API_BASE_URL=https://toursbot-production.up.railway.app
or correct production default.

==================================================
TASK
==================================================

Analyze runtime evidence for identity flow.

Check Mini_App_UI logs and backend logs after Telegram mobile run:

Flow:
1. open catalog
2. open /bookings
3. open /my-requests
4. open /settings
5. attempt one language save

Need answer:
1. Does Mini_App_UI emit safe trace lines?
2. If no trace lines:
   - is logger level hiding info?
   - is MINI_APP_DEBUG_TRACE loaded by mini_app/config.py?
   - is trace function actually called during startup/route changes?
3. If trace lines exist:
   - which source was checked?
   - has_identity true/false?
   - source label?
4. Does API client include telegram_user_id?
5. Does backend receive telegram_user_id?
6. Is identity absent at Flet runtime or lost after routing?

==================================================
OUTPUT FORMAT
==================================================

Return:

1. Evidence table:

Step | Status | Evidence | Meaning
JS/Telegram | unknown/ok/fail | ... | ...
Flet runtime | ok/fail | ... | ...
API client | ok/fail | ... | ...
Backend | ok/fail | ... | ...

2. Exact root cause if proven.

3. If not proven, list exactly what trace is missing and what minimal logging visibility fix is required.

4. Do not propose business-logic changes.

==================================================
IMPORTANT
==================================================

If Mini_App_UI safe trace still does not appear in logs, the next fix should be logging visibility only, not identity logic.

If safe trace shows identity never reaches Flet runtime, next fix should target Telegram WebApp bootstrap/launch payload path.

If safe trace shows identity reaches Flet but API client omits it, next fix should target API client propagation only.