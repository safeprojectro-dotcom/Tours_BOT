Continue Tours_BOT Mini App identity issue.

After fix:
CURSOR_PROMPT_Y30_4L_MINI_APP_IDENTITY_QUERY_SURFACE_FIX

Result:
Still not working. User-scoped pages still fail:
- /bookings
- /my-requests
- /settings

Task:
Do NOT change code yet.
Analyze safe trace with MINI_APP_DEBUG_TRACE=True.

Need answer:
1. Is identity found at startup?
2. Which source is checked?
3. Which source wins/fails?
4. Is route/page.url/page.query/page.query_string empty in real Telegram runtime?
5. Is the Mini App launched through the expected Flet entrypoint?
6. Is assets/index.html actually used by Mini_App_UI deployment?

Strict rules:
- no unsafe fallback
- no booking/payment changes
- no RFQ/supplier changes
- no broad refactor

Output:
- exact root cause
- exact file to fix
- minimal fix proposal only