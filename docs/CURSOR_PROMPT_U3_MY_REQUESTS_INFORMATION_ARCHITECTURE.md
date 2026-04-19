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
- реализации V4 — Mode 3 follow-through visibility
- реализации W1 — request lifecycle message preparation
- реализации W2 — request activity / message preview
- реализации W3 — internal/manual prepared request message surface
- реализации X1 — supplier-side request handling clarity
- реализации X2 — supplier response workflow clarity
- hotfix request detail empty-control crash
- production schema drift fix for custom_request_booking_bridges

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в broad redesign.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже сильно укреплены:
- customer-side Mode 3 flow
- admin/ops read-side
- request messaging previews
- supplier-side clarity

Но `My Requests` list/detail по-прежнему страдают по information architecture:
- карточки почти одинаковые
- нет сильной опоры на request id
- не хватает created date/time
- не видно кратко, о чём заявка
- смешиваются языки
- detail page повторяет похожие формулировки и не даёт хорошей структуры

## Exact next safe step

Implement a medium-sized coherent block:

# U3 — My Requests Information Architecture

### Goal
Make `My Requests` list and detail much easier to scan and understand by improving information architecture, status presentation, request identity, and content structure, without changing backend request/bridge/payment semantics.

This is a customer-facing read/UI block.
Not a workflow redesign.
Not a payment block.
Not a bridge redesign.
Not a new notification engine.

## CRITICAL LANGUAGE RULE

For this block, **customer-facing UI text must be Romanian-first**.

That means:
- list labels
- detail header
- section titles
- status wording
- summary lines
- current update wording
- next-step wording
- helper/disclaimer text

must be provided in Romanian and must render coherently in Romanian on the screen.

Do not leave mixed Romanian + English text on the same customer-facing request screen if Romanian keys can be added in this block.

If a key used by this screen currently falls back to English, add the Romanian key/value now as part of this block.

Goal for this block:
- `My Requests` and request detail should read as a coherent Romanian UI, not a mixed fallback UI.

## Block scope

### 1. Improve request identity in the list
Each request card in `My Requests` should show clearer identity, including as much of the following as is safely available:
- request reference / id (for example `Cerere #8`)
- request type (`Excursie de grup`, `Tur personalizat`, etc.)
- created date/time
- short subject/summary preview
- clear compact status label

The user should be able to distinguish cards quickly.

### 2. Add short subject/summary preview
The list should show a short human-readable hint about what the request is about, for example derived safely from:
- request type
- route/destination/note preview
- group size
- date hint

Do not dump raw long notes.
Do not expose confusing internal text.
Keep it short and scannable.

### 3. Improve customer-facing status presentation
Status on list and detail should be:
- short
- human-readable
- consistent
- not repeated in multiple slightly different paragraphs

Prefer compact labels/chips/headlines over repeated long status prose.

Do not change backend status semantics.
This is presentation only.

### 4. Restructure detail header
The request detail page should start with a stronger header area, for example showing:
- request reference / id
- request type
- created date/time
- travel date/date range if present
- customer-facing status
- one short summary line

The user should immediately know:
- which request this is
- when it was created
- what it is about
- what state it is in

### 5. Restructure detail body into clearer sections
Instead of repeated overlapping paragraphs, organize detail into clearer sections such as:
- ce ai cerut
- status curent
- actualizare curentă
- ce urmează

Reuse existing U1/U2/W2 messaging where useful, but avoid duplication.

### 6. Reduce language mixing
This block must explicitly remove awkward Romanian/English mixing on `My Requests` list/detail screens.

If the current screen shows English fallback text, replace it with Romanian copy for the keys used on these screens.

### 7. Keep content concise and non-repetitive
Avoid showing three near-duplicate explanatory paragraphs in a row.
If the same idea is already communicated in:
- status label
- current update
- next step section

then do not restate it verbosely again.

## What this block must NOT do

Do NOT:
- redesign request lifecycle semantics
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign supplier workflow
- add new backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- invent fake progress or delivery
- merge request messaging with booking/payment semantics

## Likely files/modules to touch

Only where needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- maybe tiny read-side formatting helpers for request list/detail summaries
- maybe thin adapters around existing request detail/list data
- focused tests for request list/detail presentation logic

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier/admin business logic
- notification delivery engine
- unrelated private bot flows

## Required design guardrails

### A. Reuse existing truth, don’t create shadow semantics
Use current request data, U1/U2 wording, and W2 preview safely.
Do not invent a second interpretation model.

### B. Strong identity, low clutter
The main goal is clarity:
- which request
- what it is about
- when it was created
- what state it is in
- what happens next

### C. No fake certainty
Do not imply:
- booking exists
- payment is ready
- supplier accepted
- delivery was sent
unless current truth actually supports it.

### D. Keep it medium-sized and coherent
This is one customer-facing information architecture block.
Do not smuggle in unrelated redesign.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current `My Requests` list/detail UI
2. identify the minimum identity fields already available
3. improve list card identity and summary
4. improve detail header
5. simplify and regroup detail body
6. reduce duplicate/redundant wording
7. add Romanian strings for every key used on these screens
8. add focused tests
9. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only:
1. list cards expose clearer identity (reference/type/status/summary)
2. detail header shows stronger request identity
3. repeated status/update/next-step wording is reduced
4. Romanian customer-facing wording is present for keys used on these screens
5. existing request semantics are not regressed

If some Flet UI behavior cannot be cleanly unit-tested, keep implementation minimal and explain.

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
This is U3: customer-facing information architecture for `My Requests`.
It is not permission to redesign the broader marketplace, bridge, or payment architecture.