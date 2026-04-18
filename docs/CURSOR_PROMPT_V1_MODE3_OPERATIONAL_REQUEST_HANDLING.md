Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`
- реализации U1 — Mode 3 custom request customer experience
- реализации U2 — Mode 3 request lifecycle clarity

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в broad admin redesign, supplier redesign, payment redesign.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- Mini App остаётся thin delivery layer
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже закрыто:
- standalone catalog Mode 2 Mini App flow (5g.4a–5g.4e)
- context-specific CTA bridge into Mode 3 (5g.5)
- global always-available custom request entry (5g.5b)
- U1 — Mode 3 custom request customer experience
- U2 — Mode 3 request lifecycle clarity

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

Customer side for Mode 3 is now much stronger.
The next practical medium block is to improve the **operational handling/readability** of custom requests without redesigning the marketplace.

---

## Exact next safe step

Implement a medium-sized coherent block:

# V1 — Mode 3 Operational Request Handling

### Goal
Make custom requests easier to inspect, triage, and continue from the operational/internal side, while preserving the existing architecture and customer-facing flow.

This is an operational/readability block.
Not a new workflow engine.
Not a payment block.
Not a supplier model redesign.
Not a bridge redesign.
Not a full admin-panel rewrite.

---

## Block scope

This block should include the following related pieces together.

### 1. Improve operational list readability for custom requests
Where custom requests are listed for internal/operational use, make the list easier to scan at a glance.

Operationally useful signals may include:
- request type / category hint
- route/date/group hint
- whether request is active vs closed
- whether customer-facing next action already exists
- whether the item likely needs review, offer selection, or continuation

The list should answer quickly:
- what is this request about?
- what stage is it in?
- what probably needs to happen next?

Keep it concise and readable.

### 2. Improve operational detail readability
On internal request detail surfaces, make the page easier to understand without digging through raw fields.

Examples of improvement:
- better sectioning
- stronger summary block
- clearer lifecycle/status wording
- clearer continuation/next-step visibility
- more obvious distinction between:
  - request intake data
  - supplier/commercial progress
  - customer-facing next action
  - already closed/completed items

### 3. Surface existing continuation states more clearly
If the current architecture already has meaningful continuation state, show it more clearly to internal users.

Examples:
- selected response exists
- bridge exists
- customer next action already exists
- request is commercially resolved but not fully closed
- request is closed externally / assisted / fulfilled

Do NOT invent new states.
Do NOT redesign bridge/payment eligibility.
Do NOT create new workflow semantics unless absolutely necessary and narrowly justified.

### 4. Make “what to do next” clearer for internal handling
Operational users should more easily understand:
- should this request be reviewed?
- is it waiting on supplier-side progress?
- is it ready for commercial continuation?
- is it already waiting on the customer?
- is it done/closed?

This can be done with:
- better labels
- concise hints
- section captions
- operational summary text

Do not build a new task engine.
Do not redesign assignment workflow broadly.

### 5. Preserve separation between internal and customer semantics
Any internal wording improvements must not accidentally overwrite or degrade customer-facing wording.

Internal/operational language can be more explicit than customer wording, but should still be human-readable and not overly technical.

---

## What this block must NOT do

Do NOT:
- redesign supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign the full admin system
- redesign operator assignment workflow broadly
- add a new charter pricing model
- alter Mode 2 hold/payment semantics
- merge customer-facing and internal request semantics
- introduce broad new backend lifecycle states unless absolutely necessary and tightly scoped

---

## Likely files/modules to touch

Only where needed:
- existing admin/custom-request list/detail surfaces
- operational read-side helpers / summary helpers / formatting helpers
- labels/templates/strings used by internal request views
- maybe tiny schema/read adapter additions if needed
- focused tests for operational list/detail readability

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows

---

## Required design guardrails

### A. Preserve current architecture
This is readability/operational clarity on top of the existing request architecture.
Do not redesign the marketplace.

### B. No fake operational states
Do not invent:
- supplier commitment that does not exist
- payment readiness that does not exist
- bridge state that does not exist
- admin/operator actions that are not implemented

### C. Keep it medium-sized and coherent
This block should be one meaningful operational package.
Do not smuggle in unrelated customer UX or backend work.

### D. Keep customer-facing behavior stable
This is primarily an operational/internal block.
Customer-facing custom request behavior should remain unchanged unless a tiny shared-helper fix is necessary.

---

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

---

## Suggested implementation order

1. audit current operational/custom-request list + detail surfaces
2. identify biggest clarity gaps
3. improve list-level scanability
4. improve detail-level summary/sectioning/next-step clarity
5. surface already-existing continuation state more clearly
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

---

## Tests required

Add focused tests only:
1. operational summaries/labels become clearer and stable
2. existing continuation state is surfaced more clearly when present
3. no fake payment/bridge readiness is implied
4. customer-facing semantics are not unintentionally regressed if shared helpers are touched

If some UI/admin behavior cannot be cleanly unit-tested, keep the changes minimal and explain.

---

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what operational behavior is now improved
6. compatibility notes
7. postponed items

---

## Extra continuity note
This is the next medium-sized operational block after customer-side U1/U2.
It is not permission to redesign the broader marketplace, supplier operations model, or payment architecture.