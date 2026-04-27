You are continuing Tours_BOT after B4.2.1.

Goal:
B4.3 — Pricing / Discount / Availability Truth Rules.

Problem:
Telegram draft is now much cleaner, but we need explicit truth rules:
- do not claim live availability unless system confirms it
- do not show promo code if there is no real discount
- do not show fake urgency
- avoid duplicated route/description in program block
- make marketing_summary and Mini App descriptions human-readable too

Scope:
Formatting/truth rules only.

Allowed:
- tighten deterministic formatting helpers
- update marketing_summary / mini_app descriptions formatting
- update quality_warnings_json when data is weak/ambiguous
- tests

Rules:
1. Availability:
- per_seat must NOT show “X locuri disponibile” unless there is confirmed live availability source.
- fallback: “📩 Locurile se confirmă la rezervare”.
- full_bus may show capacity only as vehicle/capacity, not “available seats”.

2. Discounts:
- show promo code only when discount_percent > 0 or discount_amount > 0.
- if discount_valid_until exists but no discount value, do not show public discount block.
- add quality warning for promo code without actual discount value.

3. Urgency:
- no “last seats”, “urgent”, “only X left” unless confirmed by live data.
- add quality warning if supplier-provided marketing text contains fake scarcity but system has no live proof.

4. Duplicates:
- do not repeat route/description after program block if route already appeared above.
- keep program concise and separate from included/excluded.

5. Human-readable descriptions:
- marketing_summary and mini_app_full_description should avoid:
  - raw ISO
  - raw enum labels
  - “Sales: Full bus”
  - “Payment: ...”
- keep grounding/debug info in packaging_draft_json.layout_hint.grounding_debug only.

Must NOT:
- call AI
- publish
- create Tour
- change Mini App catalog
- change booking/order/payment
- change lifecycle
- invent data

Tests:
- per_seat uses confirmation fallback, not fake availability
- full_bus capacity is not treated as live availability
- promo code without discount is not public and creates warning
- no fake urgency without live source
- route is not duplicated after program
- marketing_summary and mini_app descriptions contain no raw enum/ISO
- previous B4 tests still pass

Before coding:
1. summarize remaining issues after B4.2.1
2. list files expected to change
3. explain why this is truth/formatting only and safe

After coding:
1. files changed
2. truth rules implemented
3. tests run
4. confirm no AI/publish/Tour/Mini App/booking/payment changes
5. next safe step: B5 Admin Moderation & Review