Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2 design gate accepted
- Y2.1 supplier Telegram onboarding implemented and live-verified
- Y2.2 supplier Telegram offer intake implemented and live-smoke verified
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment core.
Не менять RFQ/bridge execution semantics.
Не менять payment-entry/reconciliation semantics.
Не смешивать Mode 2 и Mode 3.
Не делать broad redesign supplier platform.

## Continuity base
Use as source of truth:
- current codebase
- `docs/CHAT_HANDOFF.md`
- `docs/SUPPLIER_TELEGRAM_OPERATING_MODEL_Y2.md`

Already true:
- supplier v1 = one supplier + one primary Telegram operator
- `/supplier` onboarding exists and is live-verified
- approved supplier can use `/supplier_offer`
- supplier offer intake persists draft and can submit to `ready_for_moderation`
- moderation boundary must stay intact
- no direct publish from Telegram
- no direct live Layer A tour creation from bot intake

## Why this step exists
Y2.2 works, but live usage showed narrow UX/validation/navigation issues:
- no step-back navigation
- no clean cancel/home action
- payment mode wording is unclear for supplier-facing UX
- field order is not ideal
- departure point is missing
- datetime/currency validation appears too weak
- price questions should better reflect sales mode
- review before moderation should be clearer
- optional photo/media is useful but must remain narrow and safe

This step is a narrow polish step on top of Y2.2.
It is not Y2.3 workspace.
It is not supplier dashboard/stats.
It is not supplier publication redesign.

## Important compliance note
This step does not redesign supplier legal/compliance approval.
If current supplier approval is later determined to require mandatory legal business identity fields
(company/legal form, CUI, permit/license type, permit/license number),
that must be handled in a separate scoped onboarding/compliance step,
not silently mixed into this polish step.

# Exact step
## Y2.2a — Supplier offer intake polish: navigation, copy, ordering, validation

## Goals
Improve the existing Telegram supplier offer intake flow so it becomes safer and more operationally usable, while preserving the same persistence/moderation boundaries.

## What this step must implement

### 1. Add navigation controls at every meaningful FSM step
Supplier must be able to:
- go one step back
- cancel current intake and return to supplier offer entry/home state

Implement supplier-facing controls:
- `Înapoi` = one step back
- `Acasă` or equivalent = cancel current intake and return to supplier operational entry point

Requirements:
- back should restore previous FSM step safely
- cancel/home should clear current FSM intake state safely
- must not leave broken half-state in FSM memory
- conservative behavior is preferred

Important:
- do not build a broad menu system
- just add narrow safe navigation around the current offer intake FSM

### 2. Improve payment mode supplier-facing wording
Current internal wording like `Închidere asistată` is not sufficiently clear for supplier users.

Keep internal domain semantics intact, but change supplier-facing Telegram copy/buttons to something clearer, such as:
- `Plată prin platformă`
- `Rezervare / plată la îmbarcare`

Choose the clearest Romanian wording, but do not change backend domain meaning unless strictly required for mapping.

### 3. Reorder offer intake fields
Improve the order of intake so it matches supplier mental model better.

Prefer a flow closer to:
1. title
2. short route / description
3. departure point / city
4. departure datetime
5. return datetime (if applicable in current schema/flow)
6. capacity
7. sales mode
8. payment mode
9. price
10. currency
11. short program
12. vehicle / transport notes
13. optional photo/media (only if included in this step)
14. review + moderation submit

Do not force an unnecessary broad redesign if the current service contract requires some specific ordering, but improve it as much as possible.

### 4. Add departure point
Add a clear supplier input for departure point / departure city / boarding start context.

Use the narrowest useful field.
Do not build full boarding-point management here.
This is supplier intake context only.

### 5. Strengthen validation
The live flow suggested validation is too weak or inconsistent.

At minimum, make validation strict and supplier-friendly for:
- departure datetime
- return datetime (if present)
- currency code
- numeric price
- positive capacity

Requirements:
- if prompt says datetime, plain date must not silently pass
- currency should follow a narrow valid format (e.g. `EUR`, `RON`, `USD`)
- validation errors should show clear Romanian guidance
- avoid vague generic failure messages

### 6. Make price prompt context-aware
The supplier-facing price question should depend on sales mode:
- if `Per loc` → ask for price per seat
- if `Autocar complet` → ask for price for full bus

Do not just ask one generic “base price” if context-aware wording is easy to support safely.

### 7. Improve review before moderation
Before final moderation submit, show a clearer compact supplier-facing summary of the draft, so the supplier can review what is being sent.

Summary should be narrow and high-signal.
For example:
- title
- departure point
- departure date/time
- sales mode
- payment mode
- price + currency
- short route/description

Do not build a huge formatted document. Keep it Telegram-friendly.

### 8. Optional photo/media — only if safe in this step
If implementation remains narrow and safe, add optional single photo support:
- supplier may send one photo
- store as a narrow draft/moderation asset reference (e.g. Telegram file_id or existing media reference style)
- do not build gallery/media library
- do not publish automatically
- do not broaden beyond one optional image

If confidence is low or it becomes architecturally messy, postpone photo support and clearly document that it remains postponed.
Navigation/validation/copy/order is higher priority than media.

## What this step must NOT do
Do NOT:
- publish offers directly from Telegram
- bypass moderation
- create live Layer A tours
- redesign supplier offer lifecycle
- implement supplier dashboard/stats
- implement supplier offer list/workspace (that is later read-side work)
- redesign RFQ supplier flow
- add org/multi-operator RBAC
- redesign auth platform-wide
- change booking/payment semantics

## Architecture guardrails
- Telegram remains an input surface only
- business logic stays in service layer
- moderation boundary remains unchanged
- existing supplier offer domain must still be reused
- no parallel offer persistence model
- preserve clear separation from RFQ/custom request flows

## Likely files to touch
Likely:
- `app/bot/handlers/supplier_offer_intake.py`
- `app/bot/messages.py`
- `app/bot/state.py`
- `app/bot/constants.py`
- maybe small supportive bot wiring if needed
- focused tests for navigation and validation

Avoid touching unless absolutely needed:
- supplier offer publication/moderation services
- Layer A booking/payment services
- RFQ/bridge services
- broad admin/Mini App architecture

## Before coding
Output briefly:
1. current state
2. what Y2.2 already implemented
3. exact Y2.2a goal
4. likely files to change
5. risks
6. what remains postponed

## Suggested implementation order
1. inspect current supplier offer FSM
2. add back/home navigation model
3. improve supplier-facing labels/buttons
4. reorder fields safely
5. add departure point
6. strengthen validation
7. add context-aware price wording
8. improve review summary
9. optionally add single-photo support only if still narrow and clean
10. add focused tests

## Required focused tests
Add focused tests for:
1. back navigation works safely
2. home/cancel resets flow safely
3. pending/rejected/approved gating still works
4. invalid datetime is rejected clearly
5. invalid currency is rejected clearly
6. price prompt changes based on sales mode
7. moderation submit still lands in the same lifecycle state
8. no booking/payment/RFQ semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier-facing UX improved
6. whether optional photo support was included or postponed
7. compatibility notes
8. postponed items

## Important note
This is still a narrow offer-intake polish step.
Do not silently expand into Y2.3 supplier workspace, analytics, publication redesign, or broader platform architecture.