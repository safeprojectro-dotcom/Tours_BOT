Continue Tours_BOT strict continuation.

Identity issue is fixed:
- has_identity=True
- custom-requests endpoint receives telegram_user_id
- POST /mini-app/custom-requests returns 201

New issue:
After creating a custom request, it does not appear in My requests UI.
Runtime evidence:
- POST /mini-app/custom-requests HTTP 201
- subsequent GET /mini-app/custom-requests?telegram_user_id=... HTTP 200
But UI still does not show the newly created request.

Task:
Investigate and fix only My requests refresh/rendering after custom request creation.

Rules:
- Do NOT touch identity bridge.
- Do NOT touch booking/payment Layer A.
- Do NOT change RFQ/supplier semantics.
- Do NOT change backend contracts unless evidence proves response mismatch.
- Keep fail-closed behavior.

Investigate:
1. mini_app screen that creates custom request.
2. mini_app My requests screen/list rendering.
3. API client custom request create/list DTO parsing.
4. Whether list is refreshed after successful POST.
5. Whether newly created request status/type is filtered out by UI.
6. Whether backend returns created item in GET response.

Implementation goal:
After successful custom request creation:
- user sees success state
- My requests page refreshes or reloads list
- newly created request appears if backend returns it
- empty state appears only when list is truly empty

Checks:
- python -m compileall app mini_app
- focused unit test if existing patterns allow

Report:
- files changed
- migrations none
- root cause
- tests run