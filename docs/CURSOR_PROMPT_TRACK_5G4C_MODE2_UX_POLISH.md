Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после уже принятого и подтверждённого Track 5g.4b.

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

Это соответствует текущему handoff и implementation plan: Mini App должен вести пользователя по цепочке reserve → payment, используя существующие сервисы, а не отдельную архитектуру.  
Также в Mini App UX payment CTA и status/timer должны быть user-visible, но backend-owned. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}

## Что уже считается завершённым

Считать уже закрытым и не переоткрывать:
- Track 5a–5f v1
- Track 5g, 5g.1, 5g.2, 5g.3, 5g.4, 5g.4a
- Track 5g.4b validation slice

Фактически уже подтверждено:
1. Mode 2 self-serve whole-bus разрешён только при virgin capacity:
   - `seats_available == seats_total`
   - `seats_count = seats_total`
2. Partial full-bus inventory блокирует self-serve и оставляет assisted/manual catalog path
3. После valid Mode 2 virgin hold тот же Order идёт в тот же existing payment-entry path
4. Repeated payment-entry reuse работает по existing Layer A semantics
5. PaymentEntryService / PaymentReconciliationService не менялись

## Exact next safe step

Implement a narrow presentation/UX completion slice only:

# Track 5g.4c / Mode 2 UX polish

### Goal
Finish the user-visible Mini App behavior for Mode 2 so that the already-correct reserve/payment chain is presented clearly and consistently, without changing business logic.

This is a UX/copy/read-state polish slice.
Not a booking slice.
Not a payment architecture slice.

## What must be implemented

### 1. Align Mode 2 payment CTA/copy
Where the Mini App currently shows post-reservation / payment-continuation actions for Mode 2:
- align wording with accepted payment UX
- prefer clear payment-forward wording like `Pay now` where appropriate
- keep provider-neutral copy
- do not imply payment success before backend confirmation

This should stay aligned with Mini App UX payment hierarchy, where `Pay Now` is the dominant CTA on payment-related screens. :contentReference[oaicite:3]{index=3}

### 2. Align assisted/manual partial full-bus copy
For Mode 2 when self-serve is blocked because the bus is no longer virgin:
- keep assisted/manual framing
- do NOT frame as RFQ
- do NOT imply custom request flow
- do NOT expose confusing technical reasoning
- user-facing message should clearly say that this departure is no longer available for full-bus self-service and booking should continue with the team/manual assistance

This preserves the already accepted separation:
- Mode 2 catalog-assisted fallback
- not Mode 3 RFQ fallback

### 3. Ensure user-visible reservation/payment state wording is consistent
For Mode 2 surfaces already using existing Layer A states:
- active reservation wording should be clear
- payment-pending wording should be clear
- timer wording should remain factual
- expired wording should remain human-readable
- do not expose raw backend enum combinations directly

This follows existing Mini App UX rules for translating backend states into user-facing states. :contentReference[oaicite:4]{index=4}

### 4. Keep backend-owned behavior intact
Do not change:
- reservation eligibility
- seats_count semantics
- payment-entry validation
- payment session reuse
- order/payment status semantics

If a text/copy change requires minimal additive response field exposure, keep it narrow and read-only only.

## Likely files/modules to touch

Only if needed:
- `mini_app/app.py`
- Mini App UI text/copy helpers if they exist
- maybe read-side response formatting in Mini App detail/preparation/overview endpoints
- maybe localized labels/templates if they exist in current Mini App layer
- focused UI/read tests

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge services
- supplier marketplace files
- private bot business flow files

## What must NOT change

Do not change:
- any booking/payment mutation logic
- Mode 1 per-seat semantics
- Mode 2 virgin-capacity predicate
- RFQ / bridge execution logic
- eligibility logic
- my requests / 5f v1
- admin workflows
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
- keep this slice presentation-only or read-side only
- prefer no migrations
- prefer no service-layer mutation changes
- no big refactor
- do not broaden private-bot charter UX in this slice
- multilingual-ready copy if current Mini App already supports localized labels
- keep copy concise and commercially clear

## Tests required
Add focused tests only if behavior changes:
- Mode 2 virgin reservation/payment path shows correct payment-forward CTA/copy
- partial full-bus shows assisted/manual wording, not RFQ/custom request wording
- payment-pending / active reservation state wording remains consistent
- existing Mode 1 UX/read behavior is not regressed if touched

If no meaningful automated test is appropriate for some tiny text-only change, keep changes minimal and explain why.

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
It is only for polishing the already accepted Mode 2 user-facing Mini App behavior on top of the already-working Layer A flow.