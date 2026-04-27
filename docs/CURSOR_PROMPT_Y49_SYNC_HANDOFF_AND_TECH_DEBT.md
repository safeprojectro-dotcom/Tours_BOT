You are continuing Tours_BOT after creating:

- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md

Task:
Sync Y49 into continuity docs only.

Read:
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Update only:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Requirements:
1. Add Y49 as accepted design gate.
2. State that outbound messaging is the FIRST external side effect.
3. State messaging is ONLY allowed inside execution attempt.
4. State messaging requires:
   - explicit permission
   - idempotency
   - audit
5. State messaging MUST NOT be triggered by:
   - operator intent
   - request creation
   - attempt creation
6. Preserve all Y38–Y48 constraints.
7. State next safe step:
   - controlled messaging implementation (single channel, idempotent)

No code changes.

After editing, report:
- files changed
- exact Y49 continuity text added
- next safe step