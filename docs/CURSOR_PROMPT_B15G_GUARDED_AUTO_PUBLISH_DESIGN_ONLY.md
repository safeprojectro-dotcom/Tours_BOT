# CURSOR_PROMPT_B15G_GUARDED_AUTO_PUBLISH_DESIGN_ONLY

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 81b65c5 docs: record publishing console prepare chain smoke
- aa1dc8 feat: add publishing console prepare chain action execution
- 9e4b8d docs: record prepare conversion chain production smoke
- fd4e25d feat: expose prepare conversion chain action affordances
- f8f146f feat: add guarded prepare conversion chain admin endpoint

Closed:
- B16D2C — guarded admin POST endpoint for prepare_conversion_chain
- B16D2D — read model/action affordance metadata
- B16D2E — Railway production smoke passed
- B15E2 — publishing console prepare_conversion_chain action execution
- B15E2 smoke — Railway production smoke passed

Now implement:

# B15G — Guarded Auto-Publish Design Only

## Critical instruction

This is a DOCUMENTATION / DESIGN GATE ONLY.

Do NOT implement runtime code.

Do NOT add endpoints.

Do NOT add scheduler.

Do NOT add Telegram publish/send/retry.

Do NOT add auto-publish execution.

Do NOT change business logic.

Do NOT create migration.

---

## Goal

Create a design document for future guarded auto-publish behavior in the publishing console / supplier offer funnel.

The document must define:

1. What “auto-publish” means and does NOT mean.
2. Which gates must be satisfied before auto-publish may even be proposed.
3. Why auto-publish must not bypass admin approval.
4. How existing prepare_conversion_chain, publishing console, and Telegram showcase publish flows fit together.
5. Which future implementation steps would be required.
6. Which risks, rollback rules, and audit requirements apply.
7. What remains explicitly out of scope now.

---

## Architectural invariants to preserve

The design must preserve all existing project rules:

- PostgreSQL-first.
- Service layer owns business rules.
- Repository layer remains persistence-only.
- UI / route / publishing console must not duplicate business logic.
- Telegram channel is a softer showcase / discovery surface.
- Mini App / execution catalog layer is strict execution truth.
- visibility != bookability.
- Public publish and Telegram send must remain separate from internal conversion preparation.
- No hidden publish.
- No hidden order/payment/reservation mutation.
- No hidden seat mutation.
- No hidden supplier execution retry.
- Layer A booking/payment remains the only authority for orders, reservations, payments, and seats.
- Payment-entry/reconciliation remains the only payment authority.

---

## Required references

Inspect and align with current docs before writing:

- docs/CHAT_HANDOFF.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md
- docs/B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md
- docs/B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md
- docs/HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/BUSINESS-план-v2.txt if present

If some referenced docs do not exist in the repo, report and continue with available docs.

---

## Document to create

Create:

docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md

Also update minimally:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if a real design debt/open decision is introduced
- optionally docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md if it is the current B15 continuity checkpoint

Do not update code files.

---

## Required content of B15G design doc

The design document must include these sections:

### 1. Status and scope

- Status: design only / not implemented.
- No runtime behavior added.
- No auto-publish enabled.
- No Telegram send/publish/retry added.

### 2. Definition

Define three separate concepts:

1. Internal conversion preparation
   - prepare_conversion_chain
   - bridge/catalog/execution-link readiness
   - no Telegram I/O

2. Manual publish
   - admin explicitly confirms Telegram showcase publish
   - public side effect

3. Future guarded auto-publish
   - system may propose or schedule publication only after strict gates
   - must still remain auditable and reversible
   - must not silently publish from supplier input

### 3. Current foundation

Summarize current closed foundation:

- B16D2C endpoint:
  POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

- B16D2D action affordances

- B16D2E smoke result

- B15E2 publishing console action execution

- B15E2 smoke result

Mention that these support internal readiness, not public auto-publish.

### 4. Proposed future auto-publish gates

Define required gates before future auto-publish may be allowed.

At minimum:

