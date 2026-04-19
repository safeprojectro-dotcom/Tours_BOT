Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- handoff/docs sync checkpoint
- U1–U3
- V1–V4
- W1–W3
- X1–X2
- A1
- A2
- A3
- key hotfixes and production fixes

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не делай broad redesign.

## Problem
The project already has:
- supplier foundation
- supplier offers
- moderation/publication flow
- customer Mini App
- admin/internal surfaces
- supplier-side request clarity (X1/X2)

But the supplier operating model is still incomplete as a product surface.

We need to decide whether and how suppliers should operate primarily through Telegram, including:
- supplier identity / onboarding
- supplier offer submission through bot/dialog flow
- supplier access model
- supplier visibility into published-offer performance
- supplier visibility into client requests

This is important because the intended real-world operating assumption is:
- suppliers use Telegram
- admins use Telegram
- Telegram identity may be the practical entry/access anchor

## Goal
Design a safe supplier Telegram operating model that fits the current architecture, without breaking Layer A, RFQ, or marketplace boundaries.

This is a design/architecture step.
Not a full implementation step yet.

## What must be decided

### 1. Supplier identity and access model
Decide and document:
- should supplier access be anchored to Telegram user id?
- is supplier v1 a single Telegram-bound supplier account?
- or supplier entity + one or more Telegram operator users?
- how supplier onboarding should work in a safe MVP form

Prefer a realistic v1, not an overengineered organization model.

### 2. Supplier onboarding through Telegram
Decide whether supplier registration can/should happen through bot dialog/FSM and what data is collected in v1, for example:
- supplier/company name
- transport/vehicle basics
- photos
- operating region
- contact info
- basic moderation status

Clarify:
- what is collected in onboarding
- what is postponed
- what requires admin approval before supplier becomes operational

### 3. Supplier offer submission through Telegram
Decide how supplier creates an offer through Telegram bot/dialog flow, for example:
- route / title / description
- departure date/time
- photos
- seats vs full-bus mode
- price per seat or full bus
- booking vs payment mode
- restrictions / conditions

Clarify how this maps onto the already existing supplier offer domain and moderation/publication pipeline.

Critical:
- supplier bot intake must not bypass moderation
- supplier bot intake must not directly create live Layer A tours without accepted scope
- supplier input should create draft / moderation-ready records in the appropriate domain

### 4. Supplier visibility for Model 1 / published tour operations
Decide what supplier should be allowed to see for published seat-based trips/offers, such as:
- seats sold / seats remaining
- active temporary holds
- confirmed bookings count
- load factor / bus fill status

Clarify:
- what data comes from Layer A read-side
- what is safe to expose
- what customer/personally identifying details must remain hidden by default

### 5. Supplier visibility for client requests / RFQ
Decide what supplier should see regarding client requests, including:
- open custom requests relevant to them
- whether they already responded
- whether they were selected
- whether the request is now read-only/closed
- what operational/request history is visible to them

Clarify separation between:
- published-trip operational stats
- custom request / RFQ visibility

These must not be collapsed into one confusing domain.

### 6. Supplier notifications
Decide what supplier should be notified about in Telegram, for example:
- offer submitted
- offer approved/rejected/published
- maybe operational booking events for eligible offer/tour modes
- maybe RFQ/request events

Clarify carefully:
- what is notification-worthy
- what should remain admin-only
- what should not imply ownership/workflow semantics beyond current truth

### 7. Minimal safe implementation order
Recommend the safest next implementation order after this design step, for example:
- supplier Telegram identity/onboarding first
- then supplier offer submission via bot
- then supplier visibility dashboard/read-side
- then supplier notifications

Or another narrow order if justified.

## Critical architecture guardrails

### A. Preserve Layer A truth
Any supplier-facing tour/order stats must be read from existing booking/order/payment truth.
Do not create a second booking/accounting model for suppliers.

### B. Preserve moderation/publication boundaries
Supplier input must not silently become a live customer-facing tour without the intended moderation/publication step.

### C. Preserve Mode 2 vs Mode 3 separation
Mode 2:
- catalog full-bus / published offer logic

Mode 3:
- custom request / RFQ / response / bridge logic

Do not merge these just because suppliers use Telegram for both.

### D. Preserve privacy boundaries
Do not assume supplier should see all customer data.
Explicitly define safe v1 visibility boundaries.

### E. Prefer realistic MVP over overengineering
Supplier v1 may be:
- one supplier entity
- one primary Telegram user
- bot-driven onboarding and offer intake
- read-side visibility for stats and requests

Do not jump immediately to full organization/roles/permissions platform unless strongly justified.

## Must not do
Do NOT:
- implement the whole supplier portal in this step
- redesign booking/payment architecture
- redesign RFQ/bridge semantics
- redesign admin architecture
- redesign publication/moderation core
- introduce broad auth platform unnecessarily
- merge supplier/customer/admin surfaces conceptually

## Likely files/docs to touch
Design/docs only, likely:
- `docs/CHAT_HANDOFF.md` only if a tiny continuity note is justified
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` only if a tiny sync is justified
- a new design doc if needed
- existing supplier marketplace implementation plan if a narrow update is justified

Prefer creating/updating one focused design document rather than scattering changes.

## Before coding
Output briefly:
1. current project state
2. why supplier Telegram operating model is now the right design problem
3. exact decisions to make
4. likely files/docs to touch
5. risks
6. what remains postponed

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests not needed / not run if docs-only
4. recommended supplier identity/access model
5. recommended supplier onboarding model
6. recommended supplier offer-submission model
7. recommended supplier visibility model (tour stats + client requests)
8. recommended notification model
9. safest next implementation step
10. postponed items

## Extra continuity note
This is Y2: supplier Telegram operating model.
It is not permission to redesign the broader marketplace, workflow, payment, booking, or admin architecture.