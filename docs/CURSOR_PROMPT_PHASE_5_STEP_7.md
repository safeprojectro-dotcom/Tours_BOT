# Phase 5 / Step 7 — Mini App Help Entry Placeholder + Language/Settings Polish

Use:
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `docs/TESTING_STRATEGY.md`
- `docs/AI_ASSISTANT_SPEC.md`
- `docs/AI_DIALOG_FLOWS.md`
- `docs/TECH_SPEC_TOURS_BOT.md`

Implement **Phase 5 / Step 7** exactly within this scope.

## Current confirmed checkpoint

Project: `Tours_BOT`

Current approved checkpoint:
- **Phase 5 / Step 6 completed**
- commit: `e19ba40`
- message: `feat: add mini app bookings and booking status view`

Already completed before this step:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed through temporary reservation creation in private bot
- Phase 4 payment/reconciliation/webhook/expiry/notification foundations completed
- Phase 5 / Step 1 completed: `docs/MINI_APP_UX.md`
- Phase 5 / Step 2 completed: Mini App foundation + catalog + filters
- Phase 5 / Step 3 completed: Mini App read-only tour detail
- Phase 5 / Step 4 completed: Mini App reservation preparation UI only
- Phase 5 / Step 5 completed: Mini App real temporary reservation creation + payment start
- Phase 5 / Step 6 completed: Mini App My Bookings + Booking Status View

## Goal of this step

Deliver the next safe Phase 5 slice:
- **Mini App Help entry placeholder**
- **Mini App language/settings polish**
- make support/help entry points visible on the right screens without pretending that real handoff workflow already exists
- improve language selection/persistence UX inside Mini App using already existing foundations

This step must stay UX-oriented and reuse existing service-layer/read foundations.

---

## Required before coding

Before writing code, output a short implementation note with:

1. **Current Phase**
2. **Next Safe Step**
3. **What you will implement in this step**

Then also briefly list:
1. what Steps 1–6 already delivered
2. how this step maps to `docs/IMPLEMENTATION_PLAN.md` Phase 5 Included Scope / Done-When
3. what remains explicitly postponed after this step

Keep this pre-code summary concise.

---

## Exact scope

### Implement
1. Help entry placeholder in Mini App
   - add visible help entry points on the most relevant screens:
     - tour detail
     - reservation/payment-related screens
     - bookings/status screens
   - add a simple Mini App help screen or help panel
   - help screen may include:
     - supported help categories
     - safe guidance text
     - when to contact support
     - honest placeholder copy for operator help if real handoff is not implemented
   - do not pretend a real operator request has been created unless backend support exists

2. Language/settings polish
   - add or refine Mini App language/settings entry
   - allow changing language using current project foundations
   - persist selected language if current architecture already supports it
   - return cleanly to previous Mini App context
   - improve current fallback-language messaging if needed, but do not redesign multilingual architecture

3. Minimal API/UI glue only
   - add the thinnest route/service/UI changes needed
   - keep business rules out of UI
   - if a read endpoint is needed for help/settings glue, keep it narrow

---

## Strict scope guardrails

### Do not implement in this step
- waitlist workflow
- handoff/operator workflow
- real operator request creation
- Mini App auth/initData expansion unless a tiny stub is strictly required
- provider-specific checkout
- refund flow
- admin changes
- group bot changes
- content workflows
- analytics expansion

### Do not change
- repository/service/UI boundaries
- payment reconciliation as the only source of truth for paid-state transition
- PostgreSQL-first assumptions
- reservation expiry policy
- existing seat decrement / seat restoration ownership model

---

## Architectural rules

- service layer owns workflow/business rules
- repositories remain persistence-oriented only
- route layer must stay thin
- Flet/UI must stay thin
- unsupported flows must not be shown as implemented
- no fake handoff success
- no invented support state
- multilingual fallback must remain explicit

---

## UX rules for this step

Follow `docs/MINI_APP_UX.md` closely.

### Help
- help entry should be visible on high-friction screens
- help copy must be honest:
  - information/help is available
  - real human/operator workflow is still postponed if not implemented
- no fake “operator connected” behavior

### Language/settings
- simple and mobile-first
- change language
- persist or apply it consistently
- avoid mixed-language confusion
- no extra profile complexity

---

## Testing expectations

Follow `docs/TESTING_STRATEGY.md`:
- define affected modules
- define risks
- define minimal tests
- implement the smallest safe step

### Add focused tests only for new Mini App help/settings glue
Examples:
- language/settings endpoint or service works for supported language change
- help screen/endpoint returns expected safe content or structure
- UI-facing language selection uses consistent fallback behavior

### Do not
- rewrite earlier Phase 3–6 coverage
- broaden into unrelated integration suites

---

## Suggested implementation shape

Expected direction:
- add a narrow Mini App help/settings surface
- wire help CTA from key existing screens
- refine language selection/persistence inside Mini App
- keep all operator/handoff behavior explicitly postponed

Keep naming consistent with the current codebase.
Do not redesign the whole Mini App structure if a narrow extension is enough.

---

## Important continuity notes

From `docs/CHAT_HANDOFF.md` and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, preserve these assumptions:
- payment provider is still mock/provider-agnostic
- reconciliation remains the single source of truth for paid-state transition
- current Mini App still uses dev assumptions for Telegram user identity
- real handoff workflow is still postponed
- some current Mini App user-facing labels may still be English and should only be improved within narrow scope

---

## Deliverable format after implementation

After coding, report exactly:

1. **files changed**
2. **tests run**
3. **results**
4. **what remains postponed**

Be explicit and keep the report narrow.

---

## Reminder

This is a **safe, narrow Step 7 slice** only:
- Mini App help entry placeholder
- Mini App language/settings polish

Do not expand the project beyond that.