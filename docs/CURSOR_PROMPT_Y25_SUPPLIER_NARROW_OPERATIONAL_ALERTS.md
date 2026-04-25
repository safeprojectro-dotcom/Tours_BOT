Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2.3 supplier moderation/publication workspace implemented
- Y2.1a supplier legal/compliance hardening implemented
- Y24 supplier basic operational visibility completed
- updated `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment core semantics.
Не менять RFQ/bridge semantics.
Не менять payment-entry/reconciliation semantics.
Не делать broad supplier portal/dashboard redesign.

## Goal
Implement a narrow supplier-facing operational alert layer for supplier-owned published offers.

This step is NOT a full notification suite.
It is only a safe, minimal operational signal layer.

## Why this step
After Y24, supplier can manually inspect safe aggregate progress.
The next useful narrow step is proactive visibility:
- some limited signals should reach supplier without opening dashboards constantly.

## Exact scope
Add narrow supplier Telegram notifications and/or explicit read-side alert markers for supplier-owned published offers when safe aggregate conditions are met.

Examples of acceptable alert categories:
- first booking/first confirmed progress signal
- nearing capacity threshold
- sold out / full
- publication retracted
- offer expired / departed / no longer operationally relevant, only if already derivable from existing truth

Prefer a very small set.
Do not build a general event engine.

## What supplier may receive
Only safe aggregate operational signals such as:
- first confirmed booking appeared
- limited capacity remaining
- sold out / fully booked
- offer no longer active operationally

## What supplier must NOT receive
Do NOT expose:
- customer identity
- customer contact data
- payment row details
- payment provider details
- admin-only internal notes
- RFQ/customer-request sensitive data outside allowed supplier surfaces

## Important architecture rule
Reuse existing source-of-truth read paths and statuses.
Do not invent parallel booking logic in bot handlers.
If a signal cannot be derived safely and deterministically, do not send it.

## Safe scope boundaries
- no new booking/payment mutations
- no supplier controls over bookings
- no finance reporting
- no full analytics dashboard
- no customer list
- no RFQ redesign
- no broad notification orchestration engine
- no cron-heavy redesign unless a tiny existing mechanism already supports it safely

## Preferred behavior
Choose one narrow implementation style:
1. supplier bot notifications on a tiny set of events
or
2. supplier workspace alert badges/readiness markers
or
3. a minimal hybrid

But keep it small and deterministic.

## Likely files
Likely:
- supplier notification service
- supplier workspace handler/messages
- maybe a narrow existing notification/outbox reuse only if safe and simple
- focused tests

Avoid touching unrelated code.

## Before coding
Output briefly:
1. current state
2. why this step follows Y24
3. exact alert types proposed
4. likely files to change
5. risks
6. what remains postponed

## Required tests
Add focused tests for:
1. supplier gets alerts only for own offers
2. unpublished offers do not emit operational alerts
3. only safe aggregate signals are shown
4. no customer PII leaks
5. no booking/payment semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier alerts now exist
6. what remains intentionally hidden
7. compatibility notes
8. postponed items

## Important note
This is a narrow supplier alert step only.
Do not silently expand into dashboards, customer lists, finance views, booking controls, or broad event infrastructure.