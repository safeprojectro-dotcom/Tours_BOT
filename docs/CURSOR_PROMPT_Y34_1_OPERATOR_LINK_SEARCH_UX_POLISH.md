Continue Tours_BOT strict continuation.

Task:
Small UX polish for Telegram admin execution-link tour search messages/buttons.

Context:
Y33 accepted:
- code search works
- title search works
- YYYY-MM-DD date hint works
- no-results UX works
- FSM routing fix accepted

Scope:
Improve only text clarity.

Polish:
1. Prompt text:
From:
"Send tour code or title. Optionally add date YYYY-MM-DD for offer #5. Search stays limited to compatible tours."

To clearer wording:
"Send tour code or title. You can also add date YYYY-MM-DD. Search stays limited to compatible tours for offer #5."

2. Result header:
From raw:
Compatible tour search results for offer #5 (replace) — "SMOKE 2026-06-16" — page 1

To clearer:
Search results for offer #5
Mode: replace
Query: SMOKE
Date: 2026-06-16
Page: 1

3. Candidate button:
From:
Select tour #3

To:
Select tour #3 (SMOKE_FULL_BUS_001)

Rules:
- Text/UI only.
- No search logic changes.
- No FSM changes unless unavoidable.
- No callback payload changes except keep existing compact callbacks.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No migrations.

Tests:
- update existing message/assertion tests
- ensure callback length tests still pass
- run focused Telegram admin moderation tests

Report:
- files changed
- exact text changes
- tests run