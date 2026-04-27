Sync Y51 into continuity docs only.

Read:
- docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Update only:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Requirements:
1. Add Y51 as accepted design-only checkpoint.
2. State Y51 defines admin/operator visibility, audit hardening, and retry principles.
3. State no automatic retries.
4. State no hidden retry on read.
5. State retry must require a future explicit gate.
6. State next safe step: Y52 read/audit visibility implementation only, no retry execution.

No code changes.