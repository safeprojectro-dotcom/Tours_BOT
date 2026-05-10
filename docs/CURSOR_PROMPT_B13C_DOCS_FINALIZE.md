# CURSOR_PROMPT_B13C_DOCS_FINALIZE

Finalize B13C documentation only.

B13C main design doc is already created:

`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`

This finalize pass must add continuity docs only.

## Required updates

Update:

`docs/B13_CHANNEL_ADAPTER_DESIGN.md`

Add a short B13C pointer:
- publish attempt/audit design exists;
- B13C is docs-only;
- no attempt table implemented yet;
- no behavior change;
- next implementation should start from B13D/B13E only by explicit decision.

Update:

`docs/CHAT_HANDOFF.md`

Add B13C completed entry:
- B13C publish attempt/audit design completed.
- Main doc: `docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`.
- Design covers:
  - current publish baseline;
  - attempt audit purpose;
  - duplicate-send risk;
  - idempotency concept;
  - retry policy;
  - transaction/side-effect boundary;
  - future implementation options.
- No code.
- No tests.
- No migrations.
- No publish behavior changes.
- No publish readiness changes.
- No Mini App.
- No booking/payment/orders.
- Recommended next: decide whether to implement attempt table/audit later; do not auto-start migration/code.

Create/update:

`docs/HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md`

Include:
- checkpoint;
- docs created/updated;
- key design decisions;
- no-goals preserved;
- recommended next options:
  1. B13D — publish attempt table/repository/service skeleton, if approved;
  2. B13D-alt — channel preview payload read model, if avoiding migrations;
  3. Production publish smoke / content QA before audit implementation.

Update:

`docs/CURSOR_PROMPT_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`

If prompt file is truncated, close it and add completion note:
- design doc created;
- no code/tests/migrations;
- no behavior change.

Optional:

Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` only if you want to formally track:
- whether publish attempt table is mandatory before retries/multi-channel;
- exact idempotency key composition;
- transaction strategy: pre-send attempt row vs post-send persistence.

If not updated, say so.

## Forbidden

Do not change app code.
Do not change tests.
Do not add migrations.
Do not change publish behavior.
Do not change publish readiness.
Do not add retry logic.
Do not add new channels.
Do not touch Mini App.
Do not touch booking/payment/orders.
Do not call external services.
Do not publish anything.

## After completion report

Return:

1. docs changed;
2. whether OPEN_QUESTIONS changed and why;
3. recommended next step;
4. `git status --short`;
5. `git diff --stat`;
6. confirmation:
   - docs-only;
   - no code;
   - no tests;
   - no migrations;
   - no publish behavior changes;
   - no readiness changes;
   - no retry logic;
   - no new channels;
   - no Mini App;
   - no booking/payment/orders;
   - no external calls.