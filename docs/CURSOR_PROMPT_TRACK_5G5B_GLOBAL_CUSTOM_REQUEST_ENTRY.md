Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после уже реализованного Track 5g.5.

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не меняй Mode 2 / Mode 3 business separation.
Не трогай RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.

## Continuity base (обязательно принять)

Уже закрыто:
- Track 5g.4a–5g.4e — standalone catalog Mode 2 Mini App flow
- Track 5g.5 — context-specific UX bridge from unsuitable Mode 2 full-bus situations into existing Mode 3 custom request flow

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

Уже реализовано в 5g.5:
- context CTA on Mode 2 full-bus assisted / waitlist / assisted-preparation situations
- routing into existing custom request form
- waitlist kept separate from custom request
- no backend changes

## New product refinement

The user wants the “individual/custom trip” entry to be available **always**, not only when the current catalog full-bus flow is unsuitable.

Therefore:
- keep the already-added contextual CTA from 5g.5
- add a **global, always-available secondary entry** into the existing Mode 3 custom request flow across the Mini App

Important:
- this is NOT making Mode 3 primary everywhere
- this is NOT merging Mode 2 and Mode 3
- this is a globally available secondary/support path

## Exact next safe step

Implement a narrow Mini App shell/navigation slice only:

# Track 5g.5b / Global custom request entry

### Goal
Make the custom request / individual trip action always available across the Mini App as a global secondary entry point, while keeping contextual emphasis from Track 5g.5 in the relevant Mode 2 situations.

This is a UX/navigation slice.
Not a backend slice.
Not a new RFQ design.
Not a booking/payment change.

## What must be implemented

### 1. Add a global custom-request entry in Mini App shell/navigation
The action should be visible as a general entry point across the Mini App, for example in:
- top navigation
- shell action row
- a stable secondary action area already used for app-level navigation

Use the smallest safe consistent placement already matching the Mini App UI style.

### 2. Keep it secondary, not dominant
This global CTA must be:
- always available
- clear
- easy to find

But it must NOT overshadow the primary actions of the current screen.

Examples:
- on catalog screen, primary actions remain browse/details/reserve related
- on booking/payment flows, payment-forward actions remain dominant
- on help/request areas, this CTA may be naturally more visible but still should not break flow focus

### 3. Reuse existing custom request path
Route into the already existing custom request flow / screen.
Do not build a new request subsystem.
Do not alter backend request semantics.

### 4. Preserve 5g.5 contextual emphasis
Do not remove the current context-specific CTA from:
- unsuitable Mode 2 full-bus detail states
- waitlist-related full-bus states
- assisted preparation states

The new global CTA is additive:
- global availability everywhere
- stronger contextual CTA where particularly relevant

### 5. Use correct wording
The wording should clearly mean:
- custom route / individual trip / trip for your group
- separate from ready-made catalog tour
- separate from waitlist

Avoid wording that implies:
- the current catalog tour itself becomes RFQ
- waitlist and custom request are the same thing
- the current unavailable catalog departure will automatically become a custom order

## Likely files/modules to touch

Only if needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- existing shell/navigation helpers
- tiny focused UI tests if feasible

Avoid touching unless absolutely necessary:
- any backend service in `app/services/`
- booking/payment code
- RFQ bridge code
- supplier marketplace core services
- private bot flows
- admin flows

## What must NOT change

Do not change:
- any booking/payment mutation logic
- waitlist logic
- Mode 2 self-serve rules
- Mode 3 request semantics
- RFQ/bridge/payment eligibility logic
- charter pricing model
- my bookings core behavior
- Mini App auth/init
- contextual CTA behavior already added in 5g.5 unless a tiny correction is needed

## Before coding
Output briefly:
1. current state
2. what is already completed
3. exact next safe step
4. files likely to change
5. risks
6. what remains postponed

## Implementation constraints
- UX/navigation-only
- prefer no migrations
- prefer no backend changes
- no big refactor
- minimal safe placement first
- multilingual-ready where current Mini App strings already support it

## Recommended placement priority
Use the smallest safe globally visible placement, for example:
1. shell/top action row near existing global actions (`Rezervările mele`, `Cererile mele`, `Ajutor`)
2. app-level navigation zone already visible on main screens

Do not scatter duplicate identical buttons everywhere if one shell-level placement already solves discoverability.

## Tests required
Add focused tests only if meaningful:
- the global custom-request entry is visible on main Mini App surfaces where shell navigation is rendered
- wording does not mix catalog/waitlist/custom request semantics
- contextual 5g.5 CTA still exists where expected
- existing Mode 1 / Mode 2 primary flows are not regressed in obvious ways if touched

If UI-only behavior is hard to unit-test cleanly, keep change minimal and explain.

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
This slice is only about making Mode 3 entry globally available in Mini App.
It is not permission to merge or redesign Mode 2 and Mode 3.