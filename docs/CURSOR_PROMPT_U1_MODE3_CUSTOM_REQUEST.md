Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation текущего состояния после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в admin/operator/payment redesign.

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
- context-specific CTA bridge from unsuitable Mode 2 situations into existing Mode 3 custom request flow (5g.5)
- global always-available custom request entry across Mini App shell/navigation (5g.5b)

Текущее product truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

Сейчас вход в Mode 3 уже есть, но следующий большой логичный шаг — довести **customer experience самого Mode 3** как законченный Mini App section:
- вход
- форма
- отправка
- success
- My Requests / detail visibility
- continuity back/return paths

## Exact next safe step

Implement a medium-sized coherent block:

# U1 — Mode 3 / Custom Request Customer Experience

### Goal
Turn the existing custom request path into a more complete, user-friendly Mini App customer section without changing backend commercial architecture.

This is a customer UX/read/routing block.
Not a booking/payment redesign.
Not a supplier/admin redesign.
Not a bridge redesign.

## Block scope

This block should include the following related pieces together.

### 1. Prefill custom request from context where safe
When a user enters Mode 3 from:
- a full-bus detail screen
- a sold-out / waitlist full-bus state
- an assisted full-bus state
- the global custom request entry
- Help / request-related entry

the custom request form should safely prefill useful context where available, for example:
- originating tour code
- title hint / destination hint
- departure date hint
- language
- return route

Important:
- this is a UX convenience only
- do not turn the current catalog item into an RFQ automatically
- do not create hidden booking/payment side effects

### 2. Improve the custom request form UX
The form should make it clearer:
- what this request is
- what it is not
- what happens after submission
- that this is not a reservation and not a payment
- what fields are required vs optional
- that this can be used for custom route / another date / smaller or larger group / different group transport needs

Keep it concise and commercially useful.

### 3. Improve post-submit success state
After a custom request is submitted:
- show a clear success state
- show a short human-readable summary if safe
- explain what happens next
- route naturally toward `My Requests` / `Cererile mele`
- provide a clean way back to browsing if appropriate

Do not pretend that a supplier already responded.
Do not pretend that a reservation exists.
Do not pretend that payment is available here.

### 4. Polish My Requests customer visibility
If `My Requests` and/or request detail already exist:
- improve user-facing statuses and labels
- make next steps clearer
- avoid raw internal wording
- make the request detail easier to understand for non-technical users

This is read-side/customer-facing only.
Do not redesign the underlying RFQ model.

### 5. Keep navigation continuity clean
The user should be able to move coherently between:
- catalog
- tour detail
- custom request form
- request success
- My Requests
- request detail

Back/return paths should feel intentional, not accidental.

## What this block must NOT do

Do NOT:
- redesign RFQ supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign admin panels
- redesign operator/handoff workflow
- redesign supplier policy model
- change Mode 2 hold/payment semantics
- add a new charter pricing model
- merge waitlist and custom request
- make custom request primary over normal catalog checkout everywhere

## Likely files/modules to touch

Only where needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- existing custom request screen / shell navigation helpers
- existing My Requests / request detail Flet screens
- maybe tiny read-side helpers / response adapters if needed
- focused tests for custom request UX/copy/routing/prefill

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services
- supplier marketplace core services
- admin flows
- payment code
- unrelated private bot flows

## Required design guardrails

### A. Preserve Mode 2 vs Mode 3 separation
The form may be prefilled from a Mode 2 context, but:
- a Mode 2 catalog item does not become an RFQ automatically
- waitlist stays separate
- custom request stays a separate customer choice

### B. No fake promises
Do not state or imply:
- booking already exists
- payment is next
- supplier is already assigned
- request is already approved
- operator already contacted unless that is truly implemented

### C. Keep business rules in service layer
If any additive behavior requires tiny read-side helpers, keep them thin.
Do not move policy into UI.

### D. Keep it medium-sized, not sprawling
This is one coherent block.
Do not sneak in extra unrelated work.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current custom request entry + existing form + existing My Requests flow
2. add safe context-prefill support
3. improve form copy/labels/help text
4. improve submit success state
5. improve My Requests / request detail customer wording
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only for this block:
1. entering custom request from Mode 2 context can prefill safe hints
2. custom request form copy clearly distinguishes request vs reservation/payment
3. successful submission leads to a clear success state and/or My Requests path
4. My Requests / request detail customer-facing wording stays human-readable
5. Mode 2 and waitlist semantics are not regressed or merged into custom request wording

If some Flet UI behavior cannot be cleanly unit-tested, keep the changes minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what user-visible behavior is now supported
6. compatibility notes
7. postponed items

## Extra continuity note
This is the next medium-sized customer-experience block for Mode 3.
It is not permission to redesign the broader marketplace or payment architecture.