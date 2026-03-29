# Cursor Prompt - Phase 4 / Step 14

Execute Phase 4 / Step 14 and implement the code and tests exactly within that scope.

Keep it narrow:
- add only the departure-day reminder groundwork
- use only the existing telegram_private notification pipeline
- preserve explicit and idempotent state transitions
- keep it PostgreSQL-first
- keep business rules in services and worker code thin

Do not expand into:
- scheduler/orchestrator
- new channels
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications
- advanced retry policy engine
- post-trip reminders

After implementation, report:
1. files changed
2. tests run
3. results
4. what remains postponed
