Continue Tours_BOT after Y36.5 acceptance checkpoint.

Task:
Fix Telegram admin request date formatting polish.

Problem:
In /admin_requests and request detail, one custom request displays:
Travel date: 2026-04-28 - 2926-04-28

This looks like malformed display or bad test/seed data. Investigate safely.

Scope:
- Telegram admin UI formatting for custom requests.
- Optional read-only formatting helper only.
- No DB migration.
- No data mutation.
- No API semantic changes.
- No Mini App changes.
- No booking/payment changes.
- No execution-link changes.
- No supplier route changes.
- No identity bridge changes.
- No lifecycle/status/assignment changes.

Investigation:
1. Check how travel_date_start and travel_date_end are rendered in:
   - app/bot/handlers/admin_moderation.py
   - app/bot/messages.py
   - related schemas/services if formatting is upstream.
2. Determine if 2926 is actual DB data or formatting bug.
3. If actual DB data:
   - do not mutate production data.
   - display it safely as-is, but add no runtime “correction”.
   - document that it is data quality / seed issue if needed.
4. If formatting bug:
   - fix only formatting.

Desired display:
- If only start date: Travel date: YYYY-MM-DD
- If start and end date are equal: Travel date: YYYY-MM-DD
- If start and end differ: Travel date: YYYY-MM-DD → YYYY-MM-DD
- If missing: Travel date: -

Tests:
- request list/detail same start/end renders one date
- different start/end renders range
- missing date renders -
- no assignment behavior changes
- no callback changes

Run:
python -m compileall app tests/unit/test_telegram_admin_moderation_y281.py
python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops"

After implementation report:
- root cause
- files changed
- exact display changes
- tests run
- confirm no DB/API/Mini App/booking/payment changes