Y33.6A — Fix execution-link tour search input not handled.

Problem:
After Y33.6 deploy, Telegram admin flow:

/admin_published -> offer #5 -> Execution link -> Replace execution link -> Search compatible tours

Bot prompts:
"Send tour code or title. Optionally add date YYYY-MM-DD..."

User sends:
zzzz 2026-06-16

Expected:
No compatible tours found + guidance buttons.

Actual:
No response.

Railway logs show:
Update ... is not handled
No exception, webhook 200.

This means the text update is not routed to the expected FSM handler, or FSM state/context is cleared before input.

Investigate and fix narrowly.

Check:
1. Is AdminModerationState.awaiting_execution_link_tour_code_search registered in a Message handler?
2. Is that handler included in the admin_moderation router?
3. Does handler ordering allow it to run before generic admin text handlers?
4. Is FSM state cleared when rendering the search prompt?
5. Is state data preserving:
   - offer_id
   - mode create/replace
6. Does pressing "Search compatible tours" set the correct state?
7. Does repeated invalid/no-result text stay in the state or fail predictably?

Requirements:
- No search logic changes except routing/state fix.
- No filter changes.
- No execution-link semantics changes.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No migrations.
- Keep callback payloads compact.
- Keep no-results UX.

Add/adjust tests:
- pressing Search compatible tours sets AdminModerationState.awaiting_execution_link_tour_code_search
- text in that state is handled and sends no-results response
- text in that state with valid query sends results
- repeated no-results input still receives a response or state behavior is explicit
- existing code/title/date search tests still pass

Run:
python -m compileall app/bot/handlers/admin_moderation.py app/bot/messages.py app/bot/state.py tests/unit/test_telegram_admin_moderation_y281.py
python -m pytest tests/unit/test_telegram_admin_moderation_y281.py
python -m pytest tests/unit/test_supplier_offer_track3_moderation.py

Report:
- root cause
- files changed
- tests run
- whether no-results now routes through FSM handler