Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`
- реализации U1 — Mode 3 custom request customer experience
- реализации U2 — Mode 3 request lifecycle clarity
- реализации V1 — Mode 3 operational request handling
- реализации V2 — Mode 3 operational action clarity
- реализации V3 — Mode 3 transition visibility

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
- V1 — operational/admin read-side hints for custom requests
- V2 — operational/admin action clarity
- V3 — operational/admin transition visibility

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

После V1/V2/V3:
- операции видят, что это за заявка
- видят, что с ней делать
- видят request → selection → bridge chain

Следующий и последний логичный V-блок:
нужно сделать понятнее, **что уже реально пошло дальше по customer path**, а где заявка формально resolved/bridged, но фактического follow-through ещё нет.

---

## Exact next safe step

Implement a medium-sized coherent block:

# V4 — Mode 3 Follow-Through Visibility

### Goal
Make it clearer for operational/internal consumers whether a commercially progressed request has actually moved into a real customer continuation path, and where it appears to be stalled, using only already existing architecture and data.

This is an operational/read-side visibility block.
Not a workflow redesign.
Not a payment block.
Not a bridge redesign.
Not a supplier model redesign.
Not a full admin-panel rewrite.

---

## Block scope

This block should include the following related pieces together.

### 1. Clarify “resolved vs actually progressing” visibility
For operational/admin detail responses, make it clearer whether:
- request is only commercially resolved on paper
- bridge exists but no practical customer continuation is visible yet
- customer continuation path appears available
- request likely moved into customer-facing continuation
- request is terminal/closed without follow-through

This must remain careful:
- do not claim payment readiness unless existing truth supports it
- do not claim customer has acted unless existing truth supports it

### 2. Improve “stalled after resolution” interpretation
Add clearer internal hints for cases like:
- selected response exists, but no bridge
- bridge exists, but inactive/closed/replaced
- bridge exists, but no visible customer-facing continuation yet
- bridge/customer path appears present, but no evidence of further progression
- terminal closed states where no more follow-through is expected

Goal:
help operations understand where a request is likely stuck.

### 3. Distinguish “customer path available” vs “customer already moved”
This distinction is important and must stay explicit.

Examples:
- customer path may exist
- customer path appears available
- customer likely still needs prompting/monitoring
- there is no evidence yet that the request progressed further
- terminal / no further follow-through expected

Do not turn this into booking/order truth.
This is interpretation/read-side only.

### 4. Strengthen detail-level follow-through summary
Add or improve one concise detail-level summary explaining:
- whether the request is still pre-continuation
- whether the customer continuation path is available
- whether the request seems stalled after resolution/bridge setup
- whether the request is terminal

This should build on V1/V2/V3 fields, not replace them.

### 5. Keep list-level output lightweight
If any list-level follow-through signal is useful, keep it very light.
Do not overload list responses.
Prefer richer detail-level visibility.

---

## What this block must NOT do

Do NOT:
- redesign supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign full admin UI
- add a task/assignment engine
- add new major backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- merge customer-facing and internal request semantics
- imply automatic next steps that do not actually exist
- infer actual payment/order progression unless supported by existing data already used safely

---

## Likely files/modules to touch

Only where needed:
- `app/services/operational_custom_request_hints.py`
- `app/schemas/custom_marketplace.py`
- `app/services/custom_marketplace_request_service.py`
- maybe tiny repository additions if needed for safer follow-through visibility
- focused tests for resolved/bridged/customer-path follow-through interpretation

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows

---

## Required design guardrails

### A. Build on V1/V2/V3, do not replace them
This should extend operational_hints into follow-through visibility.

### B. No fake progression
Do not imply:
- customer paid
- customer opened payment
- customer completed booking
- bridge is actionable if it is not
- customer acted if there is no evidence

### C. Keep it medium-sized and coherent
This is one operational package.
Do not smuggle in unrelated customer UX or backend redesign.

### D. Preserve current architecture
Do not redesign the marketplace.
Do not redesign the bridge.
Do not redesign admin surfaces broadly.

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

1. audit V1/V2/V3 hints and identify where follow-through meaning is still ambiguous
2. identify what existing truth can safely support:
   - selected response
   - commercial resolution
   - bridge presence/state
   - customer-path visibility already derived in V3
3. enrich detail-level follow-through interpretation first
4. only add list-level signal if clearly useful and lightweight
5. add focused tests
6. keep docs/continuity updates minimal unless truly needed

---

## Tests required

Add focused tests only:
1. resolved-but-not-progressing states are interpreted more clearly
2. bridge exists vs bridge inactive vs no bridge is clearer
3. customer-path-available vs customer-acted is not conflated
4. terminal vs stalled vs customer-monitoring states are not confused
5. no fake payment/order progression is implied

If a tiny internal read-side behavior cannot be cleanly unit-tested, keep changes minimal and explain.

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
This is the last planned V-block in this sequence.
It is not permission to redesign the broader marketplace, bridge, or payment architecture.