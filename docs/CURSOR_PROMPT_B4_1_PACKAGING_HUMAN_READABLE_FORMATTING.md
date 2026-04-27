You are continuing Tours_BOT after B4.

Goal:
B4.1 — Human-readable Packaging Formatting Layer.

Problem:
B4 packaging works, but deterministic drafts expose raw technical values such as:
- 2026-05-10T07:00:00+00:00
- full_bus / assisted_closure
- “28 seats”
- mixed English/Romanian/Russian labels

The packaging draft must be more human-readable before B5 admin review.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/AI_ASSISTANT_SPEC.md

Scope:
Improve deterministic packaging output formatting only.

Allowed:
- helper functions for human-readable date/time/date-range formatting
- helper functions for price/currency
- helper functions for seats/capacity
- helper functions for sales/payment mode display labels
- update deterministic packaging draft builder
- update tests

Target:
Telegram post draft should look closer to a real post:
- 🗓 10–12 May 2026
- 🕒 Departure: 07:00
- 💶 Price: 2000 RON
- 👥 Seats: 28
- 🚍 Route: Timișoara → Brașov → Sibiu → Timișoara
- ✅ Includes: ...
- ❌ Not included: ...

Rules:
- do not invent missing data
- keep source facts grounded
- if language is unknown, use stable neutral labels or Romanian/English fallback
- avoid raw enum values in user-facing drafts
- avoid ISO timestamps in user-facing drafts
- keep raw values in JSON only if needed for audit/debug
- do not change supplier_offer lifecycle
- do not change publish behavior
- do not call AI
- do not create Tour
- do not touch Mini App catalog
- do not touch booking/order/payment

Tests:
- deterministic draft formats date range without ISO
- time formatting is human-readable
- price formatting avoids unnecessary decimals when possible
- sales/payment enums are converted to readable labels
- existing B4 tests still pass

Before coding:
1. summarize B4 current output issue
2. list files expected to change
3. explain why this is formatting-only and safe

After coding:
1. files changed
2. formatting helpers added
3. examples before/after
4. tests run
5. confirm no AI/publish/Tour/Mini App/booking/payment changes
6. next safe step: B5 Admin Moderation & Review