Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- handoff/docs sync checkpoint
- U1–U3
- V1–V4
- W1–W3
- X1–X2
- A1
- A2
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
- A1 улучшил admin scanability and sectioning
- A2 улучшил admin detail actionability
- V1–V4/W3 дают rich operational truth
- current admin surface is still not a true usable “live admin workspace”

## Exact next safe step

Implement a medium-sized coherent block:

# A3 — Minimal Live Admin Workspace

### Goal
Turn the current narrow admin custom-request surface into a more genuinely usable internal workspace for day-to-day request triage, while still staying narrow, read-oriented, and grounded in existing semantics.

This is an admin/internal UI/workspace block.
Not a workflow redesign.
Not a payment block.
Not a bridge redesign.
Not a supplier model redesign.
Not a full admin-panel rewrite.

## Block scope

### 1. Improve admin page layout into a more usable workspace
Make the current custom requests admin page feel more like a working internal screen:
- clearer list/detail relationship
- easier navigation between requests
- better visual hierarchy
- reduced “long page of blocks” feeling

A split layout, sticky list, sticky summary, or similarly narrow usability enhancement is acceptable if it remains modest and coherent.

### 2. Make list-to-detail workflow more practical
Improve the operator flow of:
- scan list
- pick request
- inspect detail
- move to next request

This can include:
- clearer selected row/current request state
- faster switching
- stronger visual emphasis on active item
- more usable list sizing or grouping

Do not redesign backend logic.

### 3. Preserve and surface existing operational truth
The workspace must continue to show:
- current operational decision
- blockers / waiting state
- prepared customer message (internal only)
- bridge/commercial context

But present them in a way that supports repeated operational use.

### 4. Keep it narrow and internal
This is not the broad admin panel.
It is a minimal live workspace for the custom request domain only.

### 5. Avoid action inflation
Do not add fake buttons/actions.
If existing actions are already available and can be repositioned safely, that is acceptable.
Otherwise stay read-focused.

## What this block must NOT do

Do NOT:
- redesign admin architecture broadly
- redesign RFQ workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign supplier workflow
- add new lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- invent workflow actions not backed by existing truth

## Likely files/modules to touch

Only where needed:
- `app/admin/custom_requests_ops.html`
- maybe narrow supporting CSS/JS/template helpers already local to this surface
- focused tests for admin UI structure if practical

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows
- core backend semantics

## Required design guardrails

### A. Reuse current truth
No shadow logic in UI.
No second interpretation model.

### B. Make it genuinely more usable
This should create a visible usability gain, not just add another section.

### C. Stay narrow
Only the custom request admin workspace.
Not the whole admin portal.

### D. No fake readiness
Do not imply payment readiness, message delivery, customer completion, or supplier commitment where not evidenced.

## Before coding
Output briefly:
1. current project state
2. what A1 and A2 already solved
3. exact A3 workspace improvement goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit the current custom request admin page as an operator workspace
2. identify the highest-friction list/detail workflow issue
3. improve page structure/layout first
4. improve active request navigation/selection clarity
5. keep operational blocks readable and lower-noise
6. add focused tests if practical
7. keep docs updates minimal unless truly needed

## Tests required
Add focused tests only where meaningful:
1. workspace still exposes existing operational sections
2. current request/selection visibility improves
3. prepared message still remains clearly internal/prepared only
4. no payment readiness/delivery implication is introduced

If visual/UI behavior cannot be cleanly unit-tested, keep implementation minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin-facing workspace behavior improved
6. compatibility notes
7. postponed items

## Extra continuity note
This is A3: minimal live admin workspace for custom requests.
It is not permission to redesign the broader admin system, marketplace workflow, or payment architecture.