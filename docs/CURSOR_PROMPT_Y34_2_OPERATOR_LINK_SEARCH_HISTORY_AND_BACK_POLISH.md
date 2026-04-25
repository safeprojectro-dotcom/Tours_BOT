Continue Tours_BOT strict continuation.

Task:
Small UX polish for Telegram admin execution-link search navigation after results/no-results.

Context:
Y33 accepted search flow.
Y34.1 clarified prompt/result text/button labels.

Goal:
Make search result navigation safer and clearer.

Scope:
Text/buttons only if possible.

Improve:
1. On search results screen, keep:
   - Select tour buttons
   - Back to compatible list
   - New search
   - Manual tour_id/code input
   - Back

2. On no-results screen, keep:
   - New search
   - Back to compatible list
   - Manual tour_id/code input
   - Back

3. Button text:
   - "New search"
   - "Back to compatible list"
   - "Manual tour_id/code input"

Rules:
- No search logic changes.
- No FSM semantic changes unless needed for New search button.
- No callback payload expansion.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No migrations.
- No execution-link semantics changes.

Tests:
- search results include New search button
- no-results include New search button
- New search re-enters search prompt
- existing selection/confirmation still works
- callback length tests still pass

Report:
- files changed
- exact UX changes
- tests run