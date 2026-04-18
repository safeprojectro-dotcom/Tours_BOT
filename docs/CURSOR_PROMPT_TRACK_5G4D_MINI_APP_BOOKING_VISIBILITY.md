Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после уже принятого и реализованного Track 5g.4c.

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не лезь в RFQ/bridge.
Не меняй payment-entry / reconciliation semantics.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- payment/reconciliation authority не меняется
- Mini App остаётся thin delivery layer
- service layer владеет policy/business rules
- UI не дублирует backend rules

Это соответствует текущему handoff и implementation plan: Mini App должен вести пользователя по цепочке reserve → payment и затем показывать booking/payment state через existing service layer, а не отдельную архитектуру.  
Также `MINI_APP_UX.md` прямо требует, чтобы `My Bookings` и `Booking Detail / Status View` переводили backend states в понятные user-visible states, не показывая пользователю raw enum combinations. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}

## Что уже считается завершённым

Считать уже закрытым и не переоткрывать:
- Track 5a–5f v1
- Track 5g, 5g.1, 5g.2, 5g.3, 5g.4, 5g.4a, 5g.4b, 5g.4c

Фактически уже подтверждено:
1. Mode 2 self-serve whole-bus разрешён только при virgin capacity:
   - `seats_available == seats_total`
   - `seats_count = seats_total`
2. Partial full-bus inventory блокирует self-serve и оставляет assisted/manual catalog path
3. После valid Mode 2 virgin hold тот же Order идёт в тот же existing payment-entry path
4. Repeated payment-entry reuse работает по existing Layer A semantics
5. User-facing CTA/copy в Mini App уже подправлены:
   - `Pay now`
   - `Payment pending`
   - assisted/manual wording without RFQ leakage

## Exact next safe step

Implement a narrow read-side/UI-completion slice only:

# Track 5g.4d / Mini App booking visibility

### Goal
Complete the user-visible booking/payment state presentation in Mini App so that Mode 2 whole-bus reservations and normal Layer A reservations are shown consistently and human-readably in “My Bookings” / booking status surfaces.

This is a read-side / presentation slice.
Not a booking mutation slice.
Not a payment architecture slice.

## What must be implemented

### 1. Human-readable booking visibility for active reservation states
Where Mini App shows booking/order entries or booking detail/status:
- active temporary reservation should be shown as a clear human-facing state
- payment pending should be shown clearly
- timer / reservation expiry should remain factual and backend-driven
- no raw backend enum combinations shown to the user

Examples aligned with `MINI_APP_UX.md`:
- active reservation -> `Reserved temporarily`
- payment pending -> clear pending wording
- confirm next action when relevant -> `Pay now`

### 2. Human-readable expired unpaid state
Current backend expiry semantics remain:
- `booking_status=reserved`
- `payment_status=unpaid`
- `cancellation_status=cancelled_no_payment`

The UI/read layer must translate this into a user-visible state such as:
- `Reservation expired`
- or equivalent localized wording

Do NOT expose the raw triple of backend statuses to the user.

This is explicitly required by Mini App UX: expired unpaid reservation must be shown as an expired/canceled-for-no-payment user-facing state, not raw enum combinations. :contentReference[oaicite:3]{index=3}

### 3. Human-readable confirmed booking state
When payment is confirmed and booking is active/confirmed:
- show a clear confirmed state
- remove or suppress payment-forward CTA where no longer relevant
- keep wording consistent with existing notification/payment logic

### 4. Ensure Mode 2 looks like a first-class booking state, not a special hack
Mode 2 valid whole-bus orders in booking visibility surfaces should:
- render like normal customer bookings
- not mention RFQ/custom request
- not expose internal charter policy mechanics
- remain consistent with already polished copy

### 5. Keep read logic/service logic thin and additive
If needed:
- add narrow read-side formatting helpers / facade mapping
- or adapt existing summary/read services
- but do not rewrite core order/payment services
- do not move business rules into UI

## Likely files/modules to touch

Only if needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- read-side Mini App services, booking overview helpers, or order summary adapters
- maybe schemas/response helpers for user-visible state mapping
- focused tests for booking visibility wording/state mapping

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge services
- supplier marketplace files
- private bot flow files
- admin flows

## What must NOT change

Do not change:
- any booking/payment mutation logic
- Mode 1 per-seat semantics
- Mode 2 virgin-capacity predicate
- payment-entry validation or reuse semantics
- RFQ / bridge execution logic
- my requests / 5f v1
- waitlist
- handoff
- Mini App auth/init expansion
- supplier-defined pricing/policy path
- charter pricing model

## Before coding
Output briefly:
1. current state
2. what is already completed
3. exact next safe step
4. files likely to change
5. risks
6. what remains postponed

## Implementation constraints
- keep this slice read-side / presentation-only
- prefer no migrations
- prefer no service-layer mutation changes
- no big refactor
- multilingual-ready where current Mini App string table already supports it
- keep wording concise and commercially clear
- backend remains the source of truth for timer and statuses

## Tests required
Add focused tests only:
- active reservation is shown as human-readable reserved-temporarily style state
- expired unpaid reservation is shown as expired / no-payment state, not raw enum exposure
- confirmed booking is shown as confirmed and not as payment-pending
- Mode 2 booking visibility does not leak RFQ/custom-request framing
- existing Mode 1 visibility is not regressed if touched

If a tiny UI-only rendering edge cannot be meaningfully unit-tested, keep changes minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what user-visible behavior is now improved
6. compatibility notes
7. postponed items

## Extra continuity note
This slice is not permission to reopen product design.
It is only for completing Mini App booking visibility/read-state presentation on top of the already-working Layer A flow.