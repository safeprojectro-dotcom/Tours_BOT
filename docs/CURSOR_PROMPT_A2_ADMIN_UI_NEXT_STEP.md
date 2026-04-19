Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- handoff/docs sync checkpoint
- U1–U3
- V1–V4
- W1–W3
- X1–X2
- A1
- key hotfixes and production fixes

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не делай broad redesign.

## Continuity base
Считать источниками истины:
- current codebase
- updated `docs/CHAT_HANDOFF.md`
- updated `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/CHECKPOINT_UVXWA1_SUMMARY.md`

Уже принято:
- A1 улучшил admin custom request list/detail scanability
- V1–V4 уже дают rich operational truth
- W3 уже даёт prepared customer message preview for admin
- supplier/customer semantics already separated and must stay separated

## Exact next safe step

Implement a medium-sized coherent block:

# A2 — Admin Request Detail Actionability Pass

### Goal
Improve admin custom-request detail usability by making the already-existing operational truth easier to act on visually, especially around:
- primary ops decision
- what is blocking progress
- what is waiting on supplier
- what is waiting on customer
- what bridge/customer continuation context exists
- what prepared customer message currently exists

This is an admin/internal UI/read block.
Not a workflow redesign.
Not a payment block.
Not a bridge redesign.
Not a supplier model redesign.
Not a full admin-panel rewrite.

## Why A2 after A1
A1 improved:
- list scanability
- filterability
- section structure
- safe prepared-message visibility

But admin detail can still likely be improved in one coherent next step by making **“what do I do now?”** and **“what is the current bottleneck?”** more obvious.

## Block scope

### 1. Add a stronger “Current operational decision” block
In admin request detail, create a compact high-signal block near the top that summarizes:
- current action focus
- whether internal ops attention is needed
- whether the request is terminal
- whether the current state is mostly waiting on supplier / internal review / customer continuation / closed follow-through

Use existing V2/V3/V4 truth.
Do not invent new logic.

### 2. Add clearer blocker / waiting-state presentation
Use existing read-side truth to make it easy to see whether the request is:
- awaiting supplier proposals
- awaiting internal review/resolution
- bridge-related but not payment-ready
- may have customer continuation path
- commercially resolved but without visible progression evidence
- terminal/closed

This should be visual/readability work, not backend redesign.

### 3. Improve “prepared customer message” placement and usefulness
W3 already provides prepared message preview.
In A2, make that block more operationally useful:
- easier to find
- clearly secondary to ops actionability
- clearly marked as prepared/internal only
- not visually confused with customer read receipt or sent delivery

Do not change W3 semantics.

### 4. Make bridge/commercial context more decision-friendly
Surface existing bridge/commercial context more clearly in detail:
- whether a bridge record exists
- what bridge status means in internal terms
- whether this suggests possible customer continuation
- whether payment readiness is still explicitly not implied

No new bridge logic.
No Layer A reads unless already safely in the current read-side model.

### 5. Keep it read-only and internal
This block must remain:
- internal/admin-facing
- read-only
- grounded in existing fields
- free of new mutating controls unless something trivial and already-existing is merely repositioned

## What this block must NOT do

Do NOT:
- redesign admin architecture broadly
- redesign RFQ workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign supplier workflow
- add new major backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- invent new workflow actions not backed by existing truth
- imply payment readiness/customer completion when not evidenced

## Likely files/modules to touch

Only where needed:
- `app/admin/custom_requests_ops.html`
- maybe tiny UI formatting helpers if already used by admin surface
- focused tests for admin UI/readability if practical

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows
- core read-side services unless a tiny additive helper is clearly justified

## Required design guardrails

### A. Reuse existing truth
The point of A2 is to expose V2/V3/V4/W3 better in admin detail.
Do not create shadow logic in the template.

### B. No fake actionability
Do not imply:
- payment is ready
- customer already acted
- supplier selection happened if not true
- message was delivered

### C. Strong next-step clarity, low clutter
The admin should be able to understand quickly:
- what needs action now
- what is blocked / waiting
- what is informational only
- what customer-facing message is currently prepared

### D. Keep it medium-sized and coherent
This is one admin detail actionability/readability block.
Do not smuggle in unrelated redesign.

## Before coding
Output briefly:
1. current project state
2. what A1 already solved
3. exact A2 block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current admin request detail after A1
2. identify the highest-value “what now?” gaps
3. add one compact operational decision block
4. tighten blocker/waiting-state presentation
5. reposition/clarify prepared customer message preview
6. keep bridge/commercial context readable and safe
7. add focused tests if practical
8. keep docs updates minimal unless truly needed

## Tests required

Add focused tests only where meaningful:
1. admin detail shows a clearer current decision/actionability block
2. prepared customer message preview still does not imply delivery
3. blocker/waiting-state wording does not imply payment readiness
4. existing operational hints remain consistent and non-contradictory

If visual/UI behavior cannot be cleanly unit-tested, keep implementation minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin-facing behavior improved
6. compatibility notes
7. postponed items

## Extra continuity note
This is A2: a narrow admin detail actionability pass on top of A1/V1–V4/W3.
It is not permission to redesign the broader admin system, marketplace workflow, or payment architecture.