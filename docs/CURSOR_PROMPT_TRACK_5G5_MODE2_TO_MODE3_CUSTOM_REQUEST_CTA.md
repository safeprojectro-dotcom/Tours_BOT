Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после закрытия Track 5g.4a–5g.4e.

Не начинай заново.
Не переоткрывай архитектуру.
Не смешивай Mode 2 и Mode 3 на уровне business rules.
Не трогай booking/payment core.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- Mini App остаётся thin delivery layer
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже закрыто:
- Track 5g.4a — strict virgin-capacity whole-bus hold semantics
- Track 5g.4b — payment continuation validation
- Track 5g.4c — Mode 2 UX/copy polish
- Track 5g.4d — booking visibility / human-readable states
- Track 5g.4e — acceptance and closure

Текущее product truth:
- Mode 2 = `supplier_route_full_bus` = готовое catalog-offer целого автобуса
- Mode 3 = `custom_bus_rental_request` = пользовательский запрос / RFQ / supplier responses / bridge flow
- Mode 2 != Mode 3

Но нужен UX-мост:
если пользователю не подходит готовый full-bus offer (например, нужен другой маршрут, другая дата, не весь автобус, своя группа/условия), Mini App должен явно предлагать перейти в custom request path.

## Exact next safe step

Implement a narrow UX/read-side CTA bridge only:

# Track 5g.5 / Mode 2 -> Mode 3 custom request CTA

### Goal
Add a clear Mini App CTA such as “Заказать индивидуальный тур” / equivalent localized wording that routes the user from unsuitable Mode 2 full-bus catalog situations into the existing Mode 3 custom request flow.

This is a UX/routing slice.
Not a booking logic slice.
Not a payment slice.
Not a redesign of RFQ.

## What must be implemented

### 1. Add a clear custom-request CTA in the right Mode 2 situations
The CTA should appear when it is helpful that the user move from Mode 2 to Mode 3, for example:
- full-bus catalog offer is not self-serve available
- full-bus offer is exhausted / waitlist state
- assisted/manual full-bus state where the ready-made catalog offer does not fit the user's actual need

The CTA should NOT imply that Mode 2 itself became RFQ.
It should be framed as:
- ready-made offer not suitable?
- need another route/date/group format?
- request an individual/custom trip

### 2. Keep waitlist and custom request separate
Do NOT replace waitlist with this CTA.

Expected logic:
- `Join waitlist` = user wants this exact catalog departure
- `Order individual tour` / `Request custom trip` = user needs a different format, route, date, capacity, or group arrangement

Both may coexist when appropriate.

### 3. Route to the existing Mode 3 entry
The CTA should route into the already existing custom request / My Requests / support entry path already present in the project.

Reuse existing flow if already implemented.
Do not invent a new custom-request architecture.

### 4. Use correct framing
The wording must preserve product separation:
- Mode 2 remains a ready-made catalog charter
- Mode 3 remains a custom request

Good framing examples:
- “Нужен другой маршрут или поездка для своей группы?”
- “Заказать индивидуальный тур”
- “Запросить автобус под вашу группу”

Bad framing examples:
- anything implying the current full-bus catalog product itself is already an RFQ
- anything that collapses waitlist and custom request into one action
- anything that says the current unavailable tour will automatically become a custom request

## Likely files/modules to touch

Only if needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- maybe existing support/request routing helpers in Mini App
- maybe tiny read-side helpers for visibility conditions
- focused tests for CTA presence/routing

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services
- supplier marketplace core services
- private bot flow files
- admin flows

## What must NOT change

Do not change:
- any booking/payment mutation logic
- Mode 2 virgin-capacity predicate
- waitlist logic
- Mode 3 RFQ business flow semantics
- bridge/payment eligibility logic
- supplier policy logic
- charter pricing model
- my bookings core behavior
- Mini App auth/init expansion

## Before coding
Output briefly:
1. current state
2. what is already completed
3. exact next safe step
4. files likely to change
5. risks
6. what remains postponed

## Implementation constraints
- keep this slice UX/routing-only
- prefer no migrations
- prefer no service-layer mutation changes
- no big refactor
- multilingual-ready where current Mini App strings already support it
- if multiple placements are possible, choose the smallest safe useful placement first

## Recommended placement priority
Prefer adding this CTA first in one or more of these places:
1. full-bus detail screen when self-serve is unavailable / assisted only
2. full-bus unavailable / waitlist-related state
3. help/request entry area if needed as a secondary fallback

Choose the smallest useful surface first.
Do not over-scatter CTAs across the whole app in one step.

## Tests required
Add focused tests only:
- CTA appears in intended Mode 2 unsupported/unavailable situations
- CTA wording does not leak RFQ framing into Mode 2 itself
- waitlist CTA remains present where expected
- CTA routes to existing custom request flow / route
- existing Mode 1 behavior is not regressed if touched

If tiny UI-only rendering cannot be fully unit-tested, keep the change minimal and explain.

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
This slice is only a UX bridge from Mode 2 to the already existing Mode 3 path.
It is not permission to merge the two modes or redesign commercial logic.