- supplier offer lifecycle approved or published-ready
- packaging_status approved_for_publish
- content quality review has no blocking issues
- media review approved or safe text-only fallback explicitly selected
- publish_safe status acceptable for target channel
- showcase preview generated and valid
- prepare_conversion_chain plan status already_prepared or safe partial state as explicitly defined
- active tour bridge present
- catalog tour open_for_sale where required
- active execution link present where the channel CTA expects booking
- no future-departure blocker
- no catalog visibility blocker
- no B8 same-offer/date conflict
- no open critical incident/disruption flag
- no unresolved supplier clarification request
- no admin-level publish hold flag
- idempotency key strategy defined
- rollback / unpublish strategy defined
- audit actor defined

### 5. Explicit non-gates / not enough alone

Explain that these are NOT sufficient by themselves:

- supplier submits offer
- AI generated content
- packaging generated but not approved
- tour bridge exists
- tour is open_for_sale but no execution link
- offer is published historically
- publishing console row exists
- action affordance enabled
- dry_run success only

### 6. Proposed future modes

Define possible future modes:

1. Disabled
   - default mode

2. Suggest only
   - system recommends “ready to publish”
   - admin still clicks publish

3. Queue for approval
   - system places item into an approval queue
   - admin approves batch

4. Scheduled publish after explicit admin approval
   - admin approves now, publish later
   - scheduler executes only approved item

5. Fully automatic publish
   - not approved for MVP
   - requires separate future decision gate

Clearly state that current recommendation is:
- Disabled / Suggest only
- No full automatic publish in current scope

### 7. Audit and idempotency requirements

Define:

- publish attempt audit required
- action code required
- actor_surface required
- requested_by required for human-triggered actions
- idempotency_key required for publish attempts
- payload fingerprint required
- before/after state snapshots recommended
- response from provider stored safely
- retry policy explicit and manual first
- no silent retries for public publishing without future gate

### 8. Failure and rollback

Define failure handling:

- Telegram API failure
- duplicate publish attempt
- partially persisted publish attempt
- channel post sent but DB update failed
- DB update succeeded but Telegram post failed
- stale content detected after approval
- tour becomes not bookable after approval
- execution link removed after approval
- incident/disruption after scheduled approval

Define rollback options:
- mark publish failed
- disable CTA / fallback landing
- manual delete/edit channel post if available
- unpublish/close showcase state
- document manual cleanup

### 9. Data model implications for future implementation

Design only. No migration now.

List possible future fields/tables if needed:

- auto_publish_policy
- publish_hold_reason
- approved_for_scheduled_publish_at
- scheduled_publish_at
- scheduled_publish_by
- auto_publish_mode
- auto_publish_gate_snapshot_json
- auto_publish_decision_log
- publish_batch_id

Mark as future only.

### 10. API implications for future implementation

Design only. No endpoint now.

Possible future endpoints:

- GET publish readiness
- POST propose auto-publish
- POST approve scheduled publish
- POST cancel scheduled publish
- POST execute scheduled publish worker-safe

Mark as future only.

### 11. Testing strategy for future implementation

Define required future tests:

- gate evaluation unit tests
- no publish when any gate fails
- stale gate recheck immediately before send
- idempotent publish execution
- duplicate prevention
- Telegram failure handling
- rollback/manual cleanup path
- no Layer A mutation
- no hidden prepare_conversion_chain execution unless explicitly configured
- smoke test on safe offer
- production dry_run before live

### 12. Decision / recommendation

End with a clear recommendation:

- Current B15G status: design accepted, no implementation.
- Future next safe implementation should start with read-only publish readiness evaluation, not actual auto-publish.
- Public Telegram publish must remain explicit until a separate go/no-go decision.

---

## Strict boundaries

Do NOT implement:

- code
- route
- schema
- service
- worker
- scheduler
- Telegram Bot API calls
- publish execution
- retry execution
- migration
- tests unless purely docs lint exists in project

This step is docs only.

---

## Before editing docs

Report briefly:

1. Which docs exist and were inspected.
2. Where current B15/B16 continuity is recorded.
3. Proposed new doc outline.
4. Files to change.

Then write docs.

---

## Verification

Run only lightweight checks:

- git diff -- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- optional markdown/manual review

Do not run code tests unless no code changes were accidentally made and you want to verify no code touched.

---

## After writing

Report:

1. Files changed.
2. Summary of design.
3. Explicitly confirm no runtime code changed.
4. Open decisions/debt added, if any.
5. Recommended next block.

Do not commit.
Do not push